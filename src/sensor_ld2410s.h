/*
 * Copyright (c) 2026 Craig McLean
 * Zephyr HLK-LD2410S 24 GHz mmWave Radar Driver (OT2 Edge Wake + UART0 Runtime PM)
 */

#pragma once

#include "ld2410s_proto.h"
#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/gpio.h>

class SensorLd2410s {
public:
    using Ot2EdgeCallback = void (*)();

    // Bounded UART wake window when sampling target distance on OT2 assertion
    // (1150 ms spans a full 1.0 Hz report period + 150 ms margin while returning
    // and suspending uart0 immediately upon receiving the first valid 5-byte frame)
    static constexpr uint32_t kDefaultSampleTimeoutMs = 1150;
    static constexpr uint32_t kAckTimeoutMs           = 150;
    static constexpr int      kConfigMaxRetries       = 3;

    SensorLd2410s();

    /**
     * @brief Configure P0.17 (OT2) GPIO interrupt, push 3 m^3 bathroom parameters
     *        over uart0 (115200 8N1), and suspend uart0 for zero-uA idle sleep.
     * @param edgeCb Callback invoked from ISR context on any OT2 rising/falling edge.
     * @return 0 on success, negative errno on critical GPIO setup error.
     */
    int Init(Ot2EdgeCallback edgeCb);

    /**
     * @brief Read instantaneous digital occupancy state from P0.17 (OT2).
     * @return true if OT2 is HIGH (occupied), false if LOW (unoccupied).
     */
    bool ReadPinOccupancy() const;

    /**
     * @brief Sample the latest radar state and target distance.
     *        If OT2 is LOW, returns immediately without waking uart0.
     *        If OT2 is HIGH, resumes uart0 for at most timeoutMs to parse one
     *        report frame, then immediately re-suspends uart0.
     */
    int SampleTargetReport(Ld2410sReport *outReport, uint32_t timeoutMs = kDefaultSampleTimeoutMs);

    /**
     * @brief Query whether boot-time UART parameter configuration succeeded.
     */
    bool IsRadarConfigured() const { return mRadarConfigured; }

private:
    static void OnOt2GpioIsr(const struct device *port, struct gpio_callback *cb, uint32_t pins);

    int ResumeUart();
    int SuspendUart();
    void DrainUartRx();
    void SendBytes(const uint8_t *data, size_t len);
    bool SendCommandAndWaitAck(const uint8_t *cmdBuf, size_t cmdLen, uint16_t expectedCmdWord, uint32_t timeoutMs);
    int ConfigureRadarParameters();

    const struct device    *mUartDev;
    struct gpio_dt_spec     mOt2Gpio;
    struct gpio_callback    mOt2CbData;
    Ot2EdgeCallback         mEdgeCallback;
    Ld2410sFrameParser      mParser;
    uint16_t                mLastDistanceMm;
    bool                    mUartSuspended;
    bool                    mRadarConfigured;
};
