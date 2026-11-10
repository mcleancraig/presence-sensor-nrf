# presence-sensor-nrf

24 GHz mmWave Human Presence, Motion, Distance, and Battery Sensor for **Home Assistant** over **OpenThread 1.3 + RFC 6052 NAT64 + Home Assistant MQTT Auto-Discovery** (plus a host-tested BTHome v2 BLE codec and wireless MQTT FOTA updater), built on the **SuperMini nRF52840** (`nice!nano v2` compatible) and the Hi-Link **HLK-LD2410S** (`20 × 20 mm`, `3.3 V` ultra-low-power radar) or **HLK-LD2410C** (`22 × 16 mm`, `5 V` continuous-power radar).

> **3D-Printable Enclosures (9 Models + Fit-Test Gauge):** Parametric CadQuery generators in [`enclosure/`](enclosure/README.md) produce **9 support-free Bambu Lab A1 enclosures** (`0.000 mm³` boolean interference, `1.20 mm` blind RF radome with `5.10 mm` antenna air gap) — covering sealed 18650 bathroom cases (**Models 1–3**), sleek desktop USB-C cases (**Models 4–5**), the flagship **`Aura v1` (`Aura-S v1` / `Aura-C v1`)** stadium monoliths with hidden rear USB-C (**Models 6–7**), and the ultra-compact stacked direct-solder **`Aura v2` (`Aura-S v2` / `Aura-C v2`)** monoliths with a sculpted flush-alcove side USB-C port (**Models 8–9**). See [Section 7](#7-3d-printable-enclosures-9-bambu-lab-a1-models--usb-c-fit-test-gauge).
>
> **Bring-up notes:** See [`doc/bringup-notes.md`](doc/bringup-notes.md) for flash offset requirements (`0x1000` without SoftDevice), `HLK-LD2410S` vs `HLK-LD2410C` power/UART architecture, and live USB CDC ACM debugging.

---

## 1. Hardware Architecture & Supported Configurations

The firmware supports two radar modules and two power modes out of the box:

| Feature / Parameter | **HLK-LD2410S (Default Build)** | **HLK-LD2410C (`ld2410c.conf` Overlay)** |
| :--- | :--- | :--- |
| **Kconfig Selection** | `CONFIG_APP_RADAR_LD2410S=y` (default in `Kconfig`) | `CONFIG_APP_RADAR_LD2410C=y` (`-DEXTRA_CONF_FILE="local.conf;ld2410c.conf"`) |
| **PCB Dimensions & Header** | **`20.0 × 20.0 × 1.2 mm`** square PCB (`R = 2.0 mm` corners); asymmetric 5-pin `2.54 mm` `J2` header (`3V3, GND, OT1, RX, OT2`) along `+X` edge | **`22.0 × 16.0 × 1.2 mm`** rectangular PCB (`R = 1.2 mm` corners); centered 5-pin `2.54 mm` header (`VCC, GND, OUT, RX, TX`) along `16.0 mm` `+X` edge |
| **Radar Supply Voltage** | **`3.0 – 3.6 V` regulated ONLY** (`~58 – 120 µA` in 1 Hz/8 Hz low-power mode). Powered from SuperMini switched **`3.3 V` `VCC` pin** (`P0.13` HIGH). **Never connect to `5 V` or raw `4.2 V` Li-ion!** | **`5.0 V` (`4.0 – 12.0 V` input to onboard SOT-23-5 `3.3 V` LDO)**, `~70 – 80 mA` avg (`120 – 200 mA` chirp peaks). Powered directly from **`5 V` USB-C socket `+`**, SuperMini **`D1` (`VBUS`)**, or **`RAW`/`B+` (`~4.1 V` with underside `BI-PROG` bridged for `300 mA`)**. |
| **Supported Power Sources** | **18650 Li-ion cell** (Models 1–3) **OR** **5 V USB-C** (Models 5, 6 `Aura-S v1`, 8 `Aura-S v2`) | **5 V USB-C** (Models 4, 7 `Aura-C v1`, 9 `Aura-C v2`) |
| **UART Baud Rate & Protocol** | `115200` baud 8N1; commands `0x0070` / `0x007A`; 5-byte minimal (`6E [state] [dist_lo] [dist_hi] 62`) & standard (`F4..F5`) frames | `256000` baud 8N1 (`NRF_UARTE_BAUDRATE_250000` with automatic `115200` baud & TX/RX pin-swap fallback); command `0x0060`; standard/engineering (`F4 F3 F2 F1 .. F8 F7 F6 F5`) frames |
| **Range Gate Spacing & Defaults** | **`0.70 m` / gate** — Gate `3` (`2.10 m`), `2100 mm` max distance clamp, `30 s` hold time (tuned for `~3 m³` bathroom) | **`0.75 m` / gate** — Gate `3` (`0`-indexed Gates `0..3` = `0.00..3.00 m`), `2950 mm` max distance clamp, `180 s` (`3 min`) hold time (tuned for seated office desk) |
| **OpenThread Role & Polling** | **Sleepy End Device (SED)** on battery (`5000 ms` sleep poll / `80 ms` active fast-poll, `400 ms` UART frame drain); or **Minimal End Device (MED, `RxOnWhenIdle=true`)** when `CONFIG_APP_ALWAYS_USB_POWERED=y` | **Minimal End Device (MED, `RxOnWhenIdle=true`)** (`CONFIG_APP_ALWAYS_USB_POWERED=y`, `CONFIG_OPENTHREAD_MTD_SED=n`, `100 ms` / `10 Hz` real-time UART processing, zero parent-poll latency, wireless MQTT FOTA enabled) |

---

## 2. Single-Source Master Wiring Table (`HLK-LD2410S` & `HLK-LD2410C` | Battery & USB-C Powered)

Use this single table for **all** hardware combinations (**`HLK-LD2410S`** vs **`HLK-LD2410C`**, and **18650 Battery-Powered** vs **USB-C Powered**, whether using a 5-pin DuPont connector or direct-soldering in `Aura v2`):

| Signal / Function | SuperMini nRF52840 Pin / Pad (`GPIO`) | `HLK-LD2410S` (`20 × 20 mm`, `3.3 V` Radar) `J2` Pin & Pad Geometry | `HLK-LD2410C` (`22 × 16 mm`, `5 V` Radar) Header Pin | **Battery-Powered Wiring** (18650 Cell — Models 1, 2, 3) | **USB-C Powered Wiring** (2-Pin Panel Socket `1005008559159734` — Models 4–9) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Radar Power (`VCC` / `3V3`)** | • **`LD2410S`**: **`VCC`** (`3.3 V` switched by `P0.13`)<br>• **`LD2410C`**: **Panel USB-C `+` (`5 V`)**, OR **`RAW`/`B+`** (bridge underside `BI-PROG`), OR **`D1` (`VBUS`)** | **`J2 Pin 1: 3V3`**<br>**Square pad**, `11.78 mm` from `+Y` top edge (near middle of `+X` edge).<br>⚠️ **`3.0–3.6 V` MAX!** | **`Pin 1: VCC`**<br>**Square pad** at end of 5-pin row.<br>Requires **`4.0–12.0 V` (`>= 200 mA` peak)** for onboard `3.3 V` LDO. | **`LD2410S` only:**<br>Wire `LD2410S J2 Pin 1 (3V3)` → SuperMini **`VCC`** (`3.3 V` LDO output; automatically cut off via `P0.13` LOW at `<= 3.0 V` battery cutoff). | • **`LD2410S` (Models 5, 6, 8)**: Wire `LD2410S J2 Pin 1 (3V3)` → SuperMini **`VCC` (`3.3 V`)**. *(Never wire `LD2410S` directly to `5 V`!)*<br>• **`LD2410C` (Models 4, 7, 9)**: Wire `LD2410C Pin 1 (VCC)` → **Panel USB-C `+` (`5 V` Red wire)** directly in parallel with SuperMini power input (recommended), OR to SuperMini **`RAW`/`B+`** (with underside `BI-PROG` bridged for `300 mA`), OR to SuperMini **`D1` (`VBUS`)**. |
| **2. Radar Ground (`GND`)** | **`GND`** (through-hole pin or `B-` pad) | **`J2 Pin 2: GND`**<br>Round pad, `9.24 mm` from `+Y` top edge (adjacent to `Pin 1 3V3`). | **`Pin 2: GND`**<br>Round pad adjacent to `Pin 1 VCC`. | Wire Radar `GND` → SuperMini **`GND`** (shared with `18650 -` plate). | Wire Radar `GND` → SuperMini **`GND`** (shared with Panel USB-C `-` Black wire). |
| **3. Radar UART TX → MCU RX** | **`008`** (`D0` / **`P0.08`**, `uart0` RX) | **`J2 Pin 3: OT1`**<br>Round pad, `6.70 mm` from `+Y` top edge (`115200` baud). | **`Pin 5: TX`**<br>Round pad at far end of 5-pin row (`256000` baud; auto-swaps if crossed). | Wire `LD2410S J2 Pin 3 (OT1)` → SuperMini **`008` (`P0.08`)**. | • **`LD2410S`**: Wire `J2 Pin 3 (OT1)` → **`008` (`P0.08`)**.<br>• **`LD2410C`**: Wire `Pin 5 (TX)` → **`008` (`P0.08`)**. |
| **4. MCU UART TX → Radar RX** | **`006`** (`D1` / **`P0.06`**, `uart0` TX) | **`J2 Pin 4: RX`**<br>Round pad, `4.16 mm` from `+Y` top edge (`115200` baud). | **`Pin 4: RX`**<br>Round pad (`256000` baud; auto-swaps if crossed). | Wire `LD2410S J2 Pin 4 (RX)` → SuperMini **`006` (`P0.06`)**. | • **`LD2410S`**: Wire `J2 Pin 4 (RX)` → **`006` (`P0.06`)**.<br>• **`LD2410C`**: Wire `Pin 4 (RX)` → **`006` (`P0.06`)**. |
| **5. Radar Wake / Presence Out** | **`017`** (`D2` / **`P0.17`**, `GPIO_INT_EDGE_BOTH`) | **`J2 Pin 5: OT2`**<br>Round pad at `+Y` corner, `1.62 mm` from `+Y` top edge. | **`Pin 3: OUT`**<br>Round pad in center of 5-pin row. | Wire `LD2410S J2 Pin 5 (OT2)` → SuperMini **`017` (`P0.17`)** for instant `< 5 ms` wake from System ON Idle. | • **`LD2410S`**: Wire `J2 Pin 5 (OT2)` → **`017` (`P0.17`)**.<br>• **`LD2410C`**: Wire `Pin 3 (OUT)` → **`017` (`P0.17`)** *(optional on 4-wire hookups)*. |
| **6. Primary Power Input (`18650` or `USB-C`)** | **`B+` / `RAW`** (`VDDH` / `LTH7R BAT`) or **`D1` (`VBUS`)**, and **`B-` / `GND`** | *(Supplied via Row 1 & Row 2)* | *(Supplied via Row 1 & Row 2)* | • **`18650 +` button contact plate** → SuperMini **`B+`** pad (measured internally via SAADC `VDDH/5`; recharges via SuperMini USB-C port in Model 3).<br>• **`18650 -` spring contact plate** → SuperMini **`B-` (`GND`)** pad. | • **Panel USB-C `+` (`5 V` Red wire)** → SuperMini **`RAW` or `B+`** pad (or `D1` `VBUS` pad; on `LD2410C` builds, split `+5 V` directly to both SuperMini `RAW`/`B+` and `LD2410C Pin 1 VCC`).<br>• **Panel USB-C `-` (`GND` Black wire)** → SuperMini **`GND` or `B-`** pad. |
| **7. Optional Decoupling Cap** | — | Across adjacent **`J2 Pin 1 (3V3)` & `Pin 2 (GND)`** (`2.54 mm` spacing) | Across adjacent **`Pin 1 (VCC)` & `Pin 2 (GND)`** (`2.54 mm` spacing) | Optional `10–47 µF` ceramic/electrolytic capacitor on `-Z` header pins smooths 24 GHz FMCW chirp current spikes. | Optional `10–47 µF` capacitor across radar `Pin 1` & `Pin 2`. |
| **8. On-Board LEDs** | • Red: **`P0.15`**<br>• Blue: **`LTH7R STAT`** | — | — | Red LED flashes `500 ms` at boot, then stays strictly OFF (`0 V`). | Blue charger LED is hardwired to `LTH7R` charger `STAT` (not a GPIO). |

### Important Hardware Notes

1. **Why `RAW` and `B+` Measure `~4.1 V` on USB Power (`LTH7R` Charger Current Limit)**:
   - On the SuperMini nRF52840 schematic, the top-right through-hole **`RAW`** pin and the front **`B+`** pad are physically tied to the same copper net (`VBAT`), which is the `BAT` output (`Pin 3`) of the onboard **`LTH7R` (`TP4054`/`LP4057`) `4.2 V` Li-ion charger IC** — **not** direct `5 V` USB `VBUS`.
   - When using the **2-Pin Panel-Mount USB-C Socket (`1005008559159734`, Models 4–9)** with the **`HLK-LD2410C`**:
     - **Best Practice (Direct Parallel `5 V` Split)**: Splice or solder the Panel USB-C Socket **`+` (`5 V` Red)** wire directly to **both** the SuperMini (`RAW` or `B+` pad) **and** `HLK-LD2410C Pin 1 (VCC)`. That way, the radar receives full `5.0 V` directly from the USB-C socket and its `120–200 mA` chirp peaks bypass the SuperMini's `LTH7R` charger IC completely.
     - **If Powering `HLK-LD2410C` from SuperMini USB-C via `RAW`/`B+`**: Bridge the 2-pad **`BI-PROG`** (`BOOST`) solder jumper on the underside of the SuperMini (next to the `VDD / DIO / CLK / GND` SWD pads) to raise the `LTH7R` current limit from `100 mA` to **`300 mA`**, or tap `~4.8 V` `VBUS` directly at Schottky diode **`D1`** / **`LTH7R Pin 4`** behind the SuperMini's USB-C port.
2. **Mechanical Radar Orientation inside All Enclosures (Models 1–9)**:
   - **Antenna Side (`TOP层` → `+Z` UP toward Lid)**: The face with the gold 24 GHz patch antennas faces **UP (`+Z`)** directly beneath the lid's **`1.20 mm` blind RF radome window** (`22 × 22 mm` for `HLK-LD2410S`, `24 × 18 mm` for `HLK-LD2410C`), maintaining an exact **`5.10 mm` (`~0.41 λ₀`) antenna air gap**.
   - **Component & Header Side (`Bottom层` → `-Z` DOWN, 5-Pin Header → `+X`)**: The underside with the MCU, crystal, and 5-pin header/pads faces **DOWN (`-Z`)**, with the 5-pin header edge on **`+X`** facing the SuperMini nRF52840.

---

## 3. OpenThread 1.3 + NAT64 + Home Assistant MQTT Auto-Discovery & Wireless FOTA

The sensor operates on your Thread mesh at **`+8 dBm` (`6.3 mW`) IEEE 802.15.4 TX power** (`CONFIG_OPENTHREAD_DEFAULT_TX_POWER=8`), synthesizes the IPv6 address of your Home Assistant Mosquitto MQTT broker from the OpenThread Border Router's `/96` **RFC 6052 NAT64 prefix**, and publishes retained **Home Assistant MQTT Auto-Discovery** payloads plus real-time JSON state updates.

### Device Identity, Topics & Auto-Discovered Entities

- **Display Name**: `Presence-XXXX` (uppercase hex of the folded 16-bit FNV-1a hash of `hwinfo_get_device_id()`).
- **Node Slug**: `presence_xxxx` (`HaMqttProto::FormatNodeSlug()`).
- **State Topic**: `presence_sensor/presence_xxxx/state`
  ```json
  {"occupancy":"ON","motion":"ON","distance_mm":1340,"battery_pct":87,"voltage_mv":3985,"packet_id":42}
  ```
- **Availability Topic (LWT)**: `presence_sensor/presence_xxxx/status` (`"online"` / `"offline"`, retained).
- **Auto-Discovered Entities (5 Entities)**:
  - `binary_sensor.presence_xxxx_occupancy` (`device_class: occupancy` — Moving + Stationary/Breathing presence)
  - `binary_sensor.presence_xxxx_motion` (`device_class: motion` — Kinematic radial movement `>= 100 mm` with `5.0 s` active hold window via `Ld2410sMotionTracker`)
  - `sensor.presence_xxxx_distance` (`device_class: distance`, `mm`)
  - `sensor.presence_xxxx_battery` (`device_class: battery`, `%`)
  - `sensor.presence_xxxx_voltage` (`device_class: voltage`, `mV`)

### Wireless MQTT Firmware Over-The-Air (FOTA) Updates (`scripts/push-ota.py`)

Always-powered USB builds (`CONFIG_APP_ALWAYS_USB_POWERED=y`, default on `ld2410c.conf` and optional on USB-powered `HLK-LD2410S` builds) run an internal dual-slot flash staging receiver (`FotaReceiver`) subscribed to `presence_sensor/presence_xxxx/ota/#` (and broadcast `presence_sensor/all/ota/#`):

```bash
# Push a newly built zephyr.bin over MQTT/OpenThread to a specific node or all USB-powered nodes:
python3 scripts/push-ota.py --node presence_xxxx --firmware build_ld2410c/zephyr/zephyr.bin
```

---

## 4. Radar Detection Tuning (`Kconfig`)

All detection parameters can be overridden in `local.conf` or `ld2410c.conf`:

| Kconfig Option | `HLK-LD2410S` Default (`3 m³` Bathroom) | `HLK-LD2410C` Default (`ld2410c.conf` Office) | Description |
| :--- | :--- | :--- | :--- |
| `CONFIG_APP_RADAR_MAX_GATE` | `3` (`2.10 m` at `0.70 m`/gate) | `3` (`3.00 m` for 0-indexed Gates `0..3` at `0.75 m`/gate) | Hardware farthest detection gate programmed into the radar at boot |
| `CONFIG_APP_RADAR_MIN_GATE` | `0` (`0.00 m`) | `0` (`0.00 m`) | Hardware nearest detection gate |
| `CONFIG_APP_RADAR_MAX_DISTANCE_MM` | `2100` (`2.10 m`) | `2950` (`2.95 m`) | Software distance boundary clamp (ignores far-wall/door bounce beyond room boundary) |
| `CONFIG_APP_RADAR_HOLD_S` | `30` (`30 s`) | `180` (`3 min`) | Unoccupied delay / presence hold time after last detected motion or breathing |
| `CONFIG_APP_RADAR_POLL_INTERVAL_MS` | `400` (`2.5 Hz` drain of `8.0 Hz` radar stream) | `100` (`10 Hz` real-time drain) | Interval between non-blocking drains of the interrupt-driven `mRxRing[256]` UART buffer |
| `CONFIG_APP_ALWAYS_USB_POWERED` | `n` (set `y` for USB-powered `LD2410S`) | `y` | Enables always-on OpenThread MED (`RxOnWhenIdle=true`), continuous `10 Hz` UART polling, and wireless MQTT FOTA |

---

## 5. How to Build, Test & Flash

Built with Nordic **nRF Connect SDK v2.8.0** and **Zephyr RTOS**.

### 1. Run Host Unit Tests (`248` Protocol & Codec Assertions)

```bash
./scripts/run-tests.sh
```

### 2. Configure `local.conf` (`Zero Secrets Invariant`)

Create a gitignored `local.conf` in the repository root with your OpenThread Active Operational Dataset TLV hex string and Home Assistant MQTT broker credentials (**never commit `local.conf` to git**):

```ini
CONFIG_APP_THREAD_DATASET_TLV_HEX="<your-openthread-active-dataset-tlv-hex>"
CONFIG_APP_MQTT_BROKER_IPV4="192.168.41.250"
CONFIG_APP_MQTT_BROKER_PORT=1883
CONFIG_APP_MQTT_USERNAME="<your-mqtt-username>"
CONFIG_APP_MQTT_PASSWORD="<your-mqtt-password>"
```

### 3. Local Zephyr Builds (`HLK-LD2410S` & `HLK-LD2410C`)

```bash
source env.sh

# A. HLK-LD2410S Release Build (Default — 18650 Battery SED; add CONFIG_APP_ALWAYS_USB_POWERED=y in local.conf for USB MED)
west build --no-sysbuild -b nice_nano/nrf52840 -p always -o=-k0 \
  -s ~/git/presence-sensor-nrf \
  -d ~/git/presence-sensor-nrf/build -- \
  -DBOARD_ROOT=$HOME/git/presence-sensor-nrf

# B. HLK-LD2410C Release Build (Constant USB-C Power, OpenThread MED, 10 Hz Poll, Wireless FOTA)
west build --no-sysbuild -b nice_nano/nrf52840 -p always -o=-k0 \
  -s ~/git/presence-sensor-nrf \
  -d ~/git/presence-sensor-nrf/build_ld2410c -- \
  -DBOARD_ROOT=$HOME/git/presence-sensor-nrf \
  -DEXTRA_CONF_FILE="local.conf;ld2410c.conf"

# C. USB CDC ACM Debug Build (live logs on /dev/cu.usbmodem* at 115200; append ;ld2410c.conf for LD2410C)
west build --no-sysbuild -b nice_nano/nrf52840 -p always -o=-k0 \
  -s ~/git/presence-sensor-nrf \
  -d ~/git/presence-sensor-nrf/build_debug -- \
  -DBOARD_ROOT=$HOME/git/presence-sensor-nrf \
  -DEXTRA_CONF_FILE="local.conf;debug.conf" \
  -DEXTRA_DTC_OVERLAY_FILE=debug.overlay
```

Or fetch prebuilt CI artifacts from GitHub Actions:

```bash
./scripts/fetch-firmware.sh                     # HLK-LD2410S release UF2
./scripts/fetch-firmware.sh --debug             # HLK-LD2410S debug UF2
./scripts/fetch-firmware.sh --ld2410c           # HLK-LD2410C release UF2
./scripts/fetch-firmware.sh --ld2410c --debug   # HLK-LD2410C debug UF2
```

### 4. Flashing via UF2 Bootloader (`0x1000` Flash Offset)

1. Connect the SuperMini nRF52840 via USB-C and **double-click `RST`** within `0.5 s` to mount `/Volumes/NICENANO`.
2. **Bootloader version check (new boards)**: Check `/Volumes/NICENANO/INFO_UF2.TXT`. If it reports `UF2 Bootloader 0.6.0`, copy `update-nice_nano_bootloader-0.6.1_nosd.uf2` to `/Volumes/NICENANO/` first, let it reboot, and double-click `RST` again.
3. Copy the UF2 image:
   ```bash
   cp -X build/zephyr/zephyr.uf2 /Volumes/NICENANO/
   ```

---

## 6. Battery Power Budget (`HLK-LD2410S` + `18650` Cell, Models 1–3)

| Contributor | Approx. Average Current |
| :--- | :--- |
| **HLK-LD2410S** (Low-power mode via `P0.13` `3.3 V` rail; `8.0 Hz` fast response) | `58 – 120 µA` |
| **nRF52840 System ON Idle** (RTC + RAM retention + GPIOTE `PORT` wake on `P0.17`) | `~3 µA` |
| **OpenThread 1.3 SED Radio** (`+8 dBm` TX, `5.0 s` sleep poll / `80 ms` active fast-poll) | `~8 – 18 µA` |
| **Brief `uart0` Wake Windows** (`OT2`-gated in 5-wire mode; `~62 ms` every `400 ms` while occupied) | `~3 – 75 µA` |
| **1-Hour SAADC `VDDH/5` Battery Sample** (one-shot, 16× oversampling) | `< 0.1 µA` |
| **SuperMini Quiescent / Diode Leakage** (batch-dependent) | `4 – 60 µA` |
| **Total Estimated System Average** | **`~75 – 265 µA` (~1.0 to 3.3 years on a 2800 mAh 18650 cell)** |

---

## 7. 3D-Printable Enclosures (9 Bambu Lab A1 Models + USB-C Fit-Test Gauge)

[`enclosure/enclosure.py`](enclosure/enclosure.py) and [`enclosure/enclosure_variants.py`](enclosure/enclosure_variants.py) build **9 support-free Bambu Lab A1 enclosure variants** plus a **4-station USB-C clip-retention fit-test gauge**, verified by [`enclosure/verify.py`](enclosure/verify.py) (`0.000 mm³` boolean overlap across all solid pairs, `1.20 mm` blind RF radome with `5.10 mm` antenna air gap) and [`enclosure/sections.py`](enclosure/sections.py) (`34` 2D cross-section PNGs in [`enclosure/out/sections/`](enclosure/out/sections/)). See [`enclosure/README.md`](enclosure/README.md) for full print and assembly details:

| Model | Variant & Radar | Outer Dimensions | Power & USB-C Port Style | Printable `.stl` Files (`enclosure/out/`) | Best Use Case |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Model 1** | **Sealed Gasketed Wall-Mount** (`HLK-LD2410S`, `20 × 20 mm`) | `118.8 × 76.1 × 29.4 mm` | `18650` cell (`10 × 10 mm` nickel contact plates) | [`base.stl`](enclosure/out/base.stl), [`lid.stl`](enclosure/out/lid.stl) | Steam-proof bathroom/outdoor wall mounting (4× `M3` heat-set inserts, `2 mm` EPDM/TPU O-ring gasket groove, `±X` wall tabs) |
| **Model 2** | **45° Room-Corner / Ceiling Snap-Fit** (`HLK-LD2410S`, `20 × 20 mm`) | `86.8 × 56.4 × 29.4 mm` | `18650` cell (`10 × 10 mm` nickel contact plates) | [`corner_base.stl`](enclosure/out/corner_base.stl), [`corner_lid.stl`](enclosure/out/corner_lid.stl), [`corner_bracket.stl`](enclosure/out/corner_bracket.stl) | Tool-less snap-fit case that slides into a 90° room-corner / ceiling bracket aiming the radar at a **45° downward pitch** |
| **Model 3** | **Freestanding Vanity / Shelf Pod** (`HLK-LD2410S`, `20 × 20 mm`) | `86.8 × 54.4 × 29.4 mm` | `18650` cell + `+X` SuperMini USB-C recharge pass-through | [`vanity_base.stl`](enclosure/out/vanity_base.stl), [`vanity_lid.stl`](enclosure/out/vanity_lid.stl) | Stands upright on a flat `-Y` pedestal foot (low-CG 18650 at bottom) with in-place USB-C recharging |
| **Model 4** | **Sleek Desktop Pod (`LD2410C`)** (`HLK-LD2410C`, `22 × 16 mm`) | `86.8 × 28.8 × 27.4 mm` | `+X` side 2-pin panel USB-C socket (`13.2 / 13.4 mm` 3-zone clip bay, no battery) | [`ld2410c_base.stl`](enclosure/out/ld2410c_base.stl), [`ld2410c_lid.stl`](enclosure/out/ld2410c_lid.stl), [`v_stand.stl`](enclosure/out/v_stand.stl) | Slim tabless beveled desktop pod (**45% narrower** than 18650 models) with detachable **Inverted-V (`ʌ`) stand** |
| **Model 5** | **Sleek Desktop Pod (`LD2410S`)** (`HLK-LD2410S`, `20 × 20 mm`) | `86.8 × 32.8 × 29.4 mm` | `+X` side 2-pin panel USB-C socket (`13.2 / 13.4 mm` 3-zone clip bay, no battery) | [`ld2410s_usb_base.stl`](enclosure/out/ld2410s_usb_base.stl), [`ld2410s_usb_lid.stl`](enclosure/out/ld2410s_usb_lid.stl), [`v_stand.stl`](enclosure/out/v_stand.stl) | Same sleek desktop pod architecture as Model 4, sized for `20 × 20 mm` `HLK-LD2410S` + 5-pin female DuPont connector |
| **Model 6** | **`Aura-S v1` (`aura_v1`) — Horizon Stadium Monolith** (`HLK-LD2410S`, `20 × 20 mm` + DuPont) | `92.0 × 34.0 × 29.4 mm` (`R = 17.0 mm` stadium) | **Hidden rear (`Z = 0`)** 2-pin panel USB-C socket (`13.2 / 13.4 mm` 3-zone clip bay) | [`aura_v1_base.stl`](enclosure/out/aura_v1_base.stl), [`aura_v1_lid.stl`](enclosure/out/aura_v1_lid.stl), [`aura_v1_stand.stl`](enclosure/out/aura_v1_stand.stl) *(also `aura_s_v1_*`)* | Award-edition architectural stadium capsule with front horizon shadow groove, hidden rear power cord, and beveled **Inverted-V (`ʌ`) floating pedestal** |
| **Model 7** | **`Aura-C v1` (`aura_c_v1`) — Horizon Stadium Monolith** (`HLK-LD2410C`, `22 × 16 mm` + DuPont) | `92.0 × 32.0 × 27.4 mm` (`R = 16.0 mm` stadium) | **Hidden rear (`Z = 0`)** 2-pin panel USB-C socket (`13.2 / 13.4 mm` 3-zone clip bay) | [`aura_c_v1_base.stl`](enclosure/out/aura_c_v1_base.stl), [`aura_c_v1_lid.stl`](enclosure/out/aura_c_v1_lid.stl), [`aura_c_v1_stand.stl`](enclosure/out/aura_c_v1_stand.stl) | Slimmer `32.0 mm` award-edition stadium capsule for the `22 × 16 mm` `HLK-LD2410C` with hidden rear USB-C and beveled **Inverted-V (`ʌ`) pedestal** |
| **Model 8** | **`Aura-S v2` (`aura_v2`) — Compact Stacked Direct-Solder Monolith** (`HLK-LD2410S`, `20 × 20 mm`) | **`64.0 × 34.0 × 23.4 mm`** (`45%` smaller volume than `v1`) | **Sculpted flush-alcove `+X` side** 2-pin panel USB-C socket (`X = +28.50 mm` recessed seat + `45°` halo) | [`aura_v2_base.stl`](enclosure/out/aura_v2_base.stl), [`aura_v2_lid.stl`](enclosure/out/aura_v2_lid.stl), [`aura_v2_stand.stl`](enclosure/out/aura_v2_stand.stl) *(also `aura_s_v2_*`)* | Stacks direct-soldered `HLK-LD2410S` (`Z = 15.9 mm`) vertically over SuperMini (`Z = 5.4 mm`); smooth unbroken `Z = 0` back face + flush side USB-C + compact **Inverted-V (`ʌ`) pedestal** |
| **Model 9** | **`Aura-C v2` (`aura_c_v2`) — Compact Stacked Direct-Solder Monolith** (`HLK-LD2410C`, `22 × 16 mm`) | **`64.0 × 32.0 × 23.4 mm`** (`2:1` stadium proportion) | **Sculpted flush-alcove `+X` side** 2-pin panel USB-C socket (`X = +28.50 mm` recessed seat + `45°` halo) | [`aura_c_v2_base.stl`](enclosure/out/aura_c_v2_base.stl), [`aura_c_v2_lid.stl`](enclosure/out/aura_c_v2_lid.stl), [`aura_c_v2_stand.stl`](enclosure/out/aura_c_v2_stand.stl) | Stacks direct-soldered `HLK-LD2410C` (`Z = 15.9 mm`) vertically over SuperMini (`Z = 5.4 mm`); smooth unbroken `Z = 0` back face + flush side USB-C + compact **Inverted-V (`ʌ`) pedestal** |
| **Fit-Test** | **USB-C Socket 4-Way Clip-Retention Gauge** | `46.9 × 100.8 × 18.0 mm` | Tests `12.6, 12.8, 13.0, 13.2 mm` clip collars + `13.4 × 5.8 mm` stem sleeve | [`usbc_socket_fit_test.stl`](enclosure/out/usbc_socket_fit_test.stl) | Dual-orientation (`Z = 0` rear & `+X` side) test gauge for AliExpress `1005008559159734` panel USB-C socket (Station #4 `13.2 mm` collar = calibrated winner) |
