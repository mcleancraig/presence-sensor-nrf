/*
 * Copyright (c) 2026 Craig McLean
 * Application Task & Low-Power Event Loop (HLK-LD2410S + BTHome v2 BLE)
 */

#pragma once

#include <zephyr/kernel.h>
#include <zephyr/sys/atomic.h>
#include "battery_monitor.h"
#include "sensor_ld2410s.h"
#include "bthome_advertiser.h"

class AppTask {
public:
    static AppTask &Instance() {
        static AppTask sInstance;
        return sInstance;
    }

    /**
     * @brief Initialize peripherals, BLE BTHome broadcaster, and run the low-power event loop.
     */
    int Start();

    /**
     * @brief Signal from ISR or timer context that an OT2 GPIO edge occurred.
     */
    void NotifyOt2Edge();

    /**
     * @brief Signal from timer context that the 1.0 s BLE burst window completed.
     */
    void NotifyBurstComplete();

private:
    AppTask();

    static void OnOt2EdgeStatic();
    static void OnHeartbeatTimer(struct k_timer *timer);
    static void OnOccupiedPollTimer(struct k_timer *timer);
    static void OnBatteryTimer(struct k_timer *timer);

    void PostEvent(uint32_t eventMask);
    void HandleOt2AndDistanceUpdate(bool forceBurst, bool forcePublish = false);
    void SampleBattery();
    void PublishCurrentState(bool burst);

    SensorLd2410s        mRadar;
    BthomeAdvertiser     mAdvertiser;
    BatteryStatus        mBatteryStatus;
    Ld2410sReport        mLastRadarReport;
    Ld2410sMotionTracker mMotionTracker;
    struct k_sem         mEventSem;
    atomic_t           mPendingEvents;
    struct k_timer     mHeartbeatTimer;
    struct k_timer     mOccupiedPollTimer;
    struct k_timer     mBatteryTimer;
    int64_t            mLastStateChangeMs;
    int64_t            mLastPublishMs;
    uint16_t           mLastPublishedDistanceMm;
    bool               mLastOccupied;
    bool               mLastMotion;
};
