# Bring-up Notes: SuperMini nRF52840 + HLK-LD2410S BTHome v2 Sensor

This document records the hardware, bootloader, power-management, and protocol details required to run the Hi-Link HLK-LD2410S 24 GHz mmWave radar with BTHome v2 BLE on SuperMini nRF52840 (`nice!nano v2` clone) boards. Read it before modifying the flash layout, `uart0` power management, radar configuration commands, or battery sensing.

---

## 1. SuperMini nRF52840 Bootloader & Flash Layout (`0x1000`)

### Why `code_partition` starts at `0x1000` (not `0x26000`)
- The SuperMini nRF52840 ships with the Adafruit nRF52 UF2 bootloader (`Board-ID: nRF52840-nicenano`).
- When no Nordic S140 SoftDevice is installed (`SoftDevice: not found` in `/Volumes/NICENANO/INFO_UF2.TXT`), the Adafruit bootloader jumps directly to `MBR_SIZE` = **`0x1000`**, not `0x26000`.
- Upstream Zephyr `nice_nano` / `promicro_nrf52840/uf2` board definitions link the application at `0x26000` assuming S140 v6 is present. On a `nosd` board, an image linked at `0x26000` never boots (the bootloader jumps into erased flash at `0x1000` and falls back to DFU mode with a pulsing red LED).
- Because Zephyr's Bluetooth stack (`CONFIG_BT_LL_SOFTDEVICE=y`) links its own BLE controller inside the application binary, our `0x1000` UF2 image overwrites any pre-installed S140 SoftDevice on first flash; the bootloader then detects no SoftDevice and boots `0x1000` cleanly.
- **New boards with Bootloader `0.6.0`**: Check `/Volumes/NICENANO/INFO_UF2.TXT`. If it reports `0.6.0`, flash `update-nice_nano_bootloader-0.6.1_nosd.uf2` first, let the board reboot, double-click `RST` again, and then copy `build/zephyr/zephyr.uf2` using `cp -X`.

### macOS UF2 Copy Quirk
- Always flash from Terminal using `cp -X build/zephyr/zephyr.uf2 /Volumes/NICENANO/`.
- Because the bootloader reboots immediately upon receiving the final UF2 block, macOS reports `fcopyfile failed: Input/output error` (or a Finder disconnect alert) as the volume unmounts. This is expected behavior.

---

## 2. HLK-LD2410S Power & UART Sleep Architecture

### Why `P0.13` (`VCC`) Must Stay HIGH Continuously
- The HLK-LD2410S is **not** a one-shot sensor that can be cold-booted in a few milliseconds:
  1. Its onboard MCU and 24 GHz FMCW transceiver require `~1–2 s` after power-up to initialize and load their adaptive room noise floor.
  2. In **Low-Speed Mode** (`1 Hz` status/distance reporting), the HLK-LD2410S autonomously duty-cycles its own 24 GHz RF front-end down to **`58 – 100 µA` average current**.
  3. The HLK-LD2410S `VCC` pin requires **`3.0 V – 3.6 V`**. Connecting it directly to a raw Li-ion cell (`4.2 V` fully charged) exceeds its `3.6 V` rating.
- Therefore, the HLK-LD2410S `VCC` pin is wired to the SuperMini's **switched `VCC` header pin** (regulated `3.3 V` output controlled by `P0.13`, `power-cutoff-gpios`).
- `BatteryMonitor::Init()` drives `P0.13` **HIGH immediately at boot** and keeps it HIGH throughout normal operation. `P0.13` is driven LOW only when `BatteryMonitor::ReadBatteryStatus()` confirms `<= 3.0 V` across 8 samples (2 seconds) right before calling `sys_poweroff()`.

