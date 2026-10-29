# Bathroom / Outdoor Presence Sensor Enclosures (3 Variants)

Parametric 3D-printable enclosures for the **SuperMini nRF52840 + Hi-Link HLK-LD2410S 24 GHz mmWave Radar + 18650** presence sensor, built with [CadQuery](https://cadquery.readthedocs.io/).

All three enclosure variants share the same verified internal architecture (`82.0 × 48.0 × 24.0 mm` cavity, `0.000 mm³` boolean interference across all solid pairs, `1.20 mm` blind RF radome with `5.10 mm` antenna air gap) and are ready to slice in **Bambu Studio** for the **Bambu Lab A1** (`0.4 mm` nozzle, `0.20 mm` layer height, **Arachne** wall generator, **zero supports**):

| Variant | Printable STL Files | Purpose & Mounting Style |
|---|---|---|
| **Model 1: Sealed Gasketed Wall-Mount** | [`out/base.stl`](out/base.stl), [`out/lid.stl`](out/lid.stl) | Steam-proof bathroom/outdoor enclosure (`118.8 × 76.1 × 29.4 mm`) with an exterior `2 mm` EPDM O-ring gasket groove, 4× `M3` heat-set inserts, and `±X` wall-mount screw tabs. |
| **Model 2: Angled 45° Corner / Ceiling Snap-Fit** | [`out/corner_base.stl`](out/corner_base.stl), [`out/corner_lid.stl`](out/corner_lid.stl), [`out/corner_bracket.stl`](out/corner_bracket.stl) | Compact flangeless snap-fit case (`86.8 × 56.4 × 29.4 mm`) that slides into a support-free **90° room-corner / ceiling bracket** holding the radar at a **45° downward pitch** into a `3 m³` bathroom. |
| **Model 3: Freestanding Vanity / Shelf Pod (USB-C)** | [`out/vanity_base.stl`](out/vanity_base.stl), [`out/vanity_lid.stl`](out/vanity_lid.stl) | Sleek freestanding pod (`86.8 × 54.4 × 29.4 mm`) that stands upright on its flat `-Y` pedestal foot (heavy 18650 cell at the bottom for low CG, radar facing horizontally into the room) with a precision **`+X` USB-C pass-through port** for in-place 18650 recharging. |

---

## 1. Shared Internal Hardware & RF Radome Architecture

| Component | Nominal Envelope | Cradle & Clearance Design |
|---|---|---|
| **Hi-Link HLK-LD2410S** (24 GHz 1T1R mmWave radar, Manual V1.2 §7 Fig. 7-1) | **`20.00 × 20.00 × 1.20 mm`** square PCB (`R = 2.00 mm` rounded corners; `J2` 5-pin `2.54 mm` header on `+X` edge) | Elevated in `+Y` lane (`RADAR_X = -19.5 mm, Y_ELEC = +10.4 mm`) on `RADAR_RAIL_H = 19.5 mm` rails (`0.8 mm` `±Y` ledges recessed `3.5 mm` from `+X` and `2.5 mm` from `-X`). Single `(+X, -Y)` corner stop leaves `J2` (`Pin 5 OT2` at `1.62 mm` .. `Pin 1 3V3` at `11.78 mm` from `+Y`) and the `19.5 mm` under-radar bay 100% open. |
| **Blind RF Radome Window** (All 3 Lids: `lid`, `corner_lid`, `vanity_lid`) | **`22.0 × 22.0 mm`** interior pocket (`RADOME_T = 1.20 mm`) | Leaves a uniform **`1.20 mm`** solid outer top wall (`< 0.2 dB` one-way loss at `24.125 GHz`, $\lambda_0 \approx 12.5\text{ mm}$) with a **`5.10 mm` (`~0.41 λ₀`) antenna-to-radome air gap**. |
| **SuperMini nRF52840** (Pro Micro form-factor BLE board) | **`33.0 × 18.0 × 1.2 mm`** (`24` through-hole pins along `±Y`, `B+`/`B-` pads at `-X`, USB-C at `+X`) | Supported on `BOARD_RAIL_H = 4.5 mm` corner pads (outside the `28.0 mm` `±Y` 12-pin rows and `-X` `B+`/`B-` pads) plus two inset longitudinal rails (`3.3 mm` inside `±Y` edges), leaving `2.0 mm` vertical clearance below `2.5 mm` through-hole solder tails. Positioned at `BOARD_X = +20.5 mm` (Models 1 & 2) or `BOARD_X_VANITY = +24.0 mm` (`0.5 mm` from `+X` wall in Model 3 for USB-C pass-through). |
| **18650 Li-ion Cell + Bare Leaf-Spring Plates** | **`Ø18.4 × 65.0 mm`** flat-top cell + two **`12.0 × 12.0 × 0.5 mm`** nickel plates | Retained in a `69.0 mm` bay (`Y_BAT = -12.3 mm`) with `0.60 mm` retaining lips (**slice with Arachne**) and `+` contact reach of **`0.50 mm >= 0.30 mm`** past the lip face. |

---

## 2. Detailed Variant Descriptions

### Model 1: Sealed Gasketed Wall-Mount (`base.stl`, `lid.stl`)
- **Outer Envelope**: `118.8 × 76.1 × 29.4 mm` (`82.0 × 48.0 × 24.0 mm` interior cavity).
- **Ingress Protection**: Continuous `2.2 × 1.5 mm` gasket groove (`GROOVE_OFFSET = 3.6 mm`) for `2 mm` EPDM/silicone O-ring cord or printed TPU gasket, compressed by 4× `M3 × 8 mm` stainless screws into `M3 × 5.7 × 4.6 mm` heat-set inserts (`SCREW_OFFSET = 6.4 mm`) located outside the sealed cavity.
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
- **In-Place USB-C Recharging Port**: Aligns the SuperMini nRF52840 at `BOARD_X_VANITY = +24.0 mm` (`0.50 mm` from the `+X` cavity wall) behind a `9.6 × 3.8 mm` rounded USB-C pass-through slot and a `13.0 × 7.6 × 1.0 mm` exterior overmold counterbore (`Z_USBC = 9.7 mm`), braced at `-X` by dual corner stops to absorb plug insertion force.

---

## 3. Bill of Materials (BOM)

| Qty | Item | Models Used |
|---|---|---|
| 1 | **SuperMini nRF52840** (`33 × 18 mm` Pro Micro BLE board) | All (1, 2, 3) |
| 1 | **Hi-Link HLK-LD2410S** (`20.0 × 20.0 × 1.2 mm` 24 GHz mmWave sensor + `2.54 mm` 5-pin `J2` header) | All (1, 2, 3) |
| 1 | **Flat-top unprotected 18650 Li-ion cell** (`Ø18.4 × 65.0 mm`) | All (1, 2, 3) |
| 1 pair | **18650 bare nickel-plated battery contact plates** (`12 × 12 × 0.5 mm`, 1× conical spring `-`, 1× dimple `+`) | All (1, 2, 3) |
| 4 | **M3 × 5.7 × 4.6 mm brass heat-set inserts** + **4× M3 × 8 mm A2/A4 stainless screws** | Model 1 only |
| ~270 mm | **2.0 mm Ø EPDM or silicone O-ring cord** (or printed 95A TPU gasket loop) | Model 1 only |

---

## 4. Recommended Print Settings (Bambu Lab A1 / Bambu Studio)

- **Filament**: **PETG** or **ASA** in light/neutral color (avoid carbon-fiber or metallic-flake pigments over the `1.2 mm` radome).
- **Nozzle / Layer Height**: `0.4 mm` nozzle, **`0.20 mm` layer height** (renders the `1.20 mm` radome as 6 solid layers).
- **Wall Generator**: **Arachne** (mandatory so the `0.60 mm` 18650 contact-plate retaining lips print cleanly).
- **Supports**: **None (`Disable Support`)** — all exported `.stl` files are pre-oriented for support-free printing:
  - `base.stl`, `corner_base.stl`, `vanity_base.stl`: upright on `Z = 0` underside.
  - `lid.stl`, `corner_lid.stl`, `vanity_lid.stl`: flipped `180°` so the flat outer top surface lies directly on the build plate.
  - `corner_bracket.stl`: rotated `90°` onto its flat `-X` end face so the `90°` V-wings and C-channel jaws extrude vertically with zero overhangs.

---

## 5. Regenerating CAD Artifacts & Running Verification

```bash
cd enclosure
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Build all 3 models, export all .step/.stl files, and run 45-pair boolean & radome verification:
.venv/bin/python verify.py

# Render all 16 2D cross-section PNGs to out/sections/*.png:
.venv/bin/python sections.py
```
