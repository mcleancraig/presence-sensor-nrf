/*
 * Copyright (c) 2026 Craig McLean
 * Zephyr HLK-LD2410S / HLK-LD2410C 24 GHz mmWave Radar Driver (OT2/OUT Edge Wake + UART0 Runtime PM)
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

#if defined(CONFIG_APP_RADAR_LD2410C)
static constexpr const char *kRadarModelTag        = "HLK-LD2410C";
static constexpr uint32_t    kPrimaryUartBaudReg   = static_cast<uint32_t>(NRF_UARTE_BAUDRATE_250000);
static constexpr uint32_t    kFallbackUartBaudReg  = static_cast<uint32_t>(NRF_UARTE_BAUDRATE_115200);
#else
static constexpr const char *kRadarModelTag        = "HLK-LD2410S";
static constexpr uint32_t    kPrimaryUartBaudReg   = static_cast<uint32_t>(NRF_UARTE_BAUDRATE_115200);
static constexpr uint32_t    kFallbackUartBaudReg  = static_cast<uint32_t>(NRF_UARTE_BAUDRATE_250000);
#endif

} // namespace

SensorLd2410s::SensorLd2410s()
    : mUartDev(DEVICE_DT_GET_OR_NULL(DT_NODELABEL(uart0))),
      mOt2Gpio(GPIO_DT_SPEC_GET_OR(ZEPHYR_USER_NODE, presence_ot2_gpios, {0})),
      mEdgeCallback(nullptr),
      mLastValidReport{Ld2410sTargetState::Unoccupied, false, false, 0, 0, true, false},
      mLastUartReportMs(0),
      mRxRing{},
      mRxHead(0),
      mRxTail(0),
      mRxBytesSeen(0),
      mUartBaudrateReg(kPrimaryUartBaudReg),
      mLastDistanceMm(0),
      mHasValidUartReport(false),
      mSwapRxTxPins(false),
      mUartSuspended(false),
      mRadarConfigured(false),
      mOt2SignalSeen(false)
{
}

void SensorLd2410s::OnOt2GpioIsr(const struct device *port, struct gpio_callback *cb, uint32_t pins)
{
    ARG_UNUSED(port);
    ARG_UNUSED(pins);
    SensorLd2410s *self = CONTAINER_OF(cb, SensorLd2410s, mOt2CbData);
    self->mOt2SignalSeen = true;
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

    if (mUartDev && mUartSuspended) {
        (void)pm_device_action_run(mUartDev, PM_DEVICE_ACTION_RESUME);
        mUartSuspended = false;
        k_busy_wait(200);
    }

    if (mUartDev) {
        uart_irq_rx_disable(mUartDev);
        uart_irq_err_disable(mUartDev);
    }

    if (nrf_uarte_event_check(NRF_UARTE0, NRF_UARTE_EVENT_RXSTARTED)) {
        nrf_uarte_event_clear(NRF_UARTE0, NRF_UARTE_EVENT_RXTO);
        nrf_uarte_task_trigger(NRF_UARTE0, NRF_UARTE_TASK_STOPRX);
        for (int i = 0; i < 200 && !nrf_uarte_event_check(NRF_UARTE0, NRF_UARTE_EVENT_RXTO); ++i) {
            k_busy_wait(10);
        }
    }
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

    nrf_uarte_baudrate_set(NRF_UARTE0, static_cast<nrf_uarte_baudrate_t>(mUartBaudrateReg));
    nrf_uarte_txrx_pins_set(NRF_UARTE0, txPin, rxPin);
    (void)nrf_uarte_errorsrc_get_and_clear(NRF_UARTE0);
    nrf_uarte_event_clear(NRF_UARTE0, NRF_UARTE_EVENT_ERROR);
    nrf_uarte_event_clear(NRF_UARTE0, NRF_UARTE_EVENT_ENDRX);
    nrf_uarte_event_clear(NRF_UARTE0, NRF_UARTE_EVENT_RXTO);
    nrf_uarte_event_clear(NRF_UARTE0, NRF_UARTE_EVENT_RXSTARTED);
    nrf_uarte_enable(NRF_UARTE0);
    nrf_uarte_task_trigger(NRF_UARTE0, NRF_UARTE_TASK_STARTRX);

    if (mUartDev) {
        uart_irq_err_enable(mUartDev);
        uart_irq_rx_enable(mUartDev);
    }
    DrainUartRx();
}

void SensorLd2410s::LogRxRingPreview(const char *stageTag) const
{
    const uint32_t errSrc = nrf_uarte_errorsrc_get_and_clear(NRF_UARTE0);
    const uint32_t tail   = mRxTail;
    const uint32_t head   = mRxHead;
    const uint32_t avail  = (head >= tail) ? (head - tail) : (kRxRingSize - tail + head);

    static constexpr char kHexDigits[17] = "0123456789ABCDEF";
    char hexBuf[64];
    size_t pos = 0;
    const uint32_t maxPreview = (avail < 16u) ? avail : 16u;
    for (uint32_t i = 0; i < maxPreview && (pos + 4u) < sizeof(hexBuf); ++i) {
        const uint8_t b = mRxRing[(tail + i) % kRxRingSize];
        hexBuf[pos++] = kHexDigits[(b >> 4) & 0x0Fu];
        hexBuf[pos++] = kHexDigits[b & 0x0Fu];
        hexBuf[pos++] = ' ';
    }
    hexBuf[pos] = '\0';

    LOG_INF("[%s] rx_bytes=%u ring_avail=%u errsrc=0x%02X ot2_pin=%d baud_reg=0x%08X swap=%d sample=[%s]",
            stageTag ? stageTag : "uart",
            mRxBytesSeen,
            avail,
            errSrc,
            ReadPinOccupancy() ? 1 : 0,
            mUartBaudrateReg,
            mSwapRxTxPins ? 1 : 0,
            hexBuf);
}

void SensorLd2410s::ParseBufferedBootReports()
{
    static constexpr uint16_t kMaxDistanceMm =
        static_cast<uint16_t>(CONFIG_APP_RADAR_MAX_DISTANCE_MM);

    uint8_t rxByte = 0;
    while (PopRxByte(&rxByte)) {
        Ld2410sParsedFrame frame{};
        if (mParser.PushByte(rxByte, &frame) && frame.type == Ld2410sFrameType::Report) {
            if (!frame.report.occupied ||
                frame.report.distanceMm == 0u ||
                frame.report.distanceMm > kMaxDistanceMm) {
                frame.report.state      = Ld2410sTargetState::Unoccupied;
                frame.report.occupied   = false;
                frame.report.motion     = false;
                frame.report.distanceCm = 0u;
                frame.report.distanceMm = 0u;
            }
            mLastValidReport    = frame.report;
            mHasValidUartReport = true;
            mLastUartReportMs   = k_uptime_get();
            mLastDistanceMm     = frame.report.occupied ? frame.report.distanceMm : 0u;
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
        ApplyUartPinMapping(mSwapRxTxPins);
        return 0;
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
    if (IS_ENABLED(CONFIG_APP_ALWAYS_USB_POWERED)) {
        return 0;
    }
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

    (void)ResumeUart();

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
        LOG_WRN("%s did not ACK EnterConfig (0x00FF); proceeding with OT2/OUT GPIO + default radar profile",
                kRadarModelTag);
        return -ETIMEDOUT;
    }

    k_msleep(kInterCommandDelayMs);

#if defined(CONFIG_APP_RADAR_LD2410C)
    // 2. Write HLK-LD2410C max moving/stationary gate & unoccupied duration (0x0060)
    const Ld2410cConfigParams cParams = {
        .maxMovingGate     = static_cast<uint32_t>(CONFIG_APP_RADAR_MAX_GATE),
        .maxStationaryGate = static_cast<uint32_t>(CONFIG_APP_RADAR_MAX_GATE),
        .unoccupiedHoldSec = static_cast<uint32_t>(CONFIG_APP_RADAR_HOLD_S),
    };

    const size_t writeLen = Ld2410sProto::BuildLd2410cWriteMaxGateAndHoldCmd(cParams, cmdBuf, sizeof(cmdBuf));
    if (!SendCommandAndWaitAck(cmdBuf, writeLen, Ld2410sProto::kCmdWriteMaxGateAndHold, kAckTimeoutMs)) {
        LOG_WRN("HLK-LD2410C did not ACK WriteMaxGateAndHold (0x0060)");
    }

    k_msleep(kInterCommandDelayMs);

    // 3. Exit configuration mode (0x00FE)
    const size_t exitLen = Ld2410sProto::BuildExitConfigCmd(cmdBuf, sizeof(cmdBuf));
    if (!SendCommandAndWaitAck(cmdBuf, exitLen, Ld2410sProto::kCmdExitConfig, kAckTimeoutMs)) {
        LOG_WRN("HLK-LD2410C did not ACK ExitConfig (0x00FE)");
    }

    mRadarConfigured = true;
    LOG_INF("HLK-LD2410C configured (max_gate=%d [%.2f m], hold=%d s, 256000 baud)",
            CONFIG_APP_RADAR_MAX_GATE,
            static_cast<double>(CONFIG_APP_RADAR_MAX_GATE) * 0.75,
            CONFIG_APP_RADAR_HOLD_S);
#else
    // 2. Write 3 m^3 bathroom gate & hold parameters (0x0070)
    const Ld2410sConfigParams params = {
        .farthestGate           = static_cast<uint32_t>(CONFIG_APP_RADAR_MAX_GATE),
        .nearestGate            = static_cast<uint32_t>(CONFIG_APP_RADAR_MIN_GATE),
        .unoccupiedHoldSec      = static_cast<uint32_t>(CONFIG_APP_RADAR_HOLD_S),
        .statusReportFreqHz10   = Ld2410sProto::kDefaultReportFreqTenthsHz,
        .distanceReportFreqHz10 = Ld2410sProto::kDefaultReportFreqTenthsHz,
        .responseSpeed          = Ld2410sProto::kDefaultResponseSpeedFast,
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
    LOG_INF("HLK-LD2410S configured (max_gate=%d [%.1f m], min_gate=%d, hold=%d s, 8.0 Hz fast, minimal 5B output)",
            CONFIG_APP_RADAR_MAX_GATE,
            static_cast<double>(CONFIG_APP_RADAR_MAX_GATE) * 0.7,
            CONFIG_APP_RADAR_MIN_GATE,
            CONFIG_APP_RADAR_HOLD_S);
#endif
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

    LOG_INF("%s OT2/OUT interrupt armed on P0.%02d (GPIO_INT_EDGE_BOTH, initial_pin=%d)",
            kRadarModelTag, mOt2Gpio.pin, ReadPinOccupancy() ? 1 : 0);

    // Apply primary UART baudrate (256000/250000 for LD2410C, 115200 for LD2410S) and enable RX
    // before the 1000 ms boot settle window so any boot stream frames are captured in mRxRing.
    ApplyUartPinMapping(false);
    ResumeUart();
    k_msleep(kRadarBootSettleMs);

    LogRxRingPreview("boot-default");
    ParseBufferedBootReports();

    ConfigureRadarParameters();
    if (!mHasValidUartReport) {
        k_msleep(250);
        ParseBufferedBootReports();
    }

    // If no valid report frame arrived on the default pin mapping (RX=P0.08, TX=P0.06) and
    // configuration did not ACK, automatically probe swapped pins and fallback baudrates.
    if (!mHasValidUartReport && !mRadarConfigured) {
        LOG_WRN("No valid frame/ACK on default UART pins (RX=P0.08, TX=P0.06, rx_bytes=%u); probing swapped pins (RX=P0.06, TX=P0.08)",
                mRxBytesSeen);
        ApplyUartPinMapping(true);
        k_msleep(kPinSwapProbeSettleMs);
        LogRxRingPreview("probe-swap-primary");
        ParseBufferedBootReports();
        if (ConfigureRadarParameters() == 0 || mHasValidUartReport) {
            LOG_INF("%s active on swapped UART pins (RX=P0.06, TX=P0.08, rx_bytes=%u)", kRadarModelTag, mRxBytesSeen);
        } else {
            // Probe fallback UART baudrate (115200 <-> 256000) on default pins
            mUartBaudrateReg = kFallbackUartBaudReg;
            ApplyUartPinMapping(false);
            k_msleep(kPinSwapProbeSettleMs);
            LogRxRingPreview("probe-default-fallback");
            ParseBufferedBootReports();
            if (ConfigureRadarParameters() == 0 || mHasValidUartReport) {
                LOG_INF("%s active on fallback baudrate (RX=P0.08, TX=P0.06, rx_bytes=%u)", kRadarModelTag, mRxBytesSeen);
            } else {
                // Probe fallback UART baudrate on swapped pins
                ApplyUartPinMapping(true);
                k_msleep(kPinSwapProbeSettleMs);
                LogRxRingPreview("probe-swap-fallback");
                ParseBufferedBootReports();
                if (ConfigureRadarParameters() == 0 || mHasValidUartReport) {
                    LOG_INF("%s active on swapped pins + fallback baudrate (RX=P0.06, TX=P0.08, rx_bytes=%u)",
                            kRadarModelTag, mRxBytesSeen);
                } else {
                    LOG_WRN("No response on swapped pins or fallback baudrate; restoring primary UART config");
                    mUartBaudrateReg = kPrimaryUartBaudReg;
                    ApplyUartPinMapping(false);
                }
            }
        }
    }

    // Keep uart0 RX continuously active in interrupt mode so OnUartIsr captures 100%
    // of asynchronous 5-byte / Standard radar frames into mRxRing with zero blind spots.
    ResumeUart();
    LOG_INF("%s Init done: valid_uart=%d cfg=%d swap=%d baud_reg=0x%08X rx_bytes=%u ot2_pin=%d",
            kRadarModelTag,
            mHasValidUartReport ? 1 : 0,
            mRadarConfigured ? 1 : 0,
            mSwapRxTxPins ? 1 : 0,
            mUartBaudrateReg,
            mRxBytesSeen,
            ReadPinOccupancy() ? 1 : 0);

    return 0;
}

bool SensorLd2410s::ReadPinOccupancy() const
{
    if (mOt2Gpio.port == nullptr || !device_is_ready(mOt2Gpio.port)) {
        return false;
    }
    return gpio_pin_get_dt(&mOt2Gpio) > 0;
}

void SensorLd2410s::LogDiagnostics(const Ld2410sReport &report, const char *reasonTag) const
{
    const uint32_t errSrc = nrf_uarte_errorsrc_get_and_clear(NRF_UARTE0);
    LOG_INF("[%s] occ=%s motion=%s state=%u dist=%u mm | ot2_pin=%d ot2_seen=%d rx_bytes=%u valid_uart=%d cfg=%d swap=%d baud=0x%08X err=0x%02X",
            reasonTag ? reasonTag : "poll",
            report.occupied ? "ON" : "OFF",
            report.motion ? "ON" : "OFF",
            static_cast<unsigned int>(report.state),
            static_cast<unsigned int>(report.distanceMm),
            ReadPinOccupancy() ? 1 : 0,
            mOt2SignalSeen ? 1 : 0,
            mRxBytesSeen,
            mHasValidUartReport ? 1 : 0,
            mRadarConfigured ? 1 : 0,
            mSwapRxTxPins ? 1 : 0,
            mUartBaudrateReg,
            errSrc);
}

int SensorLd2410s::SampleTargetReport(Ld2410sReport *outReport, uint32_t timeoutMs)
{
    if (!outReport) {
        return -EINVAL;
    }

    const bool pinOccupied = ReadPinOccupancy();
    if (pinOccupied) {
        mOt2SignalSeen = true;
    }

    ResumeUart();

    static constexpr uint16_t kMaxDistanceMm =
        static_cast<uint16_t>(CONFIG_APP_RADAR_MAX_DISTANCE_MM);

    auto drainFramesFromRing = [&]() -> bool {
        bool decodedAny         = false;
        bool sawMovingInBatch   = false;
        uint16_t movingDistCm   = 0u;
        uint16_t movingDistMm   = 0u;
        uint8_t rxByte          = 0;
        while (PopRxByte(&rxByte)) {
            Ld2410sParsedFrame frame{};
            if (mParser.PushByte(rxByte, &frame) && frame.type == Ld2410sFrameType::Report) {
                if (!frame.report.occupied ||
                    frame.report.distanceMm == 0u ||
                    frame.report.distanceMm > kMaxDistanceMm) {
                    frame.report.state      = Ld2410sTargetState::Unoccupied;
                    frame.report.occupied   = false;
                    frame.report.motion     = false;
                    frame.report.distanceCm = 0u;
                    frame.report.distanceMm = 0u;
                } else if (frame.report.motion || frame.report.state == Ld2410sTargetState::Moving) {
                    sawMovingInBatch = true;
                    movingDistCm     = frame.report.distanceCm;
                    movingDistMm     = frame.report.distanceMm;
                }
                mLastValidReport    = frame.report;
                mHasValidUartReport = true;
                mLastUartReportMs   = k_uptime_get();
                mLastDistanceMm     = frame.report.occupied ? frame.report.distanceMm : 0u;
                decodedAny          = true;
            }
        }
        // Preserve Moving state across a multi-frame batch so a trailing Stationary (0x02) frame
        // never masks an earlier Moving (0x01/0x03) frame buffered in the same poll window.
        if (decodedAny && sawMovingInBatch && mLastValidReport.occupied) {
            mLastValidReport.state      = Ld2410sTargetState::Moving;
            mLastValidReport.motion     = true;
            if (movingDistMm > 0u) {
                mLastValidReport.distanceCm = movingDistCm;
                mLastValidReport.distanceMm = movingDistMm;
                mLastDistanceMm             = movingDistMm;
            }
        }
        return decodedAny;
    };

    // 1. Drain all complete frames already buffered in mRxRing by OnUartIsr (0 ms non-blocking!)
    if (drainFramesFromRing()) {
        *outReport = mLastValidReport;
        return 0;
    }

    // 2. If no new frame completed during this 400 ms tick (e.g. radar reporting at 1 Hz / 1000 ms),
    //    return the latest valid UART report immediately without blocking or letting OT2 override it.
    const int64_t nowMs = k_uptime_get();
    if (mHasValidUartReport && (nowMs - mLastUartReportMs) <= kUartStaleReportTimeoutMs) {
        *outReport = mLastValidReport;
        return 0;
    }

    // 3. If UART has been silent for > 2.5 s (or right at boot), wait up to timeoutMs for a frame
    const int64_t deadline = nowMs + static_cast<int64_t>(timeoutMs);
    while (true) {
        if (drainFramesFromRing()) {
            *outReport = mLastValidReport;
            return 0;
        }
        const int64_t remainingMs = deadline - k_uptime_get();
        if (remainingMs <= 0) {
            break;
        }
        k_sem_take(&mRxSem, K_MSEC(remainingMs));
    }

    // 4. UART has been silent for > 2.5 s:
    //    - If UART has never decoded a frame (!mHasValidUartReport) and OT2/OUT is HIGH, fall back
    //      to hardware OT2/OUT occupancy with a nominal 1000 mm in-range distance.
    //    - If UART was previously active and OT2 is HIGH while last distance was in range, preserve it.
    const uint16_t fallbackDistMm = (!mHasValidUartReport && mLastDistanceMm == 0u) ? 1000u : mLastDistanceMm;
    if (pinOccupied && fallbackDistMm > 0u && fallbackDistMm <= kMaxDistanceMm) {
        outReport->state          = Ld2410sTargetState::Stationary;
        outReport->occupied       = true;
        outReport->motion         = false;
        outReport->distanceMm     = fallbackDistMm;
        outReport->distanceCm     = static_cast<uint16_t>(fallbackDistMm / 10u);
        outReport->isMinimalFrame = true;
        outReport->isLd2410cFrame = false;
    } else {
        mLastDistanceMm           = 0;
        mLastValidReport          = {Ld2410sTargetState::Unoccupied, false, false, 0, 0, true, false};
        outReport->state          = Ld2410sTargetState::Unoccupied;
        outReport->occupied       = false;
        outReport->motion         = false;
        outReport->distanceMm     = 0;
        outReport->distanceCm     = 0;
        outReport->isMinimalFrame = true;
        outReport->isLd2410cFrame = false;
    }
    return 0;
}
