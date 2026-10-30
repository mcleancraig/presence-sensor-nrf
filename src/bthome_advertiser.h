/*
 * Copyright (c) 2026 Craig McLean
 * Zephyr BLE BTHome v2 Broadcaster (Burst on State Change + Low-Power Heartbeat)
 */

#pragma once

#include "bthome_proto.h"
#include <zephyr/kernel.h>

class BthomeAdvertiser {
public:
    // Burst advertisement parameters on occupancy/motion state transitions:
    // 25-35 ms interval (40-56 * 0.625 ms) for 3000 ms (~100 packets across all 3 BLE adv channels)
    // guaranteeing 100% reception across ESPHome Wi-Fi/BLE shared-antenna proxy scan windows.
    static constexpr uint16_t kBurstAdvIntervalMinUnits  = 40;   // 25 ms
    static constexpr uint16_t kBurstAdvIntervalMaxUnits  = 56;   // 35 ms
    static constexpr int32_t  kBurstDurationMs           = 3000; // 3.0 s

    // Active post-burst BLE advertising interval while occupied/motion is active (~500 ms):
    static constexpr uint16_t kActiveAdvIntervalMinUnits = 768;  // 480 ms
    static constexpr uint16_t kActiveAdvIntervalMaxUnits = 832;  // 520 ms

    // Idle background BLE advertising interval when unoccupied (~1500 ms):
    static constexpr uint16_t kIdleAdvIntervalMinUnits   = 2400; // 1500 ms
    static constexpr uint16_t kIdleAdvIntervalMaxUnits   = 2560; // 1600 ms

    BthomeAdvertiser();

    /**
     * @brief Initialize Bluetooth subsystem, derive static random identity address
     *        and "Presence-XXXX" scan response name from FICR, and start advertising.
     */
    int Init();

    /**
     * @brief Publish a new sensor measurement.
     * @param m Latest battery + radar measurement (packetId is auto-incremented).
     * @param burst true to transmit a 1.0 s high-density burst (25-35 ms interval)
     *              before transitioning back to 2.5 s low-power idle advertising.
     */
    int Publish(const BthomeMeasurement &m, bool burst);

    /**
     * @brief Called from the application event loop when the burst timer expires
     *        to transition from 25-35 ms burst interval back to 2.5 s idle interval.
     */
    void TransitionToIdleInterval();

    const char *GetDeviceName() const { return mDeviceName; }
    uint8_t GetLastPacketId() const { return mPacketId; }

private:
    static void OnBurstTimerExpired(struct k_timer *timer);
    int ApplyAdvertisingParams(uint16_t intervalMinUnits, uint16_t intervalMaxUnits);

    uint8_t        mSvcData[BthomeProto::kServiceDataPayloadSize];
    char           mDeviceName[BthomeProto::kDeviceNameLen + 1];
    struct k_timer mBurstTimer;
    uint8_t        mIdentityId;
    uint8_t        mPacketId;
    bool           mAdvertising;
    bool           mInBurstMode;
    bool           mIsOccupiedOrActive;
};
