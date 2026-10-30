/*
 * Copyright (c) 2026 Craig McLean
 * Zephyr HLK-LD2410S 24 GHz mmWave Radar Driver (OT2 Edge Wake + UART0 Runtime PM)
 */

#include "sensor_ld2410s.h"
#include <zephyr/drivers/uart.h>
#include <zephyr/pm/device.h>
#include <zephyr/logging/log.h>
#include <hal/nrf_gpio.h>
#include <hal/nrf_uarte.h>

LOG_MODULE_REGISTER(sensor_ld2410s, LOG_LEVEL_INF);

#define ZEPHYR_USER_NODE DT_PATH(zephyr_user)

namespace {

// RAII scope guard ensuring uart0 is always suspended when leaving a transaction
class ScopedUartWake {
public:
    ScopedUartWake(int (*resumeFn)(void *), int (*suspendFn)(void *), void *ctx)
        : mSuspendFn(suspendFn), mCtx(ctx), mActive(false)
    {
        if (resumeFn(mCtx) == 0) {
            mActive = true;
        }
    }

    ~ScopedUartWake()
    {
        if (mActive && mSuspendFn) {
            mSuspendFn(mCtx);
        }
    }

    ScopedUartWake(const ScopedUartWake &) = delete;
    ScopedUartWake &operator=(const ScopedUartWake &) = delete;

private:
    int (*mSuspendFn)(void *);
    void *mCtx;
    bool mActive;
};

} // namespace

SensorLd2410s::SensorLd2410s()
    : mUartDev(DEVICE_DT_GET_OR_NULL(DT_NODELABEL(uart0))),
      mOt2Gpio(GPIO_DT_SPEC_GET_OR(ZEPHYR_USER_NODE, presence_ot2_gpios, {0})),
      mEdgeCallback(nullptr),
      mLastBootReport{Ld2410sTargetState::Unoccupied, false, false, 0, 0, true},
      mRxRing{},
      mRxHead(0),
      mRxTail(0),
      mRxBytesSeen(0),
      mLastDistanceMm(0),
      mHasBootReport(false),
      mSwapRxTxPins(false),
      mUartSuspended(false),
      mRadarConfigured(false)
{
}

void SensorLd2410s::OnOt2GpioIsr(const struct device *port, struct gpio_callback *cb, uint32_t pins)
{
    ARG_UNUSED(port);
    ARG_UNUSED(pins);
    SensorLd2410s *self = CONTAINER_OF(cb, SensorLd2410s, mOt2CbData);
    if (self->mEdgeCallback) {
        self->mEdgeCallback();
    }
}

void SensorLd2410s::OnUartIsr(const struct device *dev, void *userData)
{
    auto *self = static_cast<SensorLd2410s *>(userData);
    if (!self || !dev) {
        return;
    }

    while (uart_irq_update(dev) && uart_irq_is_pending(dev)) {
        (void)uart_err_check(dev);
        if (uart_irq_rx_ready(dev)) {
            uint8_t buf[32];
            int recvLen = uart_fifo_read(dev, buf, sizeof(buf));
            if (recvLen > 0) {
                self->mRxBytesSeen = self->mRxBytesSeen + static_cast<uint32_t>(recvLen);
                for (int i = 0; i < recvLen; ++i) {
                    const uint32_t head     = self->mRxHead;
                    const uint32_t nextHead = (head + 1u) % kRxRingSize;
                    if (nextHead != self->mRxTail) {
                        self->mRxRing[head] = buf[i];
                        self->mRxHead       = nextHead;
                    }
                }
                k_sem_give(&self->mRxSem);
            }
        }
    }
}

bool SensorLd2410s::PopRxByte(uint8_t *outByte)
{
    const uint32_t tail = mRxTail;
    if (tail == mRxHead) {
        return false;
    }
    *outByte = mRxRing[tail];
    mRxTail  = (tail + 1u) % kRxRingSize;
    return true;
}

