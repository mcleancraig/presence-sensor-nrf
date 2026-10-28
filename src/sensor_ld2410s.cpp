/*
 * Copyright (c) 2026 Craig McLean
 * Zephyr HLK-LD2410S 24 GHz mmWave Radar Driver (OT2 Edge Wake + UART0 Runtime PM)
 */

#include "sensor_ld2410s.h"
#include <zephyr/drivers/uart.h>
#include <zephyr/pm/device.h>
#include <zephyr/logging/log.h>

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
      mLastDistanceMm(0),
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

int SensorLd2410s::ResumeUart()
{
    if (!mUartDev || !device_is_ready(mUartDev)) {
        return -ENODEV;
    }
    if (!mUartSuspended) {
        return 0;
    }
    int ret = pm_device_action_run(mUartDev, PM_DEVICE_ACTION_RESUME);
    if (ret == 0 || ret == -EALREADY) {
        mUartSuspended = false;
        return 0;
    }
    LOG_WRN("Failed to resume uart0 (err: %d)", ret);
    return ret;
}

int SensorLd2410s::SuspendUart()
{
    if (!mUartDev || !device_is_ready(mUartDev)) {
        return -ENODEV;
    }
    if (mUartSuspended) {
        return 0;
    }
    int ret = pm_device_action_run(mUartDev, PM_DEVICE_ACTION_SUSPEND);
    if (ret == 0 || ret == -EALREADY) {
        mUartSuspended = true;
        return 0;
    }
    LOG_WRN("Failed to suspend uart0 (err: %d)", ret);
    return ret;
}

void SensorLd2410s::DrainUartRx()
{
    if (!mUartDev) {
        return;
    }
    uint8_t dummy = 0;
    int maxDrain = 256;
    while (maxDrain-- > 0 && uart_poll_in(mUartDev, &dummy) == 0) {
    }
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

    while (k_uptime_get() < deadline) {
        uint8_t rxByte = 0;
        if (uart_poll_in(mUartDev, &rxByte) == 0) {
            Ld2410sParsedFrame frame{};
            if (mParser.PushByte(rxByte, &frame) && frame.type == Ld2410sFrameType::Ack) {
                if (frame.ack.ackCommandWord == expectedAck) {
                    return frame.ack.status == 0x0000u;
                }
            }
        } else {
            k_msleep(1);
        }
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
        k_msleep(20);
    }

    if (!entered) {
        LOG_WRN("HLK-LD2410S did not ACK EnterConfig (0x00FF); proceeding with OT2 GPIO + default radar profile");
        return -ETIMEDOUT;
    }

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

    // 3. Switch to Minimal 5-Byte Output Format (0x007A -> 6E [state] [dist_lo] [dist_hi] 62)
    const size_t modeLen = Ld2410sProto::BuildSwitchOutputModeCmd(
        Ld2410sProto::kOutputModeMinimal, cmdBuf, sizeof(cmdBuf));
    if (!SendCommandAndWaitAck(cmdBuf, modeLen, Ld2410sProto::kCmdSwitchOutputMode, kAckTimeoutMs)) {
        LOG_WRN("HLK-LD2410S did not ACK SwitchOutputMode (0x007A)");
    }

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

    // Allow HLK-LD2410S internal MCU to complete boot after P0.13 VCC power-on
    k_msleep(80);
    ConfigureRadarParameters();

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
    if (!pinOccupied) {
        mLastDistanceMm            = 0;
        outReport->state           = Ld2410sTargetState::Unoccupied;
        outReport->occupied        = false;
        outReport->motion          = false;
        outReport->distanceCm      = 0;
        outReport->distanceMm      = 0;
        outReport->isMinimalFrame  = true;
        return 0;
    }

    // OT2 is HIGH (occupied): briefly resume uart0 to read the latest target distance frame
    auto resumeCb = [](void *ctx) -> int { return static_cast<SensorLd2410s *>(ctx)->ResumeUart(); };
    auto suspendCb = [](void *ctx) -> int { return static_cast<SensorLd2410s *>(ctx)->SuspendUart(); };
    ScopedUartWake uartWake(resumeCb, suspendCb, this);

    DrainUartRx();

    const int64_t deadline = k_uptime_get() + static_cast<int64_t>(timeoutMs);
    while (k_uptime_get() < deadline) {
        uint8_t rxByte = 0;
        if (uart_poll_in(mUartDev, &rxByte) == 0) {
            Ld2410sParsedFrame frame{};
            if (mParser.PushByte(rxByte, &frame) && frame.type == Ld2410sFrameType::Report) {
                *outReport = frame.report;
                // Keep hardware OT2 pin authoritative if asserted
                if (pinOccupied && !outReport->occupied) {
                    outReport->occupied = true;
                }
                if (outReport->distanceMm > 0) {
                    mLastDistanceMm = outReport->distanceMm;
                }
                return 0;
            }
        } else {
            k_msleep(2);
        }
    }

    // Fallback when OT2 is HIGH between 1 Hz UART reports: report occupied with last known distance
    outReport->state          = Ld2410sTargetState::Stationary;
    outReport->occupied       = true;
    outReport->motion         = false;
    outReport->distanceMm     = mLastDistanceMm;
    outReport->distanceCm     = static_cast<uint16_t>(mLastDistanceMm / 10u);
    outReport->isMinimalFrame = true;
    return 0;
}
