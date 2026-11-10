# Bathroom / Outdoor & Flagship Desktop Presence Sensor Enclosures (9 Variants + USB-C Fit Test)

Parametric 3D-printable enclosures for the **SuperMini nRF52840 + Hi-Link HLK-LD2410S (`20 × 20 mm`) or HLK-LD2410C (`22 × 16 mm`) 24 GHz mmWave Radar + 18650 / USB-C** presence sensor, built with [CadQuery](https://cadquery.readthedocs.io/).

All nine enclosure variants share the same verified, wall-joined internal architecture (`0.000 mm³` boolean interference across all solid pairs, `1.20 mm` blind RF radome with `5.10 mm` antenna air gap, zero free-standing thin pillars, unobstructed lid interior over the SuperMini nRF52840 for cabling, and deep-engagement `0.45 mm` chamfered snap-fit lid locks) and are ready to slice in **Bambu Studio** for the **Bambu Lab A1** (`0.4 mm` nozzle, `0.20 mm` layer height, **Arachne** wall generator, **zero supports**):

| Variant | Printable STL Files | Purpose & Mounting Style |
|---|---|---|
| **Model 1: Sealed Gasketed Wall-Mount (`HLK-LD2410S`)** | [`out/base.stl`](out/base.stl), [`out/lid.stl`](out/lid.stl) | Steam-proof bathroom/outdoor enclosure (`118.8 × 76.1 × 29.4 mm`) with an exterior `2 mm` EPDM O-ring gasket groove, 4× `M3` heat-set inserts, and `±X` wall-mount screw tabs. |
| **Model 2: Angled 45° Corner / Ceiling Snap-Fit (`HLK-LD2410S`)** | [`out/corner_base.stl`](out/corner_base.stl), [`out/corner_lid.stl`](out/corner_lid.stl), [`out/corner_bracket.stl`](out/corner_bracket.stl) | Compact flangeless snap-fit case (`86.8 × 56.4 × 29.4 mm`) that slides into a support-free **90° room-corner / ceiling bracket** holding the radar at a **45° downward pitch** into a `3 m³` bathroom. |
| **Model 3: Freestanding Vanity / Shelf Pod (`HLK-LD2410S`, USB-C)** | [`out/vanity_base.stl`](out/vanity_base.stl), [`out/vanity_lid.stl`](out/vanity_lid.stl) | Sleek freestanding pod (`86.8 × 54.4 × 29.4 mm`) that stands upright on its flat `-Y` pedestal foot (heavy 18650 cell at the bottom for low CG, radar facing horizontally into the room) with a precision **`+X` USB-C pass-through port** for in-place 18650 recharging. |
| **Model 4: HLK-LD2410C Sleek Desktop Case (`22 × 16 mm` + Panel USB-C Socket)** | [`out/ld2410c_base.stl`](out/ld2410c_base.stl), [`out/ld2410c_lid.stl`](out/ld2410c_lid.stl), [`out/v_stand.stl`](out/v_stand.stl) | Sleek flangeless/tabless desktop pod (`86.8 × 28.8 × 27.4 mm` body — **45% narrower**, no `18650` cell, no screw ears, 45° perimeter bevels) for the **`22.0 × 16.0 × 1.2 mm` HLK-LD2410C**, featuring a `+X` snap-in bay for the **AliExpress 2-Pin Panel-Mount USB-C Socket (`1005008559159734`, calibrated `13.4 mm` slot)**, `24 × 18 × 1.2 mm` blind RF radome, and flush `-Y` blind mortises for the detachable **Inverted-V (`ʌ`) Desktop Stand (`v_stand.stl`)**. |
| **Model 5: HLK-LD2410S Sleek Desktop Case (`20 × 20 mm` + Panel USB-C Socket)** | [`out/ld2410s_usb_base.stl`](out/ld2410s_usb_base.stl), [`out/ld2410s_usb_lid.stl`](out/ld2410s_usb_lid.stl), [`out/v_stand.stl`](out/v_stand.stl) | Same sleek flangeless/tabless desktop USB-powered architecture as Model 4, sized for the **`20.0 × 20.0 × 1.2 mm` HLK-LD2410S + 5-pin `2.54 mm` female DuPont connector** (`86.8 × 32.8 × 29.4 mm` body — **38% narrower** than 18650 models, `19.5 mm` under-radar clearance, `22 × 22 × 1.2 mm` blind RF radome, calibrated `13.4 mm` panel-mount USB-C socket bay, and flush `-Y` mortises for the detachable **Inverted-V Stand (`v_stand.stl`)**). |
| **Model 6: `Aura-S v1` (`aura_v1` / `aura_s_v1`) — Award-Edition Horizon Stadium Monolith (`20 × 20 mm` HLK-LD2410S)** | [`out/aura_v1_base.stl`](out/aura_v1_base.stl), [`out/aura_v1_lid.stl`](out/aura_v1_lid.stl), [`out/aura_v1_stand.stl`](out/aura_v1_stand.stl) (also exported as `aura_s_v1_*` and `aura_s_*`) | Flagship architectural homeware monolith (`92.0 × 34.0 × 29.4 mm` true `R = 17.0 mm` full-radius stadium capsule) for the **`20.0 × 20.0 × 1.2 mm` HLK-LD2410S + 5-pin DuPont connector**, with a **hidden REAR (`Z = 0`) 3-zone clip-retention USB-C socket bay (`13.2 mm` clip collar + `13.4 mm` stem guide)**, `1.8 mm × 45°` sculpted front bevel, concentric **horizon shadow groove**, parting-line shadow reveal, and a beveled **Inverted-V (`ʌ`) floating pedestal (`aura_v1_stand.stl`)**. |
| **Model 7: `Aura-C v1` (`aura_c_v1`) — Award-Edition Horizon Stadium Monolith (`22 × 16 mm` HLK-LD2410C)** | [`out/aura_c_v1_base.stl`](out/aura_c_v1_base.stl), [`out/aura_c_v1_lid.stl`](out/aura_c_v1_lid.stl), [`out/aura_c_v1_stand.stl`](out/aura_c_v1_stand.stl) (also exported as `aura_c_*`) | Slimmer flagship architectural homeware monolith (`92.0 × 32.0 × 27.4 mm` true `R = 16.0 mm` full-radius stadium capsule) for the **`22.0 × 16.0 × 1.2 mm` HLK-LD2410C**, featuring the same hidden rear (`Z = 0`) 3-zone clip-retention USB-C socket bay (`13.2 mm` clip collar + `13.4 mm` stem guide), sculpted horizon bevels, `24 × 18 × 1.2 mm` blind RF radome, and a bespoke beveled **Inverted-V (`ʌ`) floating pedestal (`aura_c_v1_stand.stl`)**. |
| **Model 8: `Aura-S v2` (`aura_v2` / `aura_s_v2`) — Compact Stacked Direct-Solder Monolith (`20 × 20 mm` HLK-LD2410S)** | [`out/aura_v2_base.stl`](out/aura_v2_base.stl), [`out/aura_v2_lid.stl`](out/aura_v2_lid.stl), [`out/aura_v2_stand.stl`](out/aura_v2_stand.stl) (also exported as `aura_s_v2_*`) | Ultra-compact **stacked direct-solder** stadium pebble (**`64.0 × 34.0 × 23.4 mm`** — **30% shorter, 20% thinner, 45% smaller volume** than `Aura v1`!) that stacks the direct-soldered **`20.0 × 20.0 mm` HLK-LD2410S** (`Z = 15.9 .. 17.1 mm`) vertically above the **SuperMini nRF52840** (`Z = 5.4 .. 6.6 mm`) using a stepped amphitheater cradle (straight-down drop-in assembly, zero overhangs), paired with a **sculpted flush-alcove `+X` side-entry `13.2 / 13.4 mm` USB-C socket** (`X = +28.50 mm` recessed flat bezel seat with a `45°` architectural shadow-reveal halo so the oval bezel nests flush inside the `+X` stadium nose, leaving a 100% smooth `Z = 0` back face) and a compact beveled **Inverted-V (`ʌ`) floating pedestal (`aura_v2_stand.stl`)**. |
| **Model 9: `Aura-C v2` (`aura_c_v2`) — Compact Stacked Direct-Solder Monolith (`22 × 16 mm` HLK-LD2410C)** | [`out/aura_c_v2_base.stl`](out/aura_c_v2_base.stl), [`out/aura_c_v2_lid.stl`](out/aura_c_v2_lid.stl), [`out/aura_c_v2_stand.stl`](out/aura_c_v2_stand.stl) | Ultra-compact **stacked direct-solder** stadium pebble (**`64.0 × 32.0 × 23.4 mm`** — `2:1` stadium proportion, `R = 16.0 mm`) that stacks the direct-soldered **`22.0 × 16.0 mm` HLK-LD2410C** (`Z = 15.9 .. 17.1 mm`) vertically above the **SuperMini nRF52840** (`Z = 5.4 .. 6.6 mm`) alongside the **sculpted flush-alcove `+X` side-entry `13.2 / 13.4 mm` USB-C socket** and a compact beveled **Inverted-V (`ʌ`) floating pedestal (`aura_c_v2_stand.stl`)**. |
| **USB-C Socket Clip-Retention Fit-Test Gauge** | [`out/usbc_socket_fit_test.stl`](out/usbc_socket_fit_test.stl) | 4-station dual-orientation clip-retention test block pairing the calibrated **`13.4 × 5.8 mm` coaxial rear stem guide** with 4 clip-locking collar widths (**`12.6 mm`**, **`12.8 mm`**, **`13.0 mm`**, **`13.2 mm`** — calibrated winner, Station #4) across a **`1.10 mm` thin front locking lip** and **`16.8 mm` clip-expansion pocket**, with **both** a rear-entry (`Z = 0`, `Aura`) socket and a side-entry (`+X`, `ld2410c`/`ld2410s_usb`) socket at every station. |

---

## 1. Shared Internal Hardware & Wall-Joined Cradle Architecture

| Component | Nominal Envelope | Wall-Joined Cradle, Retention & Clearance Design |
|---|---|---|
| **Hi-Link HLK-LD2410S** (24 GHz 1T1R mmWave radar, Manual V1.2 §7 Fig. 7-1) + **5-Pin (`1×5`) Female DuPont Connector** | **`20.00 × 20.00 × 1.20 mm`** square PCB (`R = 2.00 mm` corners) + **`13.8 × 3.2 × 16.5 mm`** 5-pin female DuPont housing & wire bend on `+X` `J2` header | Monolithic wall-joined U-box tower (`RADAR_X = -19.5 mm, Y_ELEC = +10.4 mm, RADAR_RAIL_H = 19.5 mm`): `4.4 mm` `+Y` wall fused to the `+Y` outer wall, `3.65 mm` `-Y` wall fused to the `-X` `18650` saddle, continuous `3.8 mm` `-X` cross-wall, `0.45 mm` `45°` snap-in lips, and a `3.5 × 7.95 mm` `(+X, -Y)` corner buttress that leaves an **`18.65 mm` wide unobstructed `+X` exit channel (`Y = +5.35 .. +24.0 mm`)** and **`19.5 mm` vertical clearance** so the radar installs/removes with the 5-pin female DuPont connector attached. |
| **Blind RF Radome Window + Lid Radar Corner Bosses** (All 5 Lids) | **`22.0 × 22.0 mm`** (`24.0 × 18.0 mm` on Model 4) interior pocket (`RADOME_T = 1.20 mm`) + radar corner bosses | Leaves a uniform **`1.20 mm`** solid outer top wall (`< 0.2 dB` one-way loss at `24.125 GHz`, $\lambda_0 \approx 12.5\text{ mm}$) with a **`5.10 mm` (`~0.41 λ₀`) antenna air gap**. Corner bosses stop `0.30 mm` above the radar's non-header corners. No hold-down elements hang down over the SuperMini nRF52840 so internal wiring is completely unobstructed; the SuperMini is retained directly in the base cradle by 4 corner snap-hooks. |
| **SuperMini nRF52840** (Pro Micro form-factor BLE board) | **`33.0 × 18.0 × 1.2 mm`** (`24` through-hole pins along `±Y`, `B+`/`B-` pads at `-X`, USB-C at `+X`) | Tight `0.15 mm` pocket clearance (`BOARD_RAIL_H = 4.5 mm`) with `+Y` retainers (`4.45 mm` thick) fused directly to the `+Y` outer wall, `-Y` retainers (`3.85 mm` thick) + a `4.0 mm` central bridge fused into the battery bay buttress and `+X` `18650` saddle, and **4 cantilevered corner snap-hooks (`0.65 mm` overhang with `45°` entry bevels)**. Positioned at `BOARD_X = +20.5 mm` (Models 1 & 2) or `BOARD_X_VANITY = +24.0 mm` (Model 3). |
| **18650 Li-ion Cell + `10 × 10 mm` Contact Plates** | **`Ø18.4 × 65.0 mm`** flat-top cell + two **`10.0 × 10.0 × 0.5 mm`** nickel contact plates (`-` spring, `+` button) | Wall-joined end bulkheads (`7.1 mm` along X × `21.5 mm` along Y) fused to the `±X` and `-Y` outer walls (`5.70 mm` solid backing) and tied into `4.0 mm` cell saddles by continuous longitudinal buttress ribs. Features a **`10.50 × 10.50 mm` capture pocket** (`SLOT_W = 10.50 mm`, `45°` top entry funnel, **solid bottom stop ledge at `Z_SLOT_BOT = 8.45 mm` / `FLOOR + 6.05 mm`**) that automatically centers `10 × 10 mm` plates vertically on the `18650` axis (`AXIS_Z = 13.60 mm`), with a **`7.60 mm` central window** (`1.20 mm` lip overlap/side) and a **`5.0 mm` bottom solder-tab & `+Y` wire exit tunnel**. |

---

## 2. Detailed Variant Descriptions

### Model 1: Sealed Gasketed Wall-Mount (`base.stl`, `lid.stl`)
- **Outer Envelope**: `118.8 × 76.1 × 29.4 mm` (`82.0 × 48.0 × 24.0 mm` interior cavity).
- **Tongue-and-Groove Rim & Ingress Protection**: Continuous `2.20 × 1.50 mm` debossed perimeter groove in `base.stl` (`GROOVE_OFFSET = 3.60 mm`, `89.20 × 55.20 mm` centerline, `R = 4.00 mm`) mated directly by a concentric **`1.80 × 1.25 mm` embossed tongue rim on `lid.stl`** (`RIM_CLEAR = 0.20 mm` radial slip-fit clearance per side, `RIM_Z_CLEAR = 0.25 mm` bottom clearance so the lid flange seats flush at `Z = 26.40 mm`), compressed by 4× `M3 × 8 mm` stainless screws into `M3 × 5.7 × 4.6 mm` heat-set inserts (`SCREW_OFFSET = 6.4 mm`) located outside the sealed cavity.
- **Mounting**: Two `4.0 mm` thick `±X` wall-mount tabs with `Ø4.5 mm` clearance holes at `X = ±54.9 mm`.

### Model 2: Angled 45° Corner / Ceiling Snap-Fit (`corner_base.stl`, `corner_lid.stl`, `corner_bracket.stl`)
- **Outer Case Envelope**: `86.8 × 56.4 × 29.4 mm` (compact flangeless profile; no heat-set inserts or lid screws required).
- **Tool-less 4-Point Cantilever Snap-Fit**: `corner_lid` features a `2.0 mm` deep perimeter splash-guard lip with 4 outward snap beads (`X = ±22.0 mm, Y = ±24.15 mm`) that latch into matching internal receiver grooves in `corner_base` (`0.000 mm³` interference in the closed position), plus two `±X` fingernail/flathead pry slots (`8.0 × 0.9 mm`) for easy battery access.
- **45° Room-Corner / Ceiling Bracket (`corner_bracket.stl`)**:
  - Two orthogonal `90°` mounting wings tilted at `±45°` (with 4× `Ø4.2 mm` screw holes and flat surfaces for 3M VHB / Command strips) nest flush into any `90°` wall-to-wall corner or ceiling-to-wall junction, aiming the HLK-LD2410S antenna normal at **45° downward** into a `3 m³` bathroom.
  - Integral `±Y` C-channel jaws (`0.40 mm` clearance) capture the lower slide rails on `corner_base` (`Z = 0 .. 2.0 mm`) against a `+X` end stop so the sensor slides out tool-free for charging.

### Model 3: Freestanding Shelf / Vanity Pod with USB-C Pass-Through (`vanity_base.stl`, `vanity_lid.stl`)
- **Outer Envelope**: `86.8 × 54.4 × 29.4 mm`.
- **Upright Low-CG Shelf Posture**: A flat `72.0 × 29.4 mm` pedestal foot along the `-Y` exterior wall (`Y = -28.0 mm`, flush across both `vanity_base` and `vanity_lid`) lets the pod stand upright on a bathroom vanity, shelf, or cistern with the heavy 18650 cell at the bottom (`Y_BAT = -12.3 mm`) and the HLK-LD2410S facing horizontally into the room.
- **In-Place USB-C Recharging Port**: Aligns the SuperMini nRF52840 at `BOARD_X_VANITY = +24.0 mm` (`0.50 mm` from the `+X` cavity wall) behind a `9.6 × 3.8 mm` rounded USB-C pass-through slot and a `13.0 × 7.6 × 1.0 mm` exterior overmold counterbore (`Z_USBC = 9.7 mm`), braced at `-X` by dual wall-joined corner stops to absorb plug insertion force.

### Model 4 & Model 5: Sleek Desktop USB-Powered Pods (`ld2410c_*`, `ld2410s_usb_*`) + Detachable Inverted-V Stand (`v_stand.stl`)
- **Modern Tabless Desktop Pod Silhouette**:
  - **Model 4 (`HLK-LD2410C`, `22 × 16 mm`)**: **`86.8 × 28.8 × 27.4 mm`** (`82.0 × 24.0 × 22.0 mm` single-lane cavity — **45% narrower** with the `18650` battery bay eliminated).
  - **Model 5 (`HLK-LD2410S`, `20 × 20 mm`)**: **`86.8 × 32.8 × 29.4 mm`** (`82.0 × 28.0 × 24.0 mm` single-lane cavity — **38% narrower** than 18650 models, with `19.5 mm` under-radar clearance and an `18.85 mm` wide unobstructed `+X` exit channel for the 5-pin `2.54 mm` female DuPont connector).
  - Both models eliminate wall-mount screw tabs and protruding feet in favor of a clean, symmetrical rounded-pill silhouette finished with **`0.8 mm × 45°` front and rear perimeter bevels**.
- **Separate Slot-In Inverted-V (`ʌ`) Desktop Stand (`v_stand.stl`)**:
  - Elevates the horizontal pod **`16.0 mm` above the desk** on splayed `4.2 mm` inverted-V (`ʌ`) architectural legs (`58.0 × 25.4 mm` footprint) with a sculpted chevron cutout underneath.
  - Features **twin top tenon blades** (`X = ±7.5 mm`, `7.1 × 10.1 × 3.45 mm`, `0.15 mm`/side slip-fit clearance) that slot into matching **flush blind mortise pockets** in the `-Y` bottom wall of either `ld2410c_base` or `ld2410s_usb_base` (backed by a sealed internal boss so the cavity stays 100% enclosed even when used without the stand).
- **AliExpress 2-Pin Panel-Mount USB-C Socket Bay (`1005008559159734`) — 3-Zone Clip-Retention Architecture**: Moves the SuperMini `17.5 mm` away from the `+X` wall (`PCB X = -9.50 .. +23.50 mm`) to house the panel-mount USB-C socket (`USBC_SOCK_Z = 12.5 mm`) using a **3-zone clip-retention profile**:
  1. **Zone 1 (`d = 0.00 .. 1.10 mm`) — `13.6 × 6.0 mm` Lead-In Mouth + `13.2 × 5.8 mm` (`USBC_SOCK_CLIP_THROAT_W`) Thin `1.10 mm` Clip-Locking Collar**: Compresses the `±Y` spring clips during insertion and snaps cleanly into the connector's narrower locking waist right behind the bezel.
  2. **Zone 2 (`d = 1.10 .. 5.80 mm`) — `16.8 × 5.8 mm` Clip-Barb Expansion Chamber**: Steps sharply outward at `d = 1.10 mm` to form a positive `90°` locking shoulder where the clip barbs snap open.
  3. **Zone 3 (`d = 7.50 .. 13.80 mm`) — Support-Free `45°` Taper into Coaxial `13.4 × 5.8 mm` Rear Stem Guide Sleeve**: Steps back inward at `45°` (`d = 5.80 .. 7.50 mm`) to hug the rear half of the `14.0 mm` stem on all 4 sides at the calibrated **`13.4 × 5.8 mm`** fit so the connector cannot rock sideways or unhook under cable tug.
- **High-Retention Snap-Fit Lids (`ld2410c_lid.stl`, `ld2410s_usb_lid.stl`)**: Feature a snug `0.15 mm`/side perimeter lip (`2.6 mm` deep), 4× `15.0 mm` long chamfered snap beads with `0.45 mm` radial wall engagement per side, and zero lid hold-downs over the SuperMini so cabling never interferes with lid closure.

### Model 6 (`Aura-S v1` / `aura_v1`) & Model 7 (`Aura-C v1` / `aura_c_v1`): Award-Edition Horizon Stadium Monoliths (`aura_v1_*`, `aura_s_v1_*`, `aura_c_v1_*`)
- **Full-Radius Stadium Capsule Silhouettes**:
  - **`Aura-S v1` (`HLK-LD2410S`, `20 × 20 mm`)**: **`92.0 × 34.0 × 29.4 mm`** with continuous **`R = 17.0 mm` (`OUTER_W_AURA_S / 2`) semicircular ends**, `19.5 mm` under-radar clearance for the 5-pin `2.54 mm` female DuPont connector, and a `22 × 22 × 1.2 mm` blind RF radome.
  - **`Aura-C v1` (`HLK-LD2410C`, `22 × 16 mm`)**: **`92.0 × 32.0 × 27.4 mm`** with continuous **`R = 16.0 mm` (`OUTER_W_AURA_C / 2`) semicircular ends**, `17.5 mm` under-radar clearance for the `1.27 mm` 5-pin header + `1000 µF` capacitor, and a `24 × 18 × 1.2 mm` blind RF radome.
  - Both share a `1.8 mm × 45°` sculpted front bezel chamfer, a `1.4 mm × 45°` rear taper, a `0.5 mm × 45°` parting-line shadow reveal, and a concentric **`0.8 mm × 0.45 mm` recessed stadium horizon groove** framing the seamless matte radome facade.
- **Hidden Rear-Entry (`Z = 0`) 3-Zone Clip-Retention USB-C Socket Bay**: Rotates the AliExpress 2-Pin Panel-Mount USB-C Socket (`1005008559159734`) to the **rear (`Z = 0`) face** at `USBC_AURA_X = +32.0 mm` so the USB-C power cord exits straight out the back and is 100% invisible from the front and sides. Uses the calibrated **Station #4 3-zone clip-retention architecture** (`13.6 × 6.0 mm` entry lead-in at `Z = 0.00 .. 0.45 mm`, **`13.2 × 5.8 mm` clip-locking collar** up to `Z = 1.10 mm`, **`16.8 × 6.6 mm` 4-sided clip expansion chamber** at `Z = 1.10 .. 5.80 mm`, support-free `45°` inward taper at `Z = 5.80 .. 7.50 mm`, and **coaxial `13.4 × 5.8 mm` rear stem guide sleeve** up to `Z = 13.80 mm`) with `12.4 mm` of unobstructed vertical wire-exit clearance above the stem (`Z = 14.0 .. 26.4 mm`).
- **Sculptural Beveled Inverted-V (`ʌ`) Floating Pedestals (`aura_v1_stand.stl`, `aura_s_v1_stand.stl`, `aura_c_v1_stand.stl`)**: Poise each stadium monolith `16.0 mm` above the desk on splayed `58.0 mm` wide inverted-V legs accented by a `1.2 mm × 45°` front architectural bevel, locking into the underside of `aura_v1_base.stl` or `aura_c_v1_base.stl` via twin flush mortise-and-tenon blades (`X = ±7.5 mm`).

### Model 8 (`Aura-S v2` / `aura_v2`) & Model 9 (`Aura-C v2` / `aura_c_v2`): Ultra-Compact Stacked Direct-Solder Stadium Monoliths (`aura_v2_*`, `aura_s_v2_*`, `aura_c_v2_*`)
- **45% Smaller Stacked Stadium Architecture**:
  - **`Aura-S v2` (`HLK-LD2410S`, `20 × 20 mm` direct-soldered)**: **`64.0 × 34.0 × 23.4 mm`** (`R = 17.0 mm` stadium ends — **30% shorter and 20% thinner** than `Aura v1`), using a stepped amphitheater cradle (`|Y| = 9.30 mm` upper radar ledge outside the `|Y| = 9.15 mm` lower SuperMini pocket so the SuperMini drops straight down to `Z = 5.4 .. 6.6 mm` before the radar snaps into `Z = 15.9 .. 17.1 mm`).
  - **`Aura-C v2` (`HLK-LD2410C`, `22 × 16 mm` direct-soldered)**: **`64.0 × 32.0 × 23.4 mm`** (`R = 16.0 mm` stadium ends, `2:1` stadium proportion), using a support-free `~24°` corbelled upper cradle (`Z = 11.4 .. 15.9 mm`) over the lower SuperMini (`Z = 5.4 .. 6.6 mm`).
- **Sculpted Flush-Alcove `+X` Side-Entry USB-C Bay (`USBC_AURA_V2_X_SEAT = +28.50 mm`, `USBC_AURA_V2_Z = 11.20 mm`)**:
  - Leaves the entire `Z = 0` back face **100% smooth and unbroken**.
  - Carves a recessed flat vertical seating plane at `X = +28.50 mm` (`3.50 mm` inside the `+32.00 mm` `+X` stadium nose) framed by a `17.1 × 11.0 mm` oval bezel pocket that flares outward at `45°` into the curved stadium contour so the `2.0 mm` oval USB-C bezel (`X = +28.55 .. +30.55 mm`) nests completely flush inside the nose.
  - Uses the calibrated **Station #4 (`13.20 × 5.80 mm` clip-locking collar + `16.80 mm` clip expansion pocket + coaxial `13.40 × 5.80 mm` rear stem guide sleeve)** in an open-top interior U-cradle (`X = +14.30 .. +28.50 mm`) with `6.00 mm` of open wiring space (`X = +8.50 .. +14.50 mm`) to the SuperMini (`BOARD_AURA_V2_X = -8.0 mm`).
- **Compact Beveled Inverted-V (`ʌ`) Floating Pedestals (`aura_v2_stand.stl`, `aura_s_v2_stand.stl`, `aura_c_v2_stand.stl`)**: Tailored `50.0 × 19.4 mm` footprint with twin top tenons (`X = ±7.5 mm`, `Z = 4.2 .. 13.2 mm`) that slot into flush blind `-Y` mortises in `aura_v2_base.stl` and `aura_c_v2_base.stl`.

### USB-C Socket 4-Way Dual-Orientation Clip-Retention Fit-Test Gauge (`usbc_socket_fit_test.stl`)
- **4 Clip-Locking Collar Stations Paired with the Calibrated `13.4 × 5.8 mm` Rear Stem Sleeve**: Tests 4 clip-waist collar widths (`USBC_RETENTION_TEST_THROATS = (12.6, 12.8, 13.0, 13.2)` mm across the `1.10 mm` front locking lip, followed by the `16.8 mm` clip-expansion chamber and `13.4 × 5.8 mm` coaxial rear stem guide sleeve). Each station includes **both** a rear-entry (`Z = 0`, `Aura-S`/`Aura-C`) socket bay at `X = 18.0 mm` and a side-entry (`+X`, `ld2410c`/`ld2410s_usb`) socket bay at `X = 43.4 mm`:
  - **`12.6mm (13.4)`**: `12.6 × 5.8 mm` clip collar (`0.40 mm`/side interference), `13.4 × 5.8 mm` stem guide (`Firmest Lock`)
  - **`12.8mm (13.4)`**: `12.8 × 5.8 mm` clip collar (`0.30 mm`/side interference), `13.4 × 5.8 mm` stem guide (`Firm Lock`)
  - **`13.0mm (13.4)`**: `13.0 × 5.8 mm` clip collar (`0.20 mm`/side interference), `13.4 × 5.8 mm` stem guide (`Medium Lock`)
  - **`13.2mm (13.4)`** (**Station #4 — Calibrated Winner**): `13.2 × 5.8 mm` clip collar (`0.10 mm`/side interference), `13.4 × 5.8 mm` stem guide (**`Default` used in `aura_v1`, `aura_s_v1`, `aura_c_v1`, `aura_v2`, `aura_s_v2`, `aura_c_v2`, `ld2410s_usb`, `ld2410c`**)
- Once you test-fit your physical USB-C socket into `usbc_socket_fit_test.stl`, set `USBC_SOCK_CLIP_THROAT_W` in [`enclosure_variants.py`](enclosure_variants.py) to the winning collar width (`12.6`, `12.8`, `13.0`, or `13.2`).

---

## 3. Bill of Materials (BOM)

| Qty | Item | Models Used |
|---|---|---|
| 1 | **SuperMini nRF52840** (`33 × 18 mm` Pro Micro BLE board) | All (Models 1–9) |
| 1 | **Hi-Link HLK-LD2410S** (`20.0 × 20.0 × 1.2 mm` 24 GHz mmWave sensor; with `2.54 mm` 5-pin `J2` header + **5-pin female DuPont lead** on Models 1–3, 5, 6, or **direct-soldered** on Model 8 `Aura-S v2`) | Models 1, 2, 3, 5, 6 (`Aura-S v1`), 8 (`Aura-S v2`) |
| 1 | **Hi-Link HLK-LD2410C** (`22.0 × 16.0 × 1.2 mm` 24 GHz mmWave sensor; with 5-pin header on Models 4, 7, or **direct-soldered** on Model 9 `Aura-C v2`) | Models 4, 7 (`Aura-C v1`), 9 (`Aura-C v2`) |
| 1 | **2-Pin Panel-Mount USB-C 5A Female Socket with LED** ([AliExpress `1005008559159734`](https://www.aliexpress.com/item/1005008559159734.html), `16.5 × 10.4 mm` bezel, calibrated **`13.2 mm` collar + `13.4 × 5.8 mm` stem guide**) | Models 4, 5, 6 (`Aura-S v1`), 7 (`Aura-C v1`), 8 (`Aura-S v2`), 9 (`Aura-C v2`) |
| 1 | **Flat-top unprotected 18650 Li-ion cell** (`Ø18.4 × 65.0 mm`) | Models 1, 2, 3 |
| 1 pair | **18650 bare nickel-plated battery contact plates** (**`10 × 10 × 0.5 mm`**, 1× conical spring `-`, 1× dimple `+`) | Models 1, 2, 3 |
| 4 | **M3 × 5.7 × 4.6 mm brass heat-set inserts** + **4× M3 × 8 mm A2/A4 stainless screws** | Model 1 only |
| ~270 mm | **2.0 mm Ø EPDM or silicone O-ring cord** (or printed 95A TPU gasket loop) | Model 1 only |

---

## 4. Recommended Print Settings (Bambu Lab A1 / Bambu Studio)

- **Filament**: **PETG**, **ASA**, or **Matte PLA** in light/neutral color (avoid carbon-fiber or metallic-flake pigments over the `1.2 mm` radome).
- **Nozzle / Layer Height**: `0.4 mm` nozzle, **`0.20 mm` layer height** (renders the `1.20 mm` radome as 6 solid layers).
- **Wall Generator**: **Arachne** (mandatory so the `0.60 mm` 18650 contact-plate retaining lips print cleanly).
- **Supports**: **None (`Disable Support`)** — all exported `.stl` files are pre-oriented for support-free printing:
  - `base.stl`, `corner_base.stl`, `vanity_base.stl`, `ld2410c_base.stl`, `ld2410s_usb_base.stl`, `aura_v1_base.stl`, `aura_c_v1_base.stl`, `aura_v2_base.stl`, `aura_c_v2_base.stl`: upright on `Z = 0` underside.
  - `lid.stl`, `corner_lid.stl`, `vanity_lid.stl`, `ld2410c_lid.stl`, `ld2410s_usb_lid.stl`, `aura_v1_lid.stl`, `aura_c_v1_lid.stl`, `aura_v2_lid.stl`, `aura_c_v2_lid.stl`: flipped `180°` so the flat outer top surface lies directly on the build plate.
  - `v_stand.stl`, `aura_v1_stand.stl`, `aura_c_v1_stand.stl`, `aura_v2_stand.stl`, `aura_c_v2_stand.stl`: laid flat on their `+Z` rear face so the inverted-V (`ʌ`) chevron and twin top tenons extrude vertically with zero overhangs.
  - `corner_bracket.stl`: rotated `90°` onto its flat `-X` end face so the `90°` V-wings and C-channel jaws extrude vertically with zero overhangs.

---

## 5. Regenerating CAD Artifacts & Running Verification

```bash
cd enclosure
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Build all 9 models + fit test, export all .step/.stl files, and run boolean & radome verification:
.venv/bin/python verify.py

# Render all 34 2D cross-section PNGs to out/sections/*.png:
.venv/bin/python sections.py
```