void SensorLd2410s::ApplyUartPinMapping(bool swapPins)
{
    mSwapRxTxPins = swapPins;
    const uint32_t rxPin = swapPins ? kUartAltRxPin : kUartDefaultRxPin;
    const uint32_t txPin = swapPins ? kUartAltTxPin : kUartDefaultTxPin;

    if (mUartDev) {
        uart_irq_rx_disable(mUartDev);
        uart_irq_err_disable(mUartDev);
    }

    nrf_uarte_task_trigger(NRF_UARTE0, NRF_UARTE_TASK_STOPRX);
    k_busy_wait(100);
    nrf_uarte_disable(NRF_UARTE0);

    nrf_gpio_pin_set(txPin);
    nrf_gpio_cfg(txPin,
                 NRF_GPIO_PIN_DIR_OUTPUT,
                 NRF_GPIO_PIN_INPUT_DISCONNECT,
                 NRF_GPIO_PIN_NOPULL,
                 NRF_GPIO_PIN_S0S1,
                 NRF_GPIO_PIN_NOSENSE);
    nrf_gpio_cfg(rxPin,
                 NRF_GPIO_PIN_DIR_INPUT,
                 NRF_GPIO_PIN_INPUT_CONNECT,
                 NRF_GPIO_PIN_PULLUP,
                 NRF_GPIO_PIN_S0S1,
                 NRF_GPIO_PIN_NOSENSE);

    nrf_uarte_txrx_pins_set(NRF_UARTE0, txPin, rxPin);
    nrf_uarte_enable(NRF_UARTE0);
    nrf_uarte_event_clear(NRF_UARTE0, NRF_UARTE_EVENT_ERROR);
    nrf_uarte_event_clear(NRF_UARTE0, NRF_UARTE_EVENT_ENDRX);
    nrf_uarte_event_clear(NRF_UARTE0, NRF_UARTE_EVENT_RXTO);
    nrf_uarte_event_clear(NRF_UARTE0, NRF_UARTE_EVENT_RXSTARTED);
    nrf_uarte_task_trigger(NRF_UARTE0, NRF_UARTE_TASK_STARTRX);

    if (mUartDev) {
        uart_irq_err_enable(mUartDev);
        uart_irq_rx_enable(mUartDev);
    }
    DrainUartRx();
}

void SensorLd2410s::ParseBufferedBootReports()
{
    uint8_t rxByte = 0;
    while (PopRxByte(&rxByte)) {
        Ld2410sParsedFrame frame{};
        if (mParser.PushByte(rxByte, &frame) && frame.type == Ld2410sFrameType::Report) {
            mLastBootReport = frame.report;
            mHasBootReport  = true;
            if (frame.report.occupied && frame.report.distanceMm > 0) {
                mLastDistanceMm = frame.report.distanceMm;
            }
        }
    }
}

int SensorLd2410s::ResumeUart()
{
    if (!mUartDev || !device_is_ready(mUartDev)) {
        return -ENODEV;
    }
    if (mUartSuspended) {
        int ret = pm_device_action_run(mUartDev, PM_DEVICE_ACTION_RESUME);
        if (ret != 0 && ret != -EALREADY && ret != -ENOSYS) {
            LOG_WRN("Failed to resume uart0 (err: %d)", ret);
            return ret;
        }
        mUartSuspended = false;
        k_busy_wait(200);
        if (mSwapRxTxPins) {
            ApplyUartPinMapping(true);
            return 0;
        }
    }
    nrf_uarte_enable(NRF_UARTE0);
    if (!nrf_uarte_event_check(NRF_UARTE0, NRF_UARTE_EVENT_RXSTARTED)) {
        nrf_uarte_task_trigger(NRF_UARTE0, NRF_UARTE_TASK_STARTRX);
    }
    uart_irq_err_enable(mUartDev);
    uart_irq_rx_enable(mUartDev);
    return 0;
}

int SensorLd2410s::SuspendUart()
{
    if (!mUartDev || !device_is_ready(mUartDev)) {
        return -ENODEV;
    }
    uart_irq_rx_disable(mUartDev);
    uart_irq_err_disable(mUartDev);
    if (mUartSuspended) {
        return 0;
    }
    k_msleep(2);
    int ret = pm_device_action_run(mUartDev, PM_DEVICE_ACTION_SUSPEND);
    if (ret == 0 || ret == -EALREADY || ret == -ENOSYS) {
        mUartSuspended = true;
        return 0;
    }
    LOG_WRN("Failed to suspend uart0 (err: %d)", ret);
    return ret;
}

