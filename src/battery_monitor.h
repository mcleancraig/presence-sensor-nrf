/*
 * Copyright (c) 2026 Craig McLean
 * Battery Voltage Monitor & Continuous External VCC Rail Protection
 */

#pragma once

#include <zephyr/kernel.h>
#include <zephyr/drivers/adc.h>
#include <zephyr/drivers/gpio.h>

enum class BatteryChargeLevel : uint8_t {
    OK = 0,
    Warning = 1,
    Critical = 2
};

struct BatteryStatus {
    uint16_t voltageMv;        // Battery voltage in millivolts (e.g. 3850)
    uint8_t  percentRemaining; // 0 to 100 %
    BatteryChargeLevel chargeLevel;
    bool isCutoffActive;       // True if low voltage cutoff was triggered
};

class BatteryMonitor {
public:
    static BatteryMonitor &Instance() {
        static BatteryMonitor sInstance;
        return sInstance;
    }

    // Safety Voltage Thresholds (in mV) for raw 18650 cell
    static constexpr uint16_t VOLTAGE_MAX_MV       = 4200; // 100% full
    static constexpr uint16_t VOLTAGE_NOMINAL_MV   = 3700; // ~50%
    static constexpr uint16_t VOLTAGE_WARNING_MV   = 3400; // Low battery warning threshold
    static constexpr uint16_t VOLTAGE_CRITICAL_MV  = 3050; // Critical warning
    static constexpr uint16_t VOLTAGE_CUTOFF_MV    = 3000; // Hard cutoff threshold to prevent cell damage

    // A reading at or below the cutoff is confirmed by averaging this many
    // further readings, spaced apart, and requiring consecutive low status
    // checks so a radio-TX or radar startup inrush dip cannot power the device off.
    static constexpr int CUTOFF_CONFIRM_SAMPLES      = 8;
    static constexpr int CUTOFF_CONFIRM_SPACING_MS   = 250;
    static constexpr int CUTOFF_CONSECUTIVE_READINGS = 2;

    /**
     * @brief Initialize SAADC channel and Pin 13 (P0.13) power cutoff GPIO.
     *        Configures P0.13 LOW initially so unloaded battery voltage and BLE
     *        advertising can initialize before enabling the HLK-LD2410S rail.
     */
    int Init();

    /**
     * @brief Control external VCC rail switch (Pin 13 / P0.13).
     * @param enable true to enable external rail, false to cut off.
     */
    int SetExternalPowerEnabled(bool enable);

    /**
     * @brief Alias for SetExternalPowerEnabled() to control HLK-LD2410S 3.3V power.
     */
    int SetSensorPower(bool enable) { return SetExternalPowerEnabled(enable); }

    /**
     * @brief Query whether external VCC rail switch is currently enabled.
     */
    bool IsExternalPowerEnabled() const { return mExternalPowerEnabled; }

    /**
     * @brief Query whether USB VBUS (5V) is currently connected.
     */
    bool IsUsbVbusConnected() const;

    /**
     * @brief Read the battery voltage, compute percentage and check cutoff protection.
     * @param outStatus Pointer to BatteryStatus structure to populate.
     * @return 0 on success, negative errno on failure.
     */
    int ReadBatteryStatus(BatteryStatus *outStatus);

    /**
     * @brief Cut external VCC and enter System OFF. Does not return; only a
     *        reset (RST button) or power cycle wakes the device.
     */
    [[noreturn]] void EnterSystemOff();

    /**
     * @brief Map Li-ion open-circuit voltage (mV) to 0..100%.
     */
    static uint8_t CalculatePercentage(uint16_t voltageMv);

private:
    BatteryMonitor();

    int ReadMillivolts(uint16_t *outMv);

    const struct device *mAdcDev;
    struct gpio_dt_spec mCutoffGpio;
    struct adc_channel_cfg mChannelCfg;
    int16_t mAdcBuffer;
    int mConsecutiveCutoffCount;
    bool mInitialized;
    bool mCutoffActive;
    bool mExternalPowerEnabled;
};
