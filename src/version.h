/*
 * Copyright (c) 2026 Craig McLean
 * Firmware Version & Build Provenance
 */

#pragma once

#include <stdint.h>

#define APP_VERSION_MAJOR 1
#define APP_VERSION_MINOR 2
#define APP_VERSION_PATCH 0
#define APP_BUILD_NUMBER  11

#define APP_VERSION_STRING "1.2.0"

static constexpr uint32_t kAppSoftwareVersion =
    (static_cast<uint32_t>(APP_VERSION_MAJOR) << 16) |
    (static_cast<uint32_t>(APP_VERSION_MINOR) << 8) |
    static_cast<uint32_t>(APP_VERSION_PATCH);