void SensorLd2410s::DrainUartRx()
{
    if (mUartDev) {
        uint8_t dummy[32];
        int maxDrain = 16;
        while (maxDrain-- > 0 && uart_fifo_read(mUartDev, dummy, sizeof(dummy)) > 0) {
        }
    }
    unsigned int key = irq_lock();
    mRxTail = mRxHead;
    irq_unlock(key);
    k_sem_reset(&mRxSem);
    mParser.Reset();
}

void SensorLd2410s::SendBytes(const uint8_t *data, size_t len)
{
    if (!mUartDev || !data) {
        return;
    }
    for (size_t i = 0; i < len; ++i) {
        uart_poll_out(mUartDev, data[i]);
    }
}

bool SensorLd2410s::SendCommandAndWaitAck(const uint8_t *cmdBuf,
                                          size_t cmdLen,
                                          uint16_t expectedCmdWord,
                                          uint32_t timeoutMs)
{
    DrainUartRx();
    SendBytes(cmdBuf, cmdLen);

    const uint16_t expectedAck = expectedCmdWord | Ld2410sProto::kAckBitMask;
    const int64_t deadline = k_uptime_get() + static_cast<int64_t>(timeoutMs);

    while (true) {
        uint8_t rxByte = 0;
        while (PopRxByte(&rxByte)) {
            Ld2410sParsedFrame frame{};
            if (mParser.PushByte(rxByte, &frame) && frame.type == Ld2410sFrameType::Ack) {
                if (frame.ack.ackCommandWord == expectedAck) {
                    return frame.ack.status == 0x0000u;
                }
            }
        }

        const int64_t remainingMs = deadline - k_uptime_get();
        if (remainingMs <= 0) {
            break;
        }
        k_sem_take(&mRxSem, K_MSEC(remainingMs));
    }
    return false;
}

int SensorLd2410s::ConfigureRadarParameters()
{
    if (!mUartDev || !device_is_ready(mUartDev)) {
        LOG_ERR("uart0 device not ready");
        return -ENODEV;
    }

    auto resumeCb = [](void *ctx) -> int { return static_cast<SensorLd2410s *>(ctx)->ResumeUart(); };
    auto suspendCb = [](void *ctx) -> int { return static_cast<SensorLd2410s *>(ctx)->SuspendUart(); };
    ScopedUartWake uartWake(resumeCb, suspendCb, this);

    uint8_t cmdBuf[64];

    // 1. Enter configuration mode (0x00FF)
    const size_t enterLen = Ld2410sProto::BuildEnterConfigCmd(cmdBuf, sizeof(cmdBuf));
    bool entered = false;
    for (int attempt = 0; attempt < kConfigMaxRetries; ++attempt) {
        if (SendCommandAndWaitAck(cmdBuf, enterLen, Ld2410sProto::kCmdEnterConfig, kAckTimeoutMs)) {
            entered = true;
            break;
        }
        k_msleep(kInterCommandDelayMs);
    }

    if (!entered) {
        LOG_WRN("HLK-LD2410S did not ACK EnterConfig (0x00FF); proceeding with OT2 GPIO + default radar profile");
        return -ETIMEDOUT;
    }

    k_msleep(kInterCommandDelayMs);

    // 2. Write 3 m^3 bathroom gate & hold parameters (0x0070)
    const Ld2410sConfigParams params = {
        .farthestGate           = static_cast<uint32_t>(CONFIG_APP_RADAR_MAX_GATE),
        .nearestGate            = static_cast<uint32_t>(CONFIG_APP_RADAR_MIN_GATE),
        .unoccupiedHoldSec      = static_cast<uint32_t>(CONFIG_APP_RADAR_HOLD_S),
        .statusReportFreqHz10   = Ld2410sProto::kDefaultReportFreqTenthsHz,
        .distanceReportFreqHz10 = Ld2410sProto::kDefaultReportFreqTenthsHz,
        .responseSpeed          = Ld2410sProto::kDefaultResponseSpeedNormal,
    };

    const size_t writeLen = Ld2410sProto::BuildWriteCommonParamsCmd(params, cmdBuf, sizeof(cmdBuf));
    if (!SendCommandAndWaitAck(cmdBuf, writeLen, Ld2410sProto::kCmdWriteCommonParams, kAckTimeoutMs)) {
        LOG_WRN("HLK-LD2410S did not ACK WriteCommonParams (0x0070)");
    }

    k_msleep(kInterCommandDelayMs);

    // 3. Switch to Minimal 5-Byte Output Format (0x007A -> 6E [state] [dist_lo] [dist_hi] 62)
    const size_t modeLen = Ld2410sProto::BuildSwitchOutputModeCmd(
        Ld2410sProto::kOutputModeMinimal, cmdBuf, sizeof(cmdBuf));
    if (!SendCommandAndWaitAck(cmdBuf, modeLen, Ld2410sProto::kCmdSwitchOutputMode, kAckTimeoutMs)) {
        LOG_WRN("HLK-LD2410S did not ACK SwitchOutputMode (0x007A)");
    }

    k_msleep(kInterCommandDelayMs);

    // 4. Exit configuration mode (0x00FE)
    const size_t exitLen = Ld2410sProto::BuildExitConfigCmd(cmdBuf, sizeof(cmdBuf));
    if (!SendCommandAndWaitAck(cmdBuf, exitLen, Ld2410sProto::kCmdExitConfig, kAckTimeoutMs)) {
        LOG_WRN("HLK-LD2410S did not ACK ExitConfig (0x00FE)");
    }

    mRadarConfigured = true;
    LOG_INF("HLK-LD2410S configured (max_gate=%d [%.1f m], min_gate=%d, hold=%d s, minimal 5B output)",
            CONFIG_APP_RADAR_MAX_GATE,
            static_cast<double>(CONFIG_APP_RADAR_MAX_GATE) * 0.7,
            CONFIG_APP_RADAR_MIN_GATE,
            CONFIG_APP_RADAR_HOLD_S);
    return 0;
}

