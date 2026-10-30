/*
 * Copyright (c) 2026 Craig McLean
 * Application Task & Low-Power Event Loop (HLK-LD2410S + BTHome v2 BLE)
 */

#include "app_task.h"
#include "status_led.h"
#include "version.h"
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(app_task, LOG_LEVEL_INF);

namespace {

static constexpr uint32_t kEvtOt2Edge              = BIT(0);
static constexpr uint32_t kEvtOccupiedPoll         = BIT(1);
static constexpr uint32_t kEvtHeartbeat            = BIT(2);
static constexpr uint32_t kEvtBatterySample        = BIT(3);
static constexpr uint32_t kEvtBurstDone            = BIT(4);
static constexpr uint16_t kDistanceBurstThresholdMm = 100u;

} // namespace

AppTask::AppTask()
    : mBatteryStatus{BatteryMonitor::VOLTAGE_NOMINAL_MV, 50, BatteryChargeLevel::OK, false},
      mLastRadarReport{Ld2410sTargetState::Unoccupied, false, false, 0, 0, true},
      mPendingEvents(ATOMIC_INIT(0)),
      mLastPublishedDistanceMm(0u),
      mLastOccupied(false),
      mLastMotion(false)
{
}

void AppTask::OnOt2EdgeStatic()
{
    Instance().NotifyOt2Edge();
}

void AppTask::OnHeartbeatTimer(struct k_timer *timer)
{
    ARG_UNUSED(timer);
    Instance().PostEvent(kEvtHeartbeat);
}

void AppTask::OnOccupiedPollTimer(struct k_timer *timer)
{
    ARG_UNUSED(timer);
    Instance().PostEvent(kEvtOccupiedPoll);
}

void AppTask::OnBatteryTimer(struct k_timer *timer)
{
    ARG_UNUSED(timer);
    Instance().PostEvent(kEvtBatterySample);
}

void AppTask::PostEvent(uint32_t eventMask)
{
    atomic_or(&mPendingEvents, static_cast<atomic_val_t>(eventMask));
    k_sem_give(&mEventSem);
}

void AppTask::NotifyOt2Edge()
{
    PostEvent(kEvtOt2Edge);
}

void AppTask::NotifyBurstComplete()
{
    PostEvent(kEvtBurstDone);
}

void AppTask::SampleBattery()
{
    BatteryStatus status{};
    if (BatteryMonitor::Instance().ReadBatteryStatus(&status) == 0) {
        mBatteryStatus = status;
    }
}

void AppTask::PublishCurrentState(bool burst)
{
    const BthomeMeasurement m = {
        .packetId   = 0, // Auto-incremented inside BthomeAdvertiser::Publish
        .batteryPct = mBatteryStatus.percentRemaining,
        .voltageMv  = mBatteryStatus.voltageMv,
        .motion     = mLastRadarReport.motion,
        .occupancy  = mLastRadarReport.occupied,
        .distanceMm = mLastRadarReport.distanceMm,
    };

    mAdvertiser.Publish(m, burst);
}

void AppTask::HandleOt2AndDistanceUpdate(bool forceBurst, bool forcePublish)
{
    // Fast-path for 5-wire setups (OT2 -> P0.17): on a rising OT2 hardware interrupt
    // when transitioning from unoccupied -> occupied, broadcast occupancy=true over BLE
    // immediately (< 5 ms) BEFORE waking UART0 to read exact target distance!
    if (forceBurst && !mLastOccupied && mRadar.ReadPinOccupancy()) {
        mLastOccupied              = true;
        mLastMotion                = true;
        mLastRadarReport.occupied  = true;
        mLastRadarReport.motion    = true;
        PublishCurrentState(true);
    }

    Ld2410sReport report{};
    mRadar.SampleTargetReport(&report);
    mLastRadarReport = report;

    const bool stateChanged = (report.occupied != mLastOccupied) ||
                              (report.motion != mLastMotion);
    const bool occupancyEdge = (report.occupied != mLastOccupied);
    const bool distanceChanged = (report.distanceMm != mLastPublishedDistanceMm);
    const uint16_t distDeltaMm = (report.distanceMm > mLastPublishedDistanceMm)
                                     ? (report.distanceMm - mLastPublishedDistanceMm)
                                     : (mLastPublishedDistanceMm - report.distanceMm);
    const bool significantDistChange = report.occupied &&
                                       (distDeltaMm >= kDistanceBurstThresholdMm);

    mLastOccupied = report.occupied;
    mLastMotion   = report.motion;

    const bool shouldBurst = forceBurst || occupancyEdge || stateChanged || significantDistChange;
    if (shouldBurst || forcePublish || distanceChanged) {
        mLastPublishedDistanceMm = report.distanceMm;
        PublishCurrentState(shouldBurst);
    }
}

