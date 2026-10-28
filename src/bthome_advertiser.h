/*
 * Copyright (c) 2026 Craig McLean
 * Zephyr BLE BTHome v2 Broadcaster (Burst on State Change + Low-Power Heartbeat)
 */

#pragma once

#include "bthome_proto.h"
#include <zephyr/kernel.h>

class BthomeAdvertiser {
public:
    // Burst advertisement parameters on occupancy state transitions:
    // 100 ms interval (160 * 0.625 ms) for 1500 ms (~15 packets across all 3 BLE adv channels)
    static constexpr uint16_t kBurstAdvIntervalMinUnits = 160;  // 100 ms
    static constexpr uint16_t kBurstAdvIntervalMaxUnits = 192;  // 120 ms
    static constexpr int32_t  kBurstDurationMs          = 1500;

    // Idle background BLE advertising interval between state changes:
    // 2500 ms (4000 * 0.625 ms) keeps average BLE controller draw under ~6 uA
    // while allowing instant Home Assistant passive discovery at any time.
    static constexpr uint16_t kIdleAdvIntervalMinUnits  = 4000; // 2500 ms
    static constexpr uint16_t kIdleAdvIntervalMaxUnits  = 4160; // 2600 ms

    BthomeAdvertiser();

    /**
     * @brief Initialize Bluetooth subsystem, derive static random identity address
     *        and "Presence-XXXX" scan response name from FICR, and start advertising.
     */
    int Init();

    /**
     * @brief Publish a new sensor measurement.
     * @param m Latest battery + radar measurement (packetId is auto-incremented).
     * @param burst true to transmit a 1.5 s fast burst (100 ms interval) before
     *              transitioning back to low-power slow advertising.
     */
    int Publish(const BthomeMeasurement &m, bool burst);

    /**
     * @brief Called from the application event loop when the burst timer expires
     *        to transition from 100 ms burst interval back to 2.5 s idle interval.
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
};