int SensorLd2410s::Init(Ot2EdgeCallback edgeCb)
{
    mEdgeCallback = edgeCb;
    k_sem_init(&mRxSem, 0, 1);

    if (mUartDev && device_is_ready(mUartDev)) {
        uart_irq_callback_user_data_set(mUartDev, OnUartIsr, this);
    } else {
        LOG_ERR("uart0 device not ready");
    }

    if (mOt2Gpio.port == nullptr || !device_is_ready(mOt2Gpio.port)) {
        LOG_ERR("OT2 presence GPIO (P0.17) not ready");
        return -ENODEV;
    }

    int ret = gpio_pin_configure_dt(&mOt2Gpio, GPIO_INPUT);
    if (ret != 0) {
        LOG_ERR("Failed to configure OT2 GPIO input (err: %d)", ret);
        return ret;
    }

    gpio_init_callback(&mOt2CbData, OnOt2GpioIsr, BIT(mOt2Gpio.pin));
    ret = gpio_add_callback(mOt2Gpio.port, &mOt2CbData);
    if (ret != 0) {
        LOG_ERR("Failed to add OT2 GPIO callback (err: %d)", ret);
        return ret;
    }

    ret = gpio_pin_interrupt_configure_dt(&mOt2Gpio, GPIO_INT_EDGE_BOTH);
    if (ret != 0) {
        LOG_ERR("Failed to enable OT2 edge interrupt (err: %d)", ret);
        return ret;
    }

    LOG_INF("HLK-LD2410S OT2 interrupt armed on P0.%02d (GPIO_INT_EDGE_BOTH)", mOt2Gpio.pin);

    // Enable UART0 RX before the 1000 ms boot settle window so any boot stream frames
    // emitted by the HLK-LD2410S (PY32F030 MCU + ICL1112 MMIC) are captured in mRxRing.
    ResumeUart();
    k_msleep(kRadarBootSettleMs);

    LOG_INF("HLK-LD2410S boot settle complete (rx_bytes=%u on RX=P0.08, TX=P0.06)", mRxBytesSeen);
    ParseBufferedBootReports();

    ConfigureRadarParameters();

    // If no valid report frame arrived on the default pin mapping (RX=P0.08, TX=P0.06) and
    // configuration did not ACK, automatically probe swapped pins (RX=P0.06, TX=P0.08).
    if (!mHasBootReport && !mRadarConfigured) {
        LOG_WRN("No valid frame/ACK on default UART pins (RX=P0.08, TX=P0.06, rx_bytes=%u); probing swapped pins (RX=P0.06, TX=P0.08)",
                mRxBytesSeen);
        ApplyUartPinMapping(true);
        k_msleep(kPinSwapProbeSettleMs);
        ParseBufferedBootReports();
        if (ConfigureRadarParameters() == 0 || mHasBootReport) {
            LOG_INF("HLK-LD2410S active on swapped UART pins (RX=P0.06, TX=P0.08, rx_bytes=%u)", mRxBytesSeen);
        } else {
            LOG_WRN("No response on swapped UART pins; restoring default mapping (RX=P0.08, TX=P0.06)");
            ApplyUartPinMapping(false);
        }
    }

    // Ensure uart0 is suspended after boot configuration even if ScopedUartWake
    // started with mUartSuspended == false.
    SuspendUart();

    return 0;
}

