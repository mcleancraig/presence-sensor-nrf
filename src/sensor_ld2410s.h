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

    // Bounded UART wake window when sampling target distance:
    // At 8.0 Hz (125 ms frame period), 220 ms spans ~1.75 frame intervals
    // (~62 ms average wake time) while returning and suspending uart0 immediately
    // upon receiving the first valid 5-byte report frame.
    static constexpr uint32_t kDefaultSampleTimeoutMs  = 220;
    static constexpr uint32_t kFallbackSampleTimeoutMs = 1150;
    static constexpr uint32_t kAckTimeoutMs            = 500;
    static constexpr uint32_t kRadarBootSettleMs      = 1000;
    static constexpr uint32_t kPinSwapProbeSettleMs   = 500;
    static constexpr uint32_t kInterCommandDelayMs    = 50;
    static constexpr int      kConfigMaxRetries       = 5;
    static constexpr size_t   kRxRingSize             = 256;
    static constexpr uint32_t kUartDefaultRxPin       = 8u; // P0.08 <- HLK-LD2410S OT1 (TX)
    static constexpr uint32_t kUartDefaultTxPin       = 6u; // P0.06 -> HLK-LD2410S RX
    static constexpr uint32_t kUartAltRxPin           = 6u; // P0.06 (auto-fallback if RX/TX swapped)
    static constexpr uint32_t kUartAltTxPin           = 8u; // P0.08 (auto-fallback if RX/TX swapped)

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

    /**
     * @brief Query whether the hardware OT2 pin (P0.17) has ever asserted HIGH or fired an edge ISR.
     */
    bool IsOt2SignalSeen() const { return mOt2SignalSeen; }

private:
    static void OnOt2GpioIsr(const struct device *port, struct gpio_callback *cb, uint32_t pins);
    static void OnUartIsr(const struct device *dev, void *userData);

    int ResumeUart();
    int SuspendUart();
    void ApplyUartPinMapping(bool swapPins);
    void ParseBufferedBootReports();
    bool PopRxByte(uint8_t *outByte);
    void DrainUartRx();
    void SendBytes(const uint8_t *data, size_t len);
    bool SendCommandAndWaitAck(const uint8_t *cmdBuf, size_t cmdLen, uint16_t expectedCmdWord, uint32_t timeoutMs);
    int ConfigureRadarParameters();

    const struct device    *mUartDev;
    struct gpio_dt_spec     mOt2Gpio;
    struct gpio_callback    mOt2CbData;
    Ot2EdgeCallback         mEdgeCallback;
    Ld2410sFrameParser      mParser;
    Ld2410sReport           mLastBootReport;
    struct k_sem            mRxSem;
    uint8_t                 mRxRing[kRxRingSize];
    volatile uint32_t       mRxHead;
    volatile uint32_t       mRxTail;
    volatile uint32_t       mRxBytesSeen;
    uint16_t                mLastDistanceMm;
    bool                    mHasBootReport;
    bool                    mSwapRxTxPins;
    bool                    mUartSuspended;
    bool                    mRadarConfigured;
    volatile bool           mOt2SignalSeen;
};
