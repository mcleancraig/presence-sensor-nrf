/*
 * Copyright (c) 2026 Craig McLean
 * Zephyr BLE BTHome v2 Broadcaster (Burst on State Change + Low-Power Heartbeat)
 */

#include "bthome_advertiser.h"
#include "app_task.h"
#include <string.h>
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/addr.h>
#include <zephyr/drivers/hwinfo.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(bthome_adv, LOG_LEVEL_INF);

static constexpr uint8_t kAdvFlags = BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR;

BthomeAdvertiser::BthomeAdvertiser()
    : mIdentityId(BT_ID_DEFAULT),
      mPacketId(0),
      mAdvertising(false),
      mInBurstMode(false)
{
    memset(mSvcData, 0, sizeof(mSvcData));
    memcpy(mDeviceName, "Presence-0000", sizeof("Presence-0000"));
}

void BthomeAdvertiser::OnBurstTimerExpired(struct k_timer *timer)
{
    ARG_UNUSED(timer);
    AppTask::Instance().NotifyBurstComplete();
}

int BthomeAdvertiser::Init()
{
    k_timer_init(&mBurstTimer, OnBurstTimerExpired, nullptr);

    // 1. Read factory-programmed 64-bit FICR device ID for unique BLE address & name
    uint8_t devId[16] = {};
    ssize_t devIdLen = hwinfo_get_device_id(devId, sizeof(devId));
    if (devIdLen <= 0) {
        LOG_WRN("hwinfo_get_device_id failed (%d); using fallback ID", static_cast<int>(devIdLen));
        devIdLen = 8;
    }

    BthomeProto::FormatDeviceName(devId, static_cast<size_t>(devIdLen), mDeviceName, sizeof(mDeviceName));

    // 2. Pre-create a deterministic static random BLE address from FICR device ID
    //    before bt_enable() (or after bt_enable() if default identity is used).
    bt_addr_le_t staticAddr{};
    staticAddr.type = BT_ADDR_LE_RANDOM;
    for (size_t i = 0; i < 6; ++i) {
        staticAddr.a.val[i] = devId[i % static_cast<size_t>(devIdLen)] ^
                              devId[(i + 2) % static_cast<size_t>(devIdLen)];
    }
    // Static random BLE address requires the two MSBs of the most-significant byte to be 11b (0xC0)
    staticAddr.a.val[5] |= 0xC0u;

    int ret = bt_enable(nullptr);
    if (ret != 0) {
        LOG_ERR("bt_enable failed (err: %d)", ret);
        return ret;
    }

    int idRet = bt_id_create(&staticAddr, nullptr);
    if (idRet >= 0) {
        mIdentityId = static_cast<uint8_t>(idRet);
    } else {
        mIdentityId = BT_ID_DEFAULT;
    }

    bt_set_name(mDeviceName);

    LOG_INF("BLE BTHome v2 initialized: name=%s, MAC=%02X:%02X:%02X:%02X:%02X:%02X (id=%u)",
            mDeviceName,
            staticAddr.a.val[5], staticAddr.a.val[4], staticAddr.a.val[3],
            staticAddr.a.val[2], staticAddr.a.val[1], staticAddr.a.val[0],
            mIdentityId);

    return 0;
}

int BthomeAdvertiser::ApplyAdvertisingParams(uint16_t intervalMinUnits, uint16_t intervalMaxUnits)
{
    const struct bt_data ad[] = {
        BT_DATA(BT_DATA_FLAGS, &kAdvFlags, sizeof(kAdvFlags)),
        BT_DATA(BT_DATA_SVC_DATA16, mSvcData, sizeof(mSvcData)),
    };

    const uint8_t nameLen = static_cast<uint8_t>(strlen(mDeviceName));
    const struct bt_data sd[] = {
        BT_DATA(BT_DATA_NAME_COMPLETE, mDeviceName, nameLen),
    };

    struct bt_le_adv_param param = BT_LE_ADV_PARAM_INIT(
        BT_LE_ADV_OPT_SCANNABLE | BT_LE_ADV_OPT_USE_IDENTITY,
        intervalMinUnits,
        intervalMaxUnits,
        nullptr);
    param.id = mIdentityId;

    if (mAdvertising) {
        bt_le_adv_stop();
        mAdvertising = false;
    }

    int ret = bt_le_adv_start(&param, ad, ARRAY_SIZE(ad), sd, ARRAY_SIZE(sd));
    if (ret != 0) {
        LOG_ERR("bt_le_adv_start failed (err: %d)", ret);
        return ret;
    }

    mAdvertising = true;
    return 0;
}

int BthomeAdvertiser::Publish(const BthomeMeasurement &m, bool burst)
{
    BthomeMeasurement encoded = m;
    encoded.packetId = ++mPacketId;

    BthomeProto::EncodeServiceData(encoded, mSvcData, sizeof(mSvcData));

    const struct bt_data ad[] = {
        BT_DATA(BT_DATA_FLAGS, &kAdvFlags, sizeof(kAdvFlags)),
        BT_DATA(BT_DATA_SVC_DATA16, mSvcData, sizeof(mSvcData)),
    };

    const uint8_t nameLen = static_cast<uint8_t>(strlen(mDeviceName));
    const struct bt_data sd[] = {
        BT_DATA(BT_DATA_NAME_COMPLETE, mDeviceName, nameLen),
    };

    if (burst) {
        mInBurstMode = true;
        int ret = ApplyAdvertisingParams(kBurstAdvIntervalMinUnits, kBurstAdvIntervalMaxUnits);
        k_timer_start(&mBurstTimer, K_MSEC(kBurstDurationMs), K_NO_WAIT);
        LOG_INF("BTHome burst [pkt=%u]: occ=%d mot=%d dist=%u mm bat=%u%% (%u mV)",
                encoded.packetId,
                encoded.occupancy ? 1 : 0,
                encoded.motion ? 1 : 0,
                encoded.distanceMm,
                encoded.batteryPct,
                encoded.voltageMv);
        return ret;
    }

    if (!mAdvertising) {
        mInBurstMode = false;
        return ApplyAdvertisingParams(kIdleAdvIntervalMinUnits, kIdleAdvIntervalMaxUnits);
    }

    int ret = bt_le_adv_update_data(ad, ARRAY_SIZE(ad), sd, ARRAY_SIZE(sd));
    if (ret != 0) {
        LOG_WRN("bt_le_adv_update_data failed (err: %d); restarting advertising", ret);
        return ApplyAdvertisingParams(
            mInBurstMode ? kBurstAdvIntervalMinUnits : kIdleAdvIntervalMinUnits,
            mInBurstMode ? kBurstAdvIntervalMaxUnits : kIdleAdvIntervalMaxUnits);
    }

    LOG_INF("BTHome update [pkt=%u]: occ=%d mot=%d dist=%u mm bat=%u%% (%u mV)",
            encoded.packetId,
            encoded.occupancy ? 1 : 0,
            encoded.motion ? 1 : 0,
            encoded.distanceMm,
            encoded.batteryPct,
            encoded.voltageMv);
    return 0;
}

void BthomeAdvertiser::TransitionToIdleInterval()
{
    if (!mInBurstMode) {
        return;
    }
    mInBurstMode = false;
    ApplyAdvertisingParams(kIdleAdvIntervalMinUnits, kIdleAdvIntervalMaxUnits);
}