int AppTask::Start()
{
    LOG_INF("Starting BTHome v2 mmWave Presence Sensor v%s (build %d)",
            APP_VERSION_STRING, APP_BUILD_NUMBER);

    k_sem_init(&mEventSem, 0, K_SEM_MAX_LIMIT);
    k_timer_init(&mHeartbeatTimer, OnHeartbeatTimer, nullptr);
    k_timer_init(&mOccupiedPollTimer, OnOccupiedPollTimer, nullptr);
    k_timer_init(&mBatteryTimer, OnBatteryTimer, nullptr);

    // 1. Initialize Battery Monitor with P0.13 LOW (radar unpowered) and configure SAADC VDDH/5
    int ret = BatteryMonitor::Instance().Init();
    if (ret != 0) {
        LOG_ERR("BatteryMonitor::Init failed (err: %d)", ret);
        StatusLed::Instance().BlinkError(2);
    }

    // Read initial unloaded battery/VBUS voltage before enabling the radar 3.3 V rail
    SampleBattery();

    // 2. Initialize BTHome v2 BLE Advertiser and broadcast initial state immediately
    // before enabling the HLK-LD2410S 3.3 V load (guarantees BLE discovery even on USB-only power)
    ret = mAdvertiser.Init();
    if (ret != 0) {
        LOG_ERR("BthomeAdvertiser::Init failed (err: %d)", ret);
        StatusLed::Instance().BlinkError(4);
        return ret;
    }
    PublishCurrentState(true);

    // 3. Enable P0.13 3.3 V VCC rail and initialize HLK-LD2410S (P0.17 OT2 + uart0 config + auto pin-swap probe)
    (void)BatteryMonitor::Instance().SetSensorPower(true);
    ret = mRadar.Init(OnOt2EdgeStatic);
    if (ret != 0) {
        LOG_ERR("SensorLd2410s::Init failed (err: %d)", ret);
        StatusLed::Instance().BlinkError(3);
    }

    // Ensure P0.15 status LED is strictly OFF before entering the low-power event loop
    StatusLed::Instance().Set(false);

    // 4. Perform initial radar sample and broadcast updated burst advertisement
    HandleOt2AndDistanceUpdate(true, true);

    // 5. Start periodic low-power timers (400 ms sub-second radar UART poll + heartbeat + battery)
    k_timer_start(&mOccupiedPollTimer,
                  K_MSEC(CONFIG_APP_RADAR_POLL_INTERVAL_MS),
                  K_MSEC(CONFIG_APP_RADAR_POLL_INTERVAL_MS));
    k_timer_start(&mHeartbeatTimer,
                  K_SECONDS(CONFIG_APP_HEARTBEAT_INTERVAL_SEC),
                  K_SECONDS(CONFIG_APP_HEARTBEAT_INTERVAL_SEC));
    k_timer_start(&mBatteryTimer,
                  K_SECONDS(CONFIG_APP_BATTERY_SAMPLE_INTERVAL_SEC),
                  K_SECONDS(CONFIG_APP_BATTERY_SAMPLE_INTERVAL_SEC));

    LOG_INF("Entering System ON low-power event loop (poll=%dms, heartbeat=%ds, battery=%ds)",
            CONFIG_APP_RADAR_POLL_INTERVAL_MS,
            CONFIG_APP_HEARTBEAT_INTERVAL_SEC,
            CONFIG_APP_BATTERY_SAMPLE_INTERVAL_SEC);

    while (true) {
        k_sem_take(&mEventSem, K_FOREVER);

        const uint32_t events = static_cast<uint32_t>(atomic_clear(&mPendingEvents));

        if (events & kEvtBurstDone) {
            mAdvertiser.TransitionToIdleInterval();
        }

        if (events & kEvtBatterySample) {
            SampleBattery();
        }

        const bool forceBurst   = (events & kEvtOt2Edge) != 0u;
        const bool forcePublish = (events & kEvtHeartbeat) != 0u;

        if (events & (kEvtOt2Edge | kEvtOccupiedPoll)) {
            HandleOt2AndDistanceUpdate(forceBurst, forcePublish);
        } else if (forcePublish) {
            PublishCurrentState(false);
        }
    }

    return 0;
}