### Why `uart0` (`UARTE0`) Must Be Suspended Between Reads
- An active nRF52840 `UARTE0` receiver keeps the 64 MHz HFCLK and EasyDMA bus active, drawing **`~500 – 1,000 µA`** continuously — up to 10× the current of the radar itself!
- Meanwhile, the HLK-LD2410S provides a dedicated digital presence output on **`OT2` (Pin 5)** (`HIGH` = occupied, `LOW` = unoccupied).
- Our architecture combines `OT2` GPIO interrupts on `P0.17` (`017` / `D2`) with Zephyr Device Runtime Power Management (`CONFIG_PM_DEVICE=y`, `CONFIG_PM_DEVICE_RUNTIME=y`) on `uart0` (`P0.08` / `008` / `D0` RX, `P0.06` / `006` / `D1` TX):
  1. **At boot**: `SensorLd2410s::Init()` wakes `uart0`, sends the 3 m³ bathroom configuration command sequence (`0x00FF` -> `0x0070` with `CONFIG_APP_RADAR_MAX_GATE=3` / `2.10 m`, `CONFIG_APP_RADAR_MIN_GATE=0`, `CONFIG_APP_RADAR_HOLD_S=30` -> `0x007A` Minimal 5-Byte output -> `0x00FE`), and immediately suspends `uart0` via `pm_device_action_run(mUartDev, PM_DEVICE_ACTION_SUSPEND)`.
  2. **During idle sleep**: `uart0` RX/TX pins (`P0.08` / `P0.06`) transition to the `sleep` pinctrl state (`low-power-enable` in `boards/nicekeyboards/nice_nano/nice_nano-pinctrl.dtsi`), eliminating pin leakage while the HLK-LD2410S sends 1 Hz frames. The nRF52840 sleeps at `< 3 µA` waiting on `P0.17` (`OT2` `GPIO_INT_EDGE_BOTH`).
  3. **On `OT2` edge or `15 s` occupied refresh (`CONFIG_APP_OCCUPIED_DISTANCE_POLL_SEC=15`)**: `ScopedUartWake` resumes `uart0` (`PM_DEVICE_ACTION_RESUME`), waits up to `1150 ms` (`SensorLd2410s::kDefaultSampleTimeoutMs`, spanning a full `1.0 Hz` report period + `150 ms` margin) to parse the very first valid 5-byte frame from the radar stream (`distanceCm` -> `distanceMm` and motion vs. stationary sub-state), and immediately re-suspends `uart0` (`PM_DEVICE_ACTION_SUSPEND`) on scope exit.

### Sliding-Window Parser & Delimiter Collisions (`110 cm` / `98 cm`)
- In the HLK-LD2410S Minimal 5-Byte output format (`6E [state] [dist_lo] [dist_hi] 62`), the header byte is `0x6E` (`110` decimal) and the footer byte is `0x62` (`98` decimal).
- In a bathroom, a person standing at **`110 cm`** (`0x006E`) or **`98 cm`** (`0x0062`) produces distance payload bytes identical to the frame header or footer!
- A naive state machine that resets on any `0x6E` byte or terminates on any `0x62` byte will corrupt frames at `98 cm` and `110 cm`.
- `Ld2410sFrameParser` uses a fixed-offset sliding window in `mBuf` (`mBuf[0] == 0x6E && mBuf[4] == 0x62 && mBuf[1] <= 0x03`) and shifts by 1 byte (`DiscardPrefix(1)`) on mismatch so payload bytes containing `0x6E` or `0x62` never cause false frame synchronization.

---

## 3. Battery Sensing, HLK-LD2410S Mechanical Footprint & Hardware Notes

