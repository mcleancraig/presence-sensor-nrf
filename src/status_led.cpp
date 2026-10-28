/*
 * Copyright (c) 2026 Craig McLean
 * Status LED (P0.15): boot flash and fault/activity blink
 */

#include "status_led.h"
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(status_led, LOG_LEVEL_INF);

static constexpr int kBootFlashMs = 500;

static const struct gpio_dt_spec sLed = GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios);

void StatusLed::Init()
{
    if (!gpio_is_ready_dt(&sLed) || gpio_pin_configure_dt(&sLed, GPIO_OUTPUT_INACTIVE) != 0) {
        LOG_ERR("Status LED not available");
        return;
    }

    mReady = true;

    // Solid 500 ms flash: distinguishes "application running" from the bootloader's slow fade
    gpio_pin_set_dt(&sLed, 1);
    k_msleep(kBootFlashMs);
    gpio_pin_set_dt(&sLed, 0);
}

void StatusLed::BlinkError(int count)
{
    if (!mReady) {
        return;
    }
    for (int i = 0; i < count; i++) {
        gpio_pin_set_dt(&sLed, 1);
        k_msleep(100);
        gpio_pin_set_dt(&sLed, 0);
        k_msleep(100);
    }
    k_msleep(500);
}

void StatusLed::Pulse(int ms)
{
    if (!mReady) {
        return;
    }
    gpio_pin_set_dt(&sLed, 1);
    k_msleep(ms);
    gpio_pin_set_dt(&sLed, 0);
}

void StatusLed::Set(bool on)
{
    if (!mReady) {
        return;
    }
    gpio_pin_set_dt(&sLed, on ? 1 : 0);
}
