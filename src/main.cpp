/*
 * Copyright (c) 2026 Craig McLean
 * Main Application Entry Point
 */

#include "app_task.h"
#include "status_led.h"
#include "version.h"
#include <zephyr/logging/log.h>

#if DT_NODE_HAS_COMPAT(DT_CHOSEN(zephyr_console), zephyr_cdc_acm_uart)
#include <zephyr/drivers/uart.h>
#endif

LOG_MODULE_REGISTER(app, LOG_LEVEL_INF);

int main()
{
    // First thing: solid 500 ms flash proves the application (not the UF2 bootloader) is running
    StatusLed::Instance().Init();

#if DT_NODE_HAS_COMPAT(DT_CHOSEN(zephyr_console), zephyr_cdc_acm_uart)
    // Debug build with USB console: wait (up to 10 s) for a terminal to open
    // the port so early boot logs are not lost
    const struct device *console = DEVICE_DT_GET(DT_CHOSEN(zephyr_console));
    for (int i = 0; i < 100; i++) {
        uint32_t dtr = 0;
        if (uart_line_ctrl_get(console, UART_LINE_CTRL_DTR, &dtr) == 0 && dtr) {
            break;
        }
        k_msleep(100);
    }
#endif

    LOG_INF("=========================================================");
    LOG_INF("  BTHome v2 BLE Presence Sensor v%s (SuperMini nRF52840)", APP_VERSION_STRING);
    LOG_INF("=========================================================");

    int ret = AppTask::Instance().Start();
    if (ret != 0) {
        LOG_ERR("AppTask start failed with error: %d", ret);
        return ret;
    }

    while (true) {
        k_sleep(K_FOREVER);
    }

    return 0;
}
