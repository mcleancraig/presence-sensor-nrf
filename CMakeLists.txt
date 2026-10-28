# CMakeLists.txt for BTHome v2 BLE mmWave Presence Sensor (HLK-LD2410S)
cmake_minimum_required(VERSION 3.20.0)

list(APPEND BOARD_ROOT ${CMAKE_CURRENT_SOURCE_DIR})

find_package(Zephyr HINTS $ENV{ZEPHYR_BASE})
project(presence-sensor-nrf)

target_include_directories(app PRIVATE
    src
)

target_sources(app PRIVATE
    src/main.cpp
    src/app_task.cpp
    src/battery_monitor.cpp
    src/ld2410s_proto.cpp
    src/sensor_ld2410s.cpp
    src/bthome_proto.cpp
    src/bthome_advertiser.cpp
    src/status_led.cpp
)

target_sources_ifdef(CONFIG_APP_DEBUG_KEEP_ALIVE app PRIVATE src/debug_fatal.c)
