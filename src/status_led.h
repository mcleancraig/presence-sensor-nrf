/*
 * Copyright (c) 2026 Craig McLean
 * Status LED (P0.15): boot flash and fault/activity blink
 */

#pragma once

#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>

class StatusLed {
public:
    static StatusLed &Instance() {
        static StatusLed sInstance;
        return sInstance;
    }

    /** Configure the LED and show a solid 500 ms flash to signal the application booted. */
    void Init();

    /** Blocking burst of fast blinks, used at boot to report a fault without a serial port. */
    void BlinkError(int count);

    /** Short blocking pulse, useful for activity heartbeats. */
    void Pulse(int ms);

    /** Explicitly drive the status LED on or off. */
    void Set(bool on);

private:
    StatusLed() = default;

    bool mReady = false;
};
