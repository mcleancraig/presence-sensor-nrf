# presence-sensor-nrf

Ultra-low-power 24 GHz mmWave Human Presence, Motion, Distance, and Battery Sensor for Home Assistant over **BTHome v2 Bluetooth Low Energy**, built on the SuperMini nRF52840 (`nice!nano v2` compatible) and the Hi-Link **HLK-LD2410S** battery-powered radar module.

> **Enclosure:** Three 3D-printable Bambu A1 enclosure models (STEP for Fusion + STL) in [`enclosure/`](enclosure/README.md) — see [Section 8](#8-3d-printable-enclosures-3-bambu-a1-models).
>
> **Bring-up notes:** see [`doc/bringup-notes.md`](doc/bringup-notes.md) for flash offset requirements (`0x1000` without SoftDevice), HLK-LD2410S continuous power vs. UART sleep architecture, BTHome v2 discovery, and debugging over USB CDC ACM.

---

## 1. Hardware Architecture

- **Microcontroller**: SuperMini nRF52840 (pinout and Adafruit UF2 bootloader compatible with `nice!nano v2`).
- **mmWave Radar**: Hi-Link **HLK-LD2410S** 24 GHz FMCW human presence & micro-motion radar (`3.0 V - 3.6 V` regulated rail, ~`58 - 100 µA` average current in low-speed 1 Hz sleep mode; **`20.0 × 20.0 × 1.2 mm` square PCB** with `R = 2.0 mm` rounded corners and a **`2.54 mm` (`0.100"`) pitch 5-pin `J2` header**).
- **Power Source**: Single Li-ion cell (`3.0 V - 4.2 V`) feeding the SuperMini `B+`/`B-` pads (`VDDH`).
- **Continuous Radar Power (`P0.13` Switched VCC)**: Unlike one-shot I2C sensors, the HLK-LD2410S executes an internal 1 Hz / 8 Hz FMCW chirp state machine and maintains adaptive environmental noise baselines. Its `3V3` input (`J2 Pin 1`) is powered from the SuperMini's switched `VCC` header pin (`P0.13` HIGH continuously during normal operation) so the onboard 3.3 V LDO regulates the raw cell voltage (`3.0 V - 4.2 V`) down to a clean `3.3 V` within the radar's `3.6 V` absolute maximum limit.
- **Interrupt-Driven Wake & UARTE0 Runtime Suspend**:
  - `P0.17` (`017` / `D2`, `OT2` GPIO interrupt, `GPIO_INT_EDGE_BOTH`) wakes the nRF52840 from `< 3 µA` System ON Idle immediately when a person enters or leaves the bathroom.
  - `uart0` (`115200` baud, 8N1 on `P0.08` / `008` / `D0` RX and `P0.06` / `006` / `D1` TX) uses interrupt-driven RX (`CONFIG_UART_INTERRUPT_DRIVEN=y`) with a lock-free ISR ring buffer and is suspended via `pm_device_action_run(uart_dev, PM_DEVICE_ACTION_SUSPEND)` whenever idle, releasing the nRF52840 64 MHz HFCLK and EasyDMA (~`500 µA` savings) and resuming only on `OT2` edges or periodic radar polls (`5 s` via `CONFIG_APP_OCCUPIED_DISTANCE_POLL_SEC`).
- **Low-Voltage Cutoff**: At `<= 3.0 V` (confirmed across 8 averaged readings over 2 s in `BatteryMonitor::ReadBatteryStatus()`), `P0.13` (`VCC`) is driven LOW to disconnect the HLK-LD2410S rail and the nRF52840 enters System OFF (`sys_poweroff()`).

### Pinout, Header Geometry & Enclosure Orientation

The HLK-LD2410S `J2` 5-pin header (`3V3`, `GND`, `OT1`, `RX`, `OT2`) uses a standard **`2.54 mm` (`0.100"`) pitch** and is asymmetrically positioned along the `+X` PCB edge (`Pin 5 OT2` round pad at the corner `1.62 mm` from the top `+Y` edge down to `Pin 1 3V3` **square pad** near the middle of the PCB at `11.78 mm` from the top `+Y` edge, with hole centers `1.47 mm` inward from the `+X` edge):

| HLK-LD2410S `J2` Pin (`2.54 mm` 5-pin) | Pad Shape & `Y_from_top` (`+Y` Edge) | SuperMini Silkscreen / Pin | nRF52840 Port.Pin | Direction | Function / Connection |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Pin 1: `3V3` (`3.0–3.6 V`)** | **Square pad**, `11.78 mm` (near middle) | `VCC` (switched) | Controlled by `P0.13` | Power Out | Continuous regulated 3.3 V supply (`P0.13` held HIGH during run, LOW on `<= 3.0 V` cutoff) |
| **Pin 2: `GND`** | Round pad, `9.24 mm` | `GND` | `GND` | Ground | Common ground with SuperMini and battery `B-` |
| **Pin 3: `OT1` (UART TX)** | Round pad, `6.70 mm` | `008` (`D0`) | `P0.08` | Radar -> MCU | `uart0` RX (`115200` baud, 8N1; `low-power-enable` in sleep) |
| **Pin 4: `RX` (UART RX)** | Round pad, `4.16 mm` | `006` (`D1`) | `P0.06` | MCU -> Radar | `uart0` TX (`115200` baud, 8N1; `low-power-enable` in sleep) |
| **Pin 5: `OT2` (Status IO)** | **Round pad**, `1.62 mm` (at corner) | `017` (`D2`) | `P0.17` | Radar -> MCU | Digital presence output (`HIGH` = occupied, `LOW` = clear; `GPIO_INT_EDGE_BOTH` wake) |
| **Battery `+` / `-`** | — | `B+` / `B-` | `VDDH` / `GND` | Power In | Raw Li-ion cell (`3.0 V - 4.2 V`), measured internally via `NRF_SAADC_VDDHDIV5` (`1/2` gain) |
| **Status LED (Red)** | — | On-board Red LED | `P0.15` | Internal | `500 ms` boot flash; strictly OFF (`0 V`) thereafter |
| **Charger LED (Blue)** | — | On-board Blue LED | `LTH7R` / `TP4054` `STAT` | Hardware | Li-ion charger status (not a GPIO; lights on USB when `B+` is open and `VCC` draws load) |

- **Enclosure Orientation (`20.0 × 20.0 × 1.2 mm` PCB, `R = 2.0 mm` corners)**:
  - **Antenna Side (`TOP层` -> `+Z` UP)**: The front face containing the two diagonally opposite 24 GHz patch antennas and `ICL1112` transceiver IC faces **UP (`+Z`)** directly toward the lid's **`22 × 22 × 1.2 mm`** blind RF radome window.
  - **Component / Header Side (`Bottom层` -> `-Z` DOWN, `J2` -> `+X`)**: The underside containing the `PY32F030` MCU, `YXC` crystal, and `-Z` 5-pin `J2` header faces **DOWN (`-Z`)** with **`19.5 mm`** of under-board vertical clearance, and the `J2` 5-pin header edge faces **`+X` directly toward the SuperMini nRF52840** for short, unpinched cable routing.
  - **Optional Decoupling Capacitor (`10–47 µF`)**: Because `Pin 1 (3V3)` and `Pin 2 (GND)` on `J2` are immediately adjacent (`2.54 mm` pitch), an optional `10–47 µF` capacitor can be soldered directly across Pins 1 and 2 on the `-Z` underside to smooth 24 GHz chirp current spikes.

---

## 2. BTHome v2 BLE Advertising Format

The sensor operates as a **non-connectable, scannable BLE broadcaster** using the official **BTHome v2** service UUID (`0xFCD2`). Home Assistant auto-discovers it natively via local Bluetooth adapters or **ESPHome Bluetooth Proxies** with zero pairing codes or cloud dependencies.

### Device Identity

- **Complete Local Name** (Scan Response): `Presence-XXXX` (where `XXXX` is the uppercase hex of the folded 16-bit FNV-1a hash computed by `BthomeProto::DeriveShortIdFromDeviceId()` over `hwinfo_get_device_id()`).
- **BLE Address**: Deterministic Static Random MAC derived from `hwinfo_get_device_id()` (`(addr[5] & 0xC0) == 0xC0`), ensuring a stable device entity across battery swaps and firmware updates.

### BTHome v2 Service Data Payload (`0xFCD2`, 17 Bytes)

Object IDs are encoded in **strictly ascending numerical order** per the BTHome v2 specification:

| Byte Offset | Field / Object ID | Type | Description |
| :--- | :--- | :--- | :--- |
| `0..1` | `0xD2, 0xFC` | UUID16 LE | BTHome v2 Service UUID (`0xFCD2`) |
| `2` | `0x40` | Device Info | BTHome v2 (`bit 5..7 = 2`), unencrypted (`bit 0 = 0`), regular update (`bit 2 = 0`) |
| `3..4` | `0x00, <pkt_id>` | `uint8` | **Packet ID** (`0..255` monotonic deduplication counter) |
| `5..6` | `0x01, <pct>` | `uint8` (`1 %`) | **Battery Percentage** (`0..100 %`, piecewise Li-ion curve) |
| `7..9` | `0x0C, <mv_lo>, <mv_hi>` | `uint16` LE (`0.001 V`) | **Battery Voltage** in millivolts (e.g., `4125` -> `4.125 V`) |
| `10..11` | `0x21, <0\|1>` | `uint8` (`bool`) | **Motion** (`1` = active walking/movement, `0` = stationary or clear) |
| `12..13` | `0x23, <0\|1>` | `uint8` (`bool`) | **Occupancy / Presence** (`1` = `Detected` moving or stationary breathing human, `0` = `Clear`) |
| `14..16` | `0x40, <mm_lo>, <mm_hi>` | `uint16` LE (`1 mm`) | **Target Distance** in millimeters (`0..65535 mm`, converted from HLK-LD2410S cm) |

**Primary Advertising PDU Size**: `3` bytes (Flags AD structure) + `19` bytes (Service Data AD structure) = **`22` bytes** (well within the `31`-byte BLE legacy advertising limit).

### Advertising Cadence

- **Immediate State-Change Burst**: On any occupancy/motion transition (`OT2` interrupt or UART target-state change) or `>= 100 mm` distance shift while occupied, the broadcaster enters a **100 ms advertising burst for 1.5 s** (~15 packets) with a newly incremented Packet ID so Home Assistant triggers bathroom lighting/automation within `< 150 ms`.
- **Steady-State Idle Broadcast**: Between events, the advertising interval relaxes to **2.5 s** (`2500 ms`), keeping average BLE radio current at ~`7 µA`, with a periodic state refresh every `60 s` (`CONFIG_APP_HEARTBEAT_INTERVAL_SEC`).
- **Periodic Radar UART Poll**: `uart0` wakes briefly every `5 s` (`CONFIG_APP_OCCUPIED_DISTANCE_POLL_SEC`) via interrupt-driven EasyDMA/ISR RX (`CONFIG_UART_INTERRUPT_DRIVEN=y`) for up to `1150 ms` (`SensorLd2410s::kDefaultSampleTimeoutMs`) to read the next `1.0 Hz` target distance and occupancy/motion frame from the HLK-LD2410S (handling both 5-byte Minimal `0x6E...0x62` and 12/80-byte Standard `F4 F3 F2 F1 ... F8 F7 F6 F5` output frames) before immediately re-suspending `uart0`.
- **Battery Refresh**: SAADC `VDDH/5` is sampled at boot and every `6 hours` (`21600 s`, `CONFIG_APP_BATTERY_SAMPLE_INTERVAL_SEC`).

---

## 3. Bathroom Radar Tuning (3 m³ Volume)

At boot, the firmware configures the HLK-LD2410S over `uart0` (`115200` baud on `P0.08` RX / `P0.06` TX) for a compact **3 m³ bathroom** (~`1.5 m × 1.5 m × 2.2 m`) and switches the radar to its **Minimal 5-Byte Output Format** (`6E [state] [dist_lo] [dist_hi] 62`):

| Parameter (Command `0x0070`) | Kconfig / Constant | Default Value | Setting | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Farthest Detection Gate** | `CONFIG_APP_RADAR_MAX_GATE` | `3` | `2.10 m` (`3 × 0.70 m`) | Rejects ghost reflections through bathroom walls or doors beyond `2.10 m` |
| **Nearest Detection Gate** | `CONFIG_APP_RADAR_MIN_GATE` | `0` | `0.00 m` | Detects presence right up to the sensor enclosure |
| **Unmanned Delay / Hold Time** | `CONFIG_APP_RADAR_HOLD_S` | `30` | `30 s` | Holds presence across brief motionless intervals without keeping lights on long after exit |
| **Status Report Frequency** | `kDefaultReportFreqTenthsHz` | `10` | `1.0 Hz` (`10 × 0.1 Hz`) | Enables HLK-LD2410S low-speed sleep mode (~`58 - 100 µA`) |
| **Distance Report Frequency** | `kDefaultReportFreqTenthsHz` | `10` | `1.0 Hz` (`10 × 0.1 Hz`) | Matches 1 Hz low-power cadence |
| **Response Speed** | `kDefaultResponseSpeedNormal` | `5` | Normal (`5`) | Fast entry detection (~`0.5 - 1.0 s`) with low false-trigger rate |

Gate and hold parameters are tunable via Kconfig (`CONFIG_APP_RADAR_MAX_GATE`, `CONFIG_APP_RADAR_MIN_GATE`, `CONFIG_APP_RADAR_HOLD_S`, `CONFIG_APP_OCCUPIED_DISTANCE_POLL_SEC` in `Kconfig`).

---

## 4. How to Build & Test

The firmware is built using Nordic's **nRF Connect SDK v2.8.0** and **Zephyr RTOS**.

### Host Protocol Unit Tests

Pure C++20 encoders and parsers for the HLK-LD2410S binary protocol (`src/ld2410s_proto.*`) and BTHome v2 payloads (`src/bthome_proto.*`) run natively on macOS/Linux without hardware:

```bash
scripts/run-tests.sh
```

### Local Zephyr Build

Expects the SDK in `~/ncs` next to this repo in `~/git/presence-sensor-nrf`:

```bash
source env.sh

# Release build (UART console & logging disabled for battery life)
west build --no-sysbuild -b nice_nano/nrf52840 -p always -o=-k0 \
  -s ~/git/presence-sensor-nrf \
  -d ~/git/presence-sensor-nrf/build -- \
  -DBOARD_ROOT=$HOME/git/presence-sensor-nrf
```

For benchtop bring-up with live logs over USB CDC ACM (`screen /dev/cu.usbmodem* 115200`), build with `debug.conf` and `debug.overlay`:

```bash
source env.sh
west build --no-sysbuild -b nice_nano/nrf52840 -p always -o=-k0 \
  -s ~/git/presence-sensor-nrf \
  -d ~/git/presence-sensor-nrf/build -- \
  -DBOARD_ROOT=$HOME/git/presence-sensor-nrf \
  -DEXTRA_CONF_FILE=debug.conf \
  -DEXTRA_DTC_OVERLAY_FILE=debug.overlay
```

### GitHub Actions Build

Every push runs `.github/workflows/build.yml` (host unit tests + Release UF2 + Debug UF2 in `ghcr.io/nrfconnect/sdk-nrf-toolchain:v2.8.0`). Download the latest CI artifacts into `build/zephyr/` with:

```bash
scripts/fetch-firmware.sh           # release build
scripts/fetch-firmware.sh --debug   # USB CDC ACM debug build
```

---

## 5. Flashing to SuperMini nRF52840

1. Connect the SuperMini nRF52840 to your Mac via USB-C.
2. **Double-click the RST button** within 0.5 s to enter the UF2 bootloader (`NICENANO` volume mounts).
3. **New board check**: Inspect `/Volumes/NICENANO/INFO_UF2.TXT`. If it reports `UF2 Bootloader 0.6.0`, first copy `update-nice_nano_bootloader-0.6.1_nosd.uf2` to `/Volumes/NICENANO/`, wait for reboot, and double-click `RST` again.
4. Flash the firmware from Terminal:
   ```bash
   cp -X build/zephyr/zephyr.uf2 /Volumes/NICENANO/
   ```
   *(A macOS Finder/cp I/O warning at the very end of the copy is normal because the board reboots immediately after the final UF2 block is written.)*

---

## 6. Home Assistant Integration

1. Ensure Home Assistant has either a local Bluetooth adapter or an **ESPHome Bluetooth Proxy** within BLE range of the bathroom, and the **BTHome** integration enabled.
2. Power on the sensor. Within seconds, Home Assistant automatically discovers **`Presence-XXXX`** under **Settings → Devices & Services → BTHome**.
3. Click **Configure → Submit** to add the device. It exposes five entities:
   - **Occupancy** (`binary_sensor.presence_xxxx_occupancy`, BTHome Object ID `0x23`, states `Clear` / `Detected`) — true for both moving and stationary/breathing presence. *(Note: If upgrading from an older firmware that used `0x2D` and showed `Window` / `Closed`, delete the device in **Settings → Devices & Services → BTHome → `Presence-XXXX` → Delete** so Home Assistant re-discovers it with `Occupancy`.)*
   - **Motion** (`binary_sensor.presence_xxxx_motion`, BTHome Object ID `0x21`, states `Clear` / `Detected`) — true during active movement.
   - **Distance** (`sensor.presence_xxxx_distance`, BTHome Object ID `0x40`) — target distance in mm / m.
   - **Battery** (`sensor.presence_xxxx_battery`, BTHome Object ID `0x01`) — `0–100 %`.
   - **Voltage** (`sensor.presence_xxxx_voltage`, BTHome Object ID `0x0C`) — cell voltage in `V`.

---

## 7. Power Budget & Battery Life

| Contributor | Approx. Average Current |
| :--- | :--- |
| **HLK-LD2410S** (Low-Speed 1 Hz low-power mode via `P0.13` 3.3 V rail) | `58 – 100 µA` |
| **nRF52840 System ON Idle** (RTC + RAM retention + GPIOTE `PORT` event on `P0.17`) | `~3 µA` |
| **BLE Non-Connectable Scannable Advertising** (2.5 s idle + event bursts) | `~7 µA` |
| **Brief `uart0` Wake Windows** (event-driven + 15 s occupied refresh, suspended in idle) | `< 3 µA` |
| **Hourly SAADC `VDDH/5` Battery Sample** (one-shot, 16× oversampling) | `< 0.1 µA` |
| **SuperMini Quiescent / Diode Leakage** (batch-dependent) | `4 – 60 µA` |
| **Total Estimated System Average** | **`~75 – 170 µA`** |

With a **2800 mAh Li-ion cell** (~`2200 mAh` usable above `3.0 V`), a `75 – 170 µA` average current yields **1.5 to 3.3 years** of continuous runtime per charge.

---

## 8. 3D-Printable Enclosures (3 Bambu A1 Models)

[`enclosure/enclosure.py`](enclosure/enclosure.py) generates **three complete, support-free Bambu A1 enclosure models** tailored to the **`20.0 × 20.0 × 1.2 mm` HLK-LD2410S** (`2.54 mm` 5-pin `J2` header facing `+X`), **SuperMini nRF52840**, and **18650 Li-ion cell** (see [`enclosure/README.md`](enclosure/README.md) for assembly and print settings):

| Model | Variant Name | Printable `.stl` Files (`enclosure/`) | CAD `.step` Files (`enclosure/`) | Closure & Mounting | Key Features & Best Use Case |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Model 1** | **Sealed Gasketed Wall-Mount** | `base.stl`, `lid.stl` | `base.step`, `lid.step`, `assembly.step` | 4× M3×8 screws + M3×5.7×4.6 heat-set inserts, 2 mm EPDM/TPU gasket groove, `±X` wall-mount tabs | Steam/splash-resistant bathroom wall mounting (`22 × 22 × 1.2 mm` blind RF radome window) |
| **Model 2** | **Snap-Fit + 45° Room-Corner Bracket** | `corner_base.stl`, `corner_lid.stl`, `corner_bracket.stl` | `corner_base.step`, `corner_lid.step`, `corner_bracket.step`, `corner_assembly.step` | Tool-less snap-fit lid (`±Y` barbs) + slide-on 45° downward-tilt 90° room-corner / ceiling bracket | Optimal 3 m³ bathroom corner coverage with zero metal fasteners or heat-set inserts |
| **Model 3** | **Freestanding Shelf / Vanity Pod** | `vanity_base.stl`, `vanity_lid.stl` | `vanity_base.step`, `vanity_lid.step`, `vanity_assembly.step` | Tool-less snap-fit lid (`±Y` barbs) + flat weighted `-Y` 18650 base foot | Stands upright on a bathroom shelf or vanity with a `+X` **USB-C pass-through port** for in-place 18650 recharging |
