#!/usr/bin/env bash
# Compile and execute host unit tests for HLK-LD2410S UART codec and BTHome v2 BLE encoder.
set -euo pipefail

cd "$(dirname "$0")/.."

CXX="${CXX:-c++}"
OUT_BIN="tests/test_protocols"

"$CXX" -std=c++20 -Wall -Wextra -Werror -O2 \
    src/ld2410s_proto.cpp \
    src/bthome_proto.cpp \
    src/ha_mqtt_proto.cpp \
    src/ota_updater.cpp \
    tests/test_protocols.cpp \
    -o "$OUT_BIN"

"./$OUT_BIN"
rm -f "$OUT_BIN"