- **HLK-LD2410S Physical Footprint (`20.0 × 20.0 × 1.2 mm`) & `J2` Header (`2.54 mm` Pitch)**:
  - The Hi-Link HLK-LD2410S is a **`20.0 × 20.0 × 1.2 mm` square PCB** (`±10%` thickness tolerance) with **`R = 2.0 mm` rounded corners** and zero mounting screw holes.
  - Its 5-pin `J2` header (`Pin 1: 3V3`, `Pin 2: GND`, `Pin 3: OT1`, `Pin 4: RX`, `Pin 5: OT2`) uses a standard **`2.54 mm` (`0.100"`) pitch** (`10.16 mm` center-to-center span), with hole centers **`1.47 mm` inward from the `+X` PCB edge** and asymmetrically positioned from top (`+Y`) to bottom (`-Y`): `Pin 5 (OT2)` at `1.62 mm`, `Pin 4 (RX)` at `4.16 mm`, `Pin 3 (OT1)` at `6.70 mm`, `Pin 2 (GND)` at `9.24 mm`, and `Pin 1 (3V3)` at `11.78 mm` from the top `+Y` edge (`8.22 mm` from the bottom `-Y` edge).
  - **Enclosure Orientation**:
    - **Antenna side (`TOP层`) faces UP (`+Z`)**: The two diagonally opposite 24 GHz patch antennas and the `ICL1112` transceiver IC face upward (`+Z`) into the lid's **`22 × 22 × 1.2 mm`** blind RF radome window.
    - **Component/header side (`Bottom层`) faces DOWN (`-Z`) with `J2` on `+X`**: The `PY32F030` MCU, `YXC` crystal, and `-Z` 5-pin `J2` header face downward (`-Z`) with **`19.5 mm`** of under-board vertical clearance, and the `J2` header edge faces **`+X` directly toward the SuperMini nRF52840** for short, unpinched wire routing.
  - **Optional `10–47 µF` Decoupling Capacitor**: Because `Pin 1 (3V3)` and `Pin 2 (GND)` on `J2` are immediately adjacent (`2.54 mm` pitch), an optional `10–47 µF` decoupling capacitor can be soldered directly across Pins 1 and 2 on the `-Z` underside to smooth 24 GHz chirp current spikes.
- **SAADC `VDDH/5`**: On the SuperMini nRF52840, the external voltage divider is misrouted to `P0.24` (a digital-only pin), so battery voltage is measured internally via `NRF_SAADC_VDDHDIV5` (`ADC_GAIN_1_2` = `1/2` gain, `0.6 V` internal reference = `1.2 V` full-scale = `6.0 V` at `VDDH`, 12-bit resolution, 16× hardware oversampling).
- **USB Power Reading**: While USB-C is plugged in, `VDDH` reads `~4.8 V` (`100 %`). True cell voltage is measured only when running from the battery on `B+`/`B-`.
- **No Reverse-Polarity Protection**: The SuperMini `B+`/`B-` pads have no reverse-polarity protection diode. Always verify battery polarity with a multimeter before inserting into the enclosure contacts.

---

## 4. BTHome v2 & Home Assistant Discovery

- **Ascending Object IDs**: BTHome v2 parsers require Object IDs inside the `0xFCD2` Service Data payload to appear in ascending numerical order: `0x00` (Packet ID), `0x01` (Battery %), `0x0C` (Voltage V), `0x21` (Motion), `0x2D` (Occupancy), `0x40` (Distance mm).
- **Scannable Legacy Advertising (`<= 31 B`)**: Putting the Complete Local Name (`Presence-XXXX`, 13 bytes) inside the primary Advertising Data alongside Flags (3 B) and BTHome Service Data (19 B) would total 37 bytes and fail `bt_le_adv_start()` with `-EINVAL`. Keep Flags + Service Data (`22 B`) in the primary Advertising Data (`ad[]`) and place `BT_DATA_NAME_COMPLETE` (`15 B`) in the Scan Response (`sd[]`) with `BT_LE_ADV_OPT_SCANNABLE`.
- **Unique Identity per Board**: `BthomeAdvertiser::Init()` reads the hardware device ID via `hwinfo_get_device_id()`, derives a deterministic Static Random BLE MAC address, and formats the `Presence-XXXX` suffix using the folded 16-bit FNV-1a hash in `BthomeProto::DeriveShortIdFromDeviceId()`, ensuring multiple bathroom/room sensors never collide in Home Assistant.

---

## 5. Debugging Over USB CDC ACM

- Build with `-DEXTRA_CONF_FILE=debug.conf -DEXTRA_DTC_OVERLAY_FILE=debug.overlay` (or `scripts/fetch-firmware.sh --debug`).
- In the debug build, console logs are routed over **USB CDC ACM** (`/dev/cu.usbmodem*`) while hardware `uart0` remains dedicated to the HLK-LD2410S radar on `P0.08` (`008` / `D0` RX) and `P0.06` (`006` / `D1` TX).
- `main()` waits up to 10 seconds for a terminal (`screen /dev/cu.usbmodem* 115200`) to assert DTR before starting radar configuration so early boot logs are captured.
- `CONFIG_APP_DEBUG_KEEP_ALIVE=y` (`src/debug_fatal.c`) keeps USB CDC ACM alive if an assertion or fatal fault occurs on an application thread.
