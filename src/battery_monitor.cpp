/*
 * Copyright (c) 2026 Craig McLean
 * Battery Voltage Monitor & Continuous External VCC Rail Protection
 */

#include "battery_monitor.h"
#include <string.h>
#include <hal/nrf_power.h>
#include <zephyr/logging/log.h>
#include <zephyr/logging/log_ctrl.h>
#include <zephyr/sys/poweroff.h>
#include <zephyr/dt-bindings/adc/nrf-saadc.h>
#include <zephyr/dt-bindings/adc/nrf-saadc-v3.h>

LOG_MODULE_REGISTER(battery_monitor, LOG_LEVEL_INF);

#define ZEPHYR_USER_NODE DT_PATH(zephyr_user)

static constexpr uint8_t kAdcChannelId = 0;

#if defined(CONFIG_APP_BATTERY_SENSE_VDDH)
// The cell feeds VDDH directly (B+ / BAT pad), so it is measured through the
// SAADC's internal VDDH/5 input: no external divider and no divider leakage.
// Gain 1/2 with the 0.6 V reference gives 1.2 V full scale = 6.0 V at VDDH.
static constexpr enum adc_gain kAdcGain = ADC_GAIN_1_2;
static constexpr uint8_t kAdcInput = NRF_SAADC_VDDHDIV5;
static constexpr int64_t kScaleNum = 5;
static constexpr int64_t kScaleDen = 1;
#else
// External divider: Vbat = Vpin * (Rtop + Rbottom) / Rbottom.
// Gain 1/6 with the 0.6 V reference gives 3.6 V full scale at the pin.
static constexpr enum adc_gain kAdcGain = ADC_GAIN_1_6;
static constexpr uint8_t kAdcInput = NRF_SAADC_AIN0 + CONFIG_APP_BATTERY_DIVIDER_AIN;
static constexpr int64_t kScaleNum =
    static_cast<int64_t>(CONFIG_APP_BATTERY_DIVIDER_R_TOP_OHMS) + CONFIG_APP_BATTERY_DIVIDER_R_BOTTOM_OHMS;
static constexpr int64_t kScaleDen = CONFIG_APP_BATTERY_DIVIDER_R_BOTTOM_OHMS;
#endif

BatteryMonitor::BatteryMonitor()
    : mAdcDev(DEVICE_DT_GET_OR_NULL(DT_NODELABEL(adc))),
      mCutoffGpio(GPIO_DT_SPEC_GET_OR(ZEPHYR_USER_NODE, power_cutoff_gpios, {0})),
      mAdcBuffer(0),
      mConsecutiveCutoffCount(0),
      mInitialized(false),
      mCutoffActive(false),
      mExternalPowerEnabled(false)
{
    memset(&mChannelCfg, 0, sizeof(mChannelCfg));
}

int BatteryMonitor::Init()
{
    // Step 1: Initialize Pin 13 (P0.13) Power Cutoff GPIO as INACTIVE (LOW) initially.
    // This allows the unloaded VDDH voltage to be measured and BLE advertising to start
    // before enabling the HLK-LD2410S ~70 mA cold-boot inrush via SetSensorPower(true).
    if (mCutoffGpio.port != nullptr && device_is_ready(mCutoffGpio.port)) {
        int ret = gpio_pin_configure_dt(&mCutoffGpio, GPIO_OUTPUT_INACTIVE);
        if (ret != 0) {
            LOG_ERR("Failed to configure Pin 13 power cutoff GPIO (err: %d)", ret);
            return ret;
        }
        mExternalPowerEnabled = false;
        LOG_INF("External VCC rail (P0.13) initialized LOW prior to unloaded SAADC sample");
    } else {
        LOG_WRN("Pin 13 power cutoff GPIO not defined or not ready");
    }

    // Step 2: Initialize SAADC
    if (!mAdcDev || !device_is_ready(mAdcDev)) {
        LOG_ERR("SAADC device not ready");
        return -ENODEV;
    }

    mChannelCfg.gain             = kAdcGain;
    mChannelCfg.reference        = ADC_REF_INTERNAL; // 0.6V internal bandgap
    mChannelCfg.acquisition_time = ADC_ACQ_TIME(ADC_ACQ_TIME_MICROSECONDS, 40);
    mChannelCfg.channel_id       = kAdcChannelId;
    mChannelCfg.input_positive   = kAdcInput;

    int ret = adc_channel_setup(mAdcDev, &mChannelCfg);
    if (ret != 0) {
        LOG_ERR("SAADC channel setup failed (err: %d)", ret);
        return ret;
    }

    mInitialized = true;
#if defined(CONFIG_APP_BATTERY_SENSE_VDDH)
    LOG_INF("Battery monitor initialized on internal VDDH/5");
#else
    LOG_INF("Battery monitor initialized on AIN%d with external divider", CONFIG_APP_BATTERY_DIVIDER_AIN);
#endif
    return 0;
}