bool SensorLd2410s::ReadPinOccupancy() const
{
    if (mOt2Gpio.port == nullptr || !device_is_ready(mOt2Gpio.port)) {
        return false;
    }
    return gpio_pin_get_dt(&mOt2Gpio) > 0;
}

int SensorLd2410s::SampleTargetReport(Ld2410sReport *outReport, uint32_t timeoutMs)
{
    if (!outReport) {
        return -EINVAL;
    }

    const bool pinOccupied = ReadPinOccupancy();

    // Flush stale ring-buffer bytes BEFORE waking UART0 so no incoming byte
    // received immediately after ResumeUart() is discarded.
    DrainUartRx();

    // Briefly resume uart0 and enable RX interrupt to capture one report frame from the radar
    auto resumeCb = [](void *ctx) -> int { return static_cast<SensorLd2410s *>(ctx)->ResumeUart(); };
    auto suspendCb = [](void *ctx) -> int { return static_cast<SensorLd2410s *>(ctx)->SuspendUart(); };
    ScopedUartWake uartWake(resumeCb, suspendCb, this);

    const int64_t deadline = k_uptime_get() + static_cast<int64_t>(timeoutMs);
    while (true) {
        uint8_t rxByte = 0;
        while (PopRxByte(&rxByte)) {
            Ld2410sParsedFrame frame{};
            if (mParser.PushByte(rxByte, &frame) && frame.type == Ld2410sFrameType::Report) {
                mHasBootReport = false;
                *outReport = frame.report;
                if (pinOccupied && !outReport->occupied) {
                    outReport->occupied = true;
                }
                if (outReport->occupied) {
                    if (outReport->distanceMm > 0) {
                        mLastDistanceMm = outReport->distanceMm;
                    } else if (mLastDistanceMm > 0) {
                        outReport->distanceMm = mLastDistanceMm;
                        outReport->distanceCm = static_cast<uint16_t>(mLastDistanceMm / 10u);
                    }
                } else {
                    mLastDistanceMm       = 0;
                    outReport->distanceMm = 0;
                    outReport->distanceCm = 0;
                }
                return 0;
            }
        }

        const int64_t remainingMs = deadline - k_uptime_get();
        if (remainingMs <= 0) {
            break;
        }
        k_sem_take(&mRxSem, K_MSEC(remainingMs));
    }

    // If a valid report was already captured during the boot settle window, use it
    if (mHasBootReport) {
        mHasBootReport = false;
        *outReport     = mLastBootReport;
        if (pinOccupied && !outReport->occupied) {
            outReport->occupied = true;
        }
        return 0;
    }

    // Fallback if no UART report frame arrived within timeoutMs: use hardware OT2 pin state
    if (pinOccupied) {
        outReport->state          = Ld2410sTargetState::Stationary;
        outReport->occupied       = true;
        outReport->motion         = false;
        outReport->distanceMm     = mLastDistanceMm;
        outReport->distanceCm     = static_cast<uint16_t>(mLastDistanceMm / 10u);
        outReport->isMinimalFrame = true;
    } else {
        mLastDistanceMm           = 0;
        outReport->state          = Ld2410sTargetState::Unoccupied;
        outReport->occupied       = false;
        outReport->motion         = false;
        outReport->distanceMm     = 0;
        outReport->distanceCm     = 0;
        outReport->isMinimalFrame = true;
    }
    return 0;
}