bool BatteryMonitor::IsUsbVbusConnected() const
{
    return nrf_power_usbregstatus_vbusdet_get(NRF_POWER);
}

int BatteryMonitor::SetExternalPowerEnabled(bool enable)
{
    if (mCutoffGpio.port == nullptr || !device_is_ready(mCutoffGpio.port)) {
        return -ENODEV;
    }

    int ret = gpio_pin_set_dt(&mCutoffGpio, enable ? 1 : 0);
    if (ret == 0) {
        mExternalPowerEnabled = enable;
        LOG_INF("External VCC rail set to: %s", enable ? "ENABLED" : "CUT OFF");
    }
    return ret;
}

uint8_t BatteryMonitor::CalculatePercentage(uint16_t voltageMv)
{
    // Li-ion open-circuit discharge curve approximation
    if (voltageMv >= 4150) return 100;
    if (voltageMv >= 4050) return 90 + (voltageMv - 4050) / 10;
    if (voltageMv >= 3950) return 80 + (voltageMv - 3950) / 10;
    if (voltageMv >= 3850) return 70 + (voltageMv - 3850) / 10;
    if (voltageMv >= 3780) return 60 + (voltageMv - 3780) * 10 / 70;
    if (voltageMv >= 3700) return 50 + (voltageMv - 3700) * 10 / 80;
    if (voltageMv >= 3630) return 40 + (voltageMv - 3630) * 10 / 70;
    if (voltageMv >= 3550) return 30 + (voltageMv - 3550) * 10 / 80;
    if (voltageMv >= 3450) return 20 + (voltageMv - 3450) * 10 / 100;
    if (voltageMv >= 3350) return 10 + (voltageMv - 3350) * 10 / 100;
    if (voltageMv >= 3200) return 5 + (voltageMv - 3200) * 5 / 150;
    if (voltageMv >= 3000) return (voltageMv - 3000) * 5 / 200;
    return 0;
}

int BatteryMonitor::ReadMillivolts(uint16_t *outMv)
{
    struct adc_sequence sequence = {
        .options      = nullptr,
        .channels     = BIT(kAdcChannelId),
        .buffer       = &mAdcBuffer,
        .buffer_size  = sizeof(mAdcBuffer),
        .resolution   = 12,
        .oversampling = 4, // 16 samples averaged in hardware
        .calibrate    = true,
    };

    int ret = adc_read(mAdcDev, &sequence);
    if (ret != 0) {
        LOG_ERR("ADC read failed (err: %d)", ret);
        return ret;
    }

    int32_t pinMv = mAdcBuffer < 0 ? 0 : mAdcBuffer;
    ret = adc_raw_to_millivolts(adc_ref_internal(mAdcDev), kAdcGain, sequence.resolution, &pinMv);
    if (ret != 0) {
        return ret;
    }

    int64_t battMv = static_cast<int64_t>(pinMv) * kScaleNum / kScaleDen;
    *outMv = static_cast<uint16_t>(MIN(battMv, UINT16_MAX));
    return 0;
}

int BatteryMonitor::ReadBatteryStatus(BatteryStatus *outStatus)
{
    if (!mInitialized || !outStatus) {
        return -EINVAL;
    }

    uint16_t battMv = 0;
    int ret = ReadMillivolts(&battMv);
    if (ret != 0) {
        return ret;
    }

    const bool vbusConnected = IsUsbVbusConnected();

    // Confirm a low reading before acting on it (only when running on battery;
    // when USB-C is connected without a battery on B+, the TP4054 BAT node can
    // droop under the HLK-LD2410S load and must not stall or trigger System OFF).
    if (battMv <= VOLTAGE_CUTOFF_MV && !vbusConnected) {
        uint32_t sum = 0;
        int count = 0;
        for (int i = 0; i < CUTOFF_CONFIRM_SAMPLES; i++) {
            k_msleep(CUTOFF_CONFIRM_SPACING_MS);
            uint16_t mv = 0;
            if (ReadMillivolts(&mv) == 0) {
                sum += mv;
                count++;
            }
        }
        if (count > 0) {
            battMv = static_cast<uint16_t>(sum / static_cast<uint32_t>(count));
        }
        LOG_WRN("Low reading confirmed as %u mV (average of %d)", battMv, count);
    }

    outStatus->voltageMv = battMv;
    outStatus->percentRemaining = CalculatePercentage(battMv);
    outStatus->isCutoffActive = mCutoffActive;

    // Determine charge level status
    if (battMv > VOLTAGE_WARNING_MV) {
        outStatus->chargeLevel = BatteryChargeLevel::OK;
    } else if (battMv > VOLTAGE_CRITICAL_MV) {
        outStatus->chargeLevel = BatteryChargeLevel::Warning;
        LOG_WRN("Battery low: %u mV (%u%%)", battMv, outStatus->percentRemaining);
    } else {
        outStatus->chargeLevel = BatteryChargeLevel::Critical;
        LOG_WRN("Battery/VDDH reading low: %u mV (%u%%, usb_vbus=%d)",
                battMv, outStatus->percentRemaining, vbusConnected ? 1 : 0);
    }

    // Check for hard over-discharge cutoff condition (<= 3000 mV) across consecutive status checks.
    // Never enter System OFF when USB VBUS is connected (e.g. benchtop USB testing without a battery).
    if (battMv <= VOLTAGE_CUTOFF_MV && !mCutoffActive && !vbusConnected) {
        mConsecutiveCutoffCount++;
        LOG_WRN("Under-voltage sample (%u mV <= %u mV), consecutive=%d/%d",
                battMv, VOLTAGE_CUTOFF_MV, mConsecutiveCutoffCount, CUTOFF_CONSECUTIVE_READINGS);
        if (mConsecutiveCutoffCount >= CUTOFF_CONSECUTIVE_READINGS) {
            LOG_ERR("CRITICAL UNDER-VOLTAGE (%u mV <= %u mV)! Activating VCC power cutoff to protect 18650 cell.",
                    battMv, VOLTAGE_CUTOFF_MV);
            mCutoffActive = true;
            EnterSystemOff();
        }
    } else {
        mConsecutiveCutoffCount = 0;
    }

    LOG_INF("Battery: %u mV, %u%% (usb_vbus=%d)",
            battMv, outStatus->percentRemaining, vbusConnected ? 1 : 0);

    return 0;
}

void BatteryMonitor::EnterSystemOff()
{
    // Disconnect external VCC rail (powers down HLK-LD2410S); GPIO state is retained in System OFF
    SetExternalPowerEnabled(false);

    LOG_ERR("Entering nRF52840 SYSTEM OFF");
    LOG_PANIC(); // Flush deferred logs synchronously

    sys_poweroff();
    CODE_UNREACHABLE;
}
