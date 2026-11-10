"""
Additional parametric enclosure variants for the presence sensor
(SuperMini nRF52840 + Hi-Link HLK-LD2410S 20x20 mm or HLK-LD2410C 22x16 mm 24 GHz radar + 18650 cell):

  Model 2 (Corner / Ceiling 45 deg Mount — HLK-LD2410S):
    - corner_base.stl / .step    : Compact flangeless snap-fit base with side slide rails
    - corner_lid.stl / .step     : Snap-fit lid with blind 22x22x1.2 mm RF radome pocket
    - corner_bracket.stl / .step : 90 deg room-corner / ceiling bracket holding the sensor at 45 deg

  Model 3 (Freestanding Vanity / Shelf Pod with USB-C Pass-Through — HLK-LD2410S):
    - vanity_base.stl / .step    : Upright shelf/vanity base (-Y stabilizer foot + USB-C port)
    - vanity_lid.stl / .step     : Matching snap-fit lid with flush -Y standing foot & 1.2 mm radome

  Model 4 (HLK-LD2410C Sleek Desktop USB-C Enclosure — 22x16 mm HLK-LD2410C):
    - ld2410c_base.stl / .step     : Sleek flangeless/tabless desktop USB-C base for 22x16 mm HLK-LD2410C
                                     with flush -Y mortise sockets for the detachable Inverted-V stand
    - ld2410c_lid.stl / .step      : Matching snap-fit lid with blind 24x18x1.2 mm RF radome pocket

  Model 5 (HLK-LD2410S Sleek Desktop USB-C Enclosure — 20x20 mm HLK-LD2410S):
    - ld2410s_usb_base.stl / .step : Sleek flangeless/tabless desktop USB-C base for 20x20 mm HLK-LD2410S
                                     with flush -Y mortise sockets for the detachable Inverted-V stand
    - ld2410s_usb_lid.stl / .step  : Matching snap-fit lid with blind 22x22x1.2 mm RF radome pocket

  Detachable Inverted-V Desktop Stand (fits both Model 4 & Model 5):
    - v_stand.stl / .step          : Separate modern inverted-V (ʌ) trestle stand that slots into the -Y mortises

  Model 6 — "Aura-S" (Award-Edition Horizon Stadium Monolith for 20x20 mm HLK-LD2410S):
    - aura_s_base.stl / .step      : Full-radius stadium unibody shell (92.0 x 34.0 x 26.4 mm, R=17 mm ends)
                                     with hidden REAR (Z=0, 13.4x5.8 mm) USB-C socket & flush -Y stand mortises
    - aura_s_lid.stl / .step       : Sculpted architectural stadium bezel with 45 deg chamfer, recessed horizon
                                     shadow-groove, and blind 22x22x1.2 mm RF radome (for 20x20 mm HLK-LD2410S)
    - aura_s_stand.stl / .step     : Sculptural tapered Inverted-V (ʌ) floating pedestal for Aura-S

  Model 7 — "Aura-C" (Award-Edition Horizon Stadium Monolith for 22x16 mm HLK-LD2410C):
    - aura_c_base.stl / .step      : Slimmer full-radius stadium unibody shell (92.0 x 32.0 x 24.4 mm, R=16 mm ends)
                                     with hidden REAR (Z=0, 13.4x5.8 mm) USB-C socket & flush -Y stand mortises
    - aura_c_lid.stl / .step       : Sculpted architectural stadium bezel with 45 deg chamfer, recessed horizon
                                     shadow-groove, and blind 24x18x1.2 mm RF radome (for 22x16 mm HLK-LD2410C)
    - aura_c_stand.stl / .step     : Sculptural tapered Inverted-V (ʌ) floating pedestal for Aura-C

  USB-C Socket 4-Way Fit-Test Gauge:
    - usbc_socket_fit_test.stl / .step : 4-station fit test (+0.5, +1.0, +1.5, +2.0 mm wider sockets)
"""

import math
from pathlib import Path

import cadquery as cq

import enclosure as e

# --------------------------------------------------------------------------------------
# Model 2 & Model 3 Parameters
# --------------------------------------------------------------------------------------

OUTER_R = e.INNER_R + e.WALL            # 4.4 mm compact outer corner radius

# Snap-fit retention (4 cantilever beads on lid lip + 4 receiver grooves in base inner wall)
# Uses tight 0.15 mm/side lip clearance, 2.6 mm deep lip, 15.0 mm long snap beads, and 0.45 mm
# radial wall engagement per side (4.5x deeper than before) for a secure, rattle-free lid lock.
SNAP_X_OFF = 22.0                       # snap catch X positions (+/- 22.0 mm)
SNAP_L = 15.0                           # snap bead length along X (15.0 mm per corner catch)
SNAP_ENGAGE = 0.45                      # radial catch engagement into the base inner wall per side (mm)
SNAP_BEAD_W = e.LIP_CLEAR + SNAP_ENGAGE # outward bead protrusion past lip outer face (0.60 mm)
SNAP_BEAD_H = 1.00                      # vertical height of snap bead
SNAP_Z_BOT = e.H - 2.05                 # snap bead bottom Z on 26.4 mm tall bases (24.35 mm)
PRY_W = 8.0                             # fingernail/screwdriver pry slot width (Y)
PRY_H = 0.9                             # pry slot height at top rim

# Model 2 slide rails (on corner_base Z=0..2.0 mm) and mating 45 deg / 90 deg corner bracket
RAIL_OUT = 1.8                          # outward rail width beyond +/-Y outer wall
RAIL_THK = 2.0                          # rail thickness on Z=0..2.0 mm build plate
RAIL_SPAN_X = 58.0                      # slide rail length along X (stop clears bracket +X end)
BRACKET_LEN_X = 52.0                    # bracket length along X (-26..+26 mm)
BRACKET_CLEAR = 0.40                    # clearance between bracket jaw and base rail
BRACKET_PLATE_T = 2.6                   # backing plate thickness (Z = -3.0..-0.4 mm)
CORNER_APEX_Z = -28.0                   # 90 deg V-wing apex Z coordinate below base
CORNER_WING_T = 3.2                     # thickness of the 45 deg / 90 deg mounting wings

# Model 3 Freestanding Vanity Pod (-Y standing foot + SuperMini USB-C pass-through at +X)
BOARD_X_VANITY = e.INNER_L / 2 - 0.5 - e.BOARD_L / 2   # +24.0 mm (+X board edge at +40.5 mm)
Z_USBC = e.FLOOR + e.BOARD_RAIL_H + e.BOARD_T + 1.6    # +9.7 mm (USB-C receptacle centre Z)
USBC_SLOT_W = 9.6                       # through-wall USB-C opening width (Y)
USBC_SLOT_H = 3.8                       # through-wall USB-C opening height (Z)
USBC_BOOT_W = 13.0                      # exterior USB-C cable overmold counterbore width (Y)
USBC_BOOT_H = 7.6                       # exterior USB-C cable overmold counterbore height (Z)
USBC_BOOT_D = 1.0                       # exterior counterbore depth into +X wall
VANITY_FOOT_OUT = 1.6                   # flat -Y standing foot extension beyond -Y outer wall
VANITY_FOOT_L = 72.0                    # flat -Y standing foot length along X

# Model 4 Hi-Link HLK-LD2410C (22.0 x 16.0 x 1.2 mm 24 GHz radar) — Compact Battery-Free Enclosure
# Designed for the AliExpress 2-Pin Panel-Mount USB-C Socket (item 1005008559159734: 16.5 x 10.4 x 2.0 mm
# front bezel, 12.0 x 5.35 x 14.0 mm rear snap-in body with 15.7 mm side retention wings) feeding 5V
# split to the SuperMini nRF52840 (moved away from the +X wall) and the HLK-LD2410C, with no 18650 cell.
INNER_L_C = 82.0                        # compact single-lane cavity length along X (mm)
INNER_W_C = 24.0                        # compact battery-free cavity width along Y (50% narrower than 48 mm)
DEPTH_C = 22.0                          # compact cavity depth along Z (mm)
H_C = e.FLOOR + DEPTH_C                 # 24.4 mm base height
OUTER_L_C = INNER_L_C + 2 * e.WALL      # 86.8 mm outer length (X)
OUTER_W_C = INNER_W_C + 2 * e.WALL      # 28.8 mm outer width (Y) — down from 52.8 mm!
Y_C = 0.0                               # single inline centerline for radar, SuperMini & USB-C socket
RADAR_C_L = 22.0                        # HLK-LD2410C PCB length along X (mm)
RADAR_C_W = 16.0                        # HLK-LD2410C PCB width along Y (mm)
RADAR_C_T = 1.2                         # HLK-LD2410C PCB thickness (mm)
RADAR_C_CORNER_R = 1.2                  # HLK-LD2410C PCB rounded corner radius (mm)
RADAR_C_X = -26.5                       # HLK-LD2410C center X (PCB spans X = -37.50 .. -15.50 mm)
RADAR_C_RAIL_H = 17.5                   # 17.5 mm under-radar clearance (places radar 5.1 mm below radome)
RADOME_C_L = 24.0                       # blind interior RF radome pocket length over 22x16 mm LD2410C
RADOME_C_W = 18.0                       # blind interior RF radome pocket width over 22x16 mm LD2410C
BOARD_C_X = +7.0                        # SuperMini center X (PCB X = -9.50..+23.50 mm, 17.5 mm clear of +X wall)

# AliExpress 2-Pin Panel-Mount USB-C Socket (1005008559159734) — 3-Zone Clip-Retention Architecture:
# - Rigid rear stem body (d = 5.8..14.0 mm): 13.0 x 5.35 mm -> guided by coaxial 13.4 x 5.8 mm rear sleeve
# - Spring clip barbs (d = 1.1..5.5 mm): expand into 16.8 x 6.6 mm interior locking pocket behind 1.10 mm lip
# - Clip-locking waist right behind bezel (d = 0.0..1.15 mm): captured by 1.10 mm thick locking collar
#   (13.6 x 6.0 mm outer lead-in funnel at d = 0..0.45 mm -> 13.2 x 5.8 mm clip-locking collar at d = 0.45..1.10 mm)
USBC_SOCK_Z = 12.5                      # socket center Z (clears +X mounting tab at Z=4.0 and lid at Z=24.4)
USBC_SOCK_BEZEL_W = 16.5                # exterior oval bezel width along Y (mm)
USBC_SOCK_BEZEL_H = 10.4                # exterior oval bezel height along Z (mm)
USBC_SOCK_BEZEL_T = 2.0                 # exterior oval bezel thickness along X (mm)
USBC_SOCK_STEM_L = 14.0                 # insertion stem length behind bezel along X (mm)
USBC_SOCK_STEM_W = 13.0                 # calibrated rigid rear stem width along Y (mm)
USBC_SOCK_STEM_H = 5.35                 # insertion stem height along Z (mm)
USBC_SOCK_WAIST_W = 12.3                # connector clip-locking waist width right behind bezel (d = 0..1.15 mm)
USBC_SOCK_WING_W = 15.8                 # uncompressed width across +/-Y spring clip barbs (mm)
USBC_SOCK_CUT_W = 13.4                  # calibrated rear stem guide channel width along Y (confirmed by 13.4 fit-test)
USBC_SOCK_CUT_H = 5.8                   # stem guide channel height along Z (5.35 + 0.45 mm clearance)
USBC_SOCK_CLIP_THROAT_W = 13.2          # calibrated clip-locking collar width along Y (Station #4 on retention test)
USBC_SOCK_PANEL_T = 1.10                # 1.10 mm locking lip thickness so clip barbs clear the lip and click open
USBC_SOCK_POCKET_END = 5.80             # axial depth where clip-expansion pocket transitions to 13.4 mm stem sleeve (mm)
USBC_SOCK_EXTRA_W = 0.0                 # additional width offset beyond calibrated 13.4 mm slot (mm)
USBC_RETENTION_TEST_THROATS = (12.6, 12.8, 13.0, 13.2)  # 4 clip-locking throat widths tested with 13.4 mm stem sleeve
AURA_VERSION = "v1"                     # Version tag for calibrated Aura v1 release (13.2 mm clip collar + 13.4 mm stem)

# Model 5 Hi-Link HLK-LD2410S (20.0 x 20.0 x 1.2 mm 24 GHz radar) — Compact Battery-Free USB-C Enclosure
# Shares the single-lane battery-free architecture of Model 4 (no 18650 cell, AliExpress panel-mount USB-C
# socket at +X, SuperMini at BOARD_C_X = +7.0 mm, flat -Y shelf foot, and +/-X wall-mount screw tabs),
# sized for the 20.0 x 20.0 x 1.2 mm HLK-LD2410S + 5-pin 2.54 mm female DuPont connector (19.5 mm under-board).
INNER_L_S = 82.0                        # compact single-lane cavity length along X (mm)
INNER_W_S = 28.0                        # compact battery-free cavity width along Y for 20x20 mm LD2410S (mm)
DEPTH_S = 24.0                          # cavity depth along Z for 19.5 mm under-radar DuPont clearance (mm)
H_S = e.FLOOR + DEPTH_S                 # 26.4 mm base height
OUTER_L_S = INNER_L_S + 2 * e.WALL      # 86.8 mm outer body length (X)
OUTER_W_S = INNER_W_S + 2 * e.WALL      # 32.8 mm outer body width (Y) — 38% narrower than 18650 models
RADAR_S_USB_X = -26.5                   # HLK-LD2410S center X in compact USB enclosure (PCB X = -36.5..-16.5 mm)

# Model 6 ("Aura-S", 20x20 mm HLK-LD2410S) & Model 7 ("Aura-C", 22x16 mm HLK-LD2410C) — Award-Edition Stadium Monoliths
OUTER_L_AURA = 92.0                     # full-radius stadium capsule length along X (mm)
OUTER_W_AURA = 34.0                     # Aura-S stadium height/width along Y for 20x20 mm HLK-LD2410S (mm)
OUTER_R_AURA = OUTER_W_AURA / 2 - 0.05  # 16.95 mm true semicircular stadium ends (Aura-S)
INNER_L_AURA = OUTER_L_AURA - 2 * e.WALL  # 87.2 mm stadium cavity length (X)
INNER_W_AURA = OUTER_W_AURA - 2 * e.WALL  # 29.2 mm stadium cavity width (Y, Aura-S)
INNER_R_AURA = INNER_W_AURA / 2 - 0.05  # 14.55 mm concentric stadium cavity radius (Aura-S)
DEPTH_AURA = 24.0                       # Aura-S cavity depth along Z (mm)
H_AURA = e.FLOOR + DEPTH_AURA           # 26.4 mm Aura-S base height
RADAR_AURA_X = -26.0                    # 20x20 mm HLK-LD2410S center X (PCB X = -36.0..-16.0 mm)
BOARD_AURA_X = +7.0                     # SuperMini nRF52840 center X (PCB X = -9.5..+23.5 mm)
USBC_AURA_X = +32.0                     # Rear-entry (Z=0) 13.4x5.8 mm USB-C socket center X

OUTER_W_AURA_C = 32.0                   # Aura-C slimmer stadium height/width along Y for 22x16 mm HLK-LD2410C (mm)
OUTER_R_AURA_C = OUTER_W_AURA_C / 2 - 0.05  # 15.95 mm true semicircular stadium ends (Aura-C)
INNER_W_AURA_C = OUTER_W_AURA_C - 2 * e.WALL  # 27.2 mm stadium cavity width (Y, Aura-C)
INNER_R_AURA_C = INNER_W_AURA_C / 2 - 0.05  # 13.55 mm concentric stadium cavity radius (Aura-C)
DEPTH_AURA_C = 22.0                     # Aura-C slimmer cavity depth along Z (mm)
H_AURA_C = e.FLOOR + DEPTH_AURA_C       # 24.4 mm Aura-C base height
RADAR_AURA_C_X = -25.5                  # 22x16 mm HLK-LD2410C center X (PCB X = -36.5..-14.5 mm)

# Model 8 ("Aura-S v2" / "aura_v2") & Model 9 ("Aura-C v2" / "aura_c_v2") — Compact Stacked Direct-Solder Monoliths
# Stacks the direct-soldered radar (upper tier, Z = 15.9..17.1 mm) vertically above the SuperMini nRF52840
# (lower tier, Z = 5.4..6.6 mm) alongside a sculpted flush-alcove +X side-entry 13.2/13.4 mm USB-C socket,
# shrinking length from 92.0 mm to 64.0 mm (-30%) and total height from 29.4 mm to 23.4 mm (-20%, ~45% less volume).
OUTER_L_AURA_V2 = 64.0                  # compact stacked stadium capsule length along X (down from 92.0 mm)
INNER_L_AURA_V2 = OUTER_L_AURA_V2 - 2 * e.WALL  # 59.2 mm compact stadium cavity length (X)
DEPTH_AURA_V2 = 18.0                    # compact stacked cavity depth along Z (down from 24.0 mm)
H_AURA_V2 = e.FLOOR + DEPTH_AURA_V2     # 20.4 mm base height (23.4 mm total height with 3.0 mm lid)
BOARD_V2_RAIL_H = 3.0                   # 3.0 mm under-SuperMini clearance for direct-soldered wire pads
RADAR_V2_RAIL_H = 13.5                  # places radar PCB at Z = 15.9..17.1 mm (7.5 mm above SuperMini shield, 5.1 mm below radome)
BOARD_AURA_V2_X = -8.0                  # lower-tier SuperMini center X (PCB X = -24.5..+8.5 mm; 6.0 mm clear of side USB-C stem)
RADAR_AURA_V2_X = -10.5                 # upper-tier radar center X (LD2410S X = -20.5..-0.5 mm; LD2410C X = -21.5..+0.5 mm)
USBC_AURA_V2_X_SEAT = OUTER_L_AURA_V2 / 2 - 3.50  # +28.50 mm recessed flat bezel seat inside +32.00 mm +X stadium nose
USBC_AURA_V2_Z = 11.2                   # vertical center of side-entry (+X) USB-C socket (centered on 20.4 mm base wall)
SNAP_X_AURA_V2 = 8.0                    # snap-catch X offset (+/- 8.0 mm) inside straight stadium wall
SNAP_L_AURA_V2 = 11.0                   # snap-bead length along X for compact 64 mm stadium
V_STAND_V2_BOT_W = 50.0                 # compact splayed footprint width for 64 mm Aura v2 stand (mm)
V_STAND_V2_DEPTH_Z = 19.4               # front-to-back stand depth tailored to 20.4 mm Aura v2 base (mm)
V_MORTISE_V2_Z0 = 4.2                   # Aura v2 mortise start Z (mm)
V_MORTISE_V2_L_Z = 9.0                  # Aura v2 mortise length along Z (Z = 4.2..13.2 mm)


def _yz_rrect_cut(
    x0: float, x_len: float, cy: float, cz: float, w_y: float, h_z: float
) -> cq.Workplane:
    """Extrude a filleted YZ rectangle along X for USB-C slot/counterbore."""
    return (
        cq.Workplane("YZ")
        .workplane(offset=x0)
        .center(cy, cz)
        .rect(w_y, h_z)
        .extrude(x_len)
        .edges("|X")
        .fillet(1.2)
    )


def _snap_bead_x(
    cx: float, length_x: float, inner_w: float, sy: int, z_bot: float
) -> cq.Workplane:
    """Chamfered support-free snap bead along X with 0.45 mm radial wall lock and 45 deg entry/exit ramps."""
    y_root = sy * (inner_w / 2 - e.LIP_CLEAR - 0.15)
    y_tip = sy * (inner_w / 2 + SNAP_ENGAGE)
    z0 = z_bot
    z1 = z_bot + 0.35
    z2 = z_bot + SNAP_BEAD_H - 0.25
    z3 = z_bot + SNAP_BEAD_H
    pts = [(y_root, z0), (y_tip, z1), (y_tip, z2), (y_root, z3)]
    return cq.Workplane("YZ").workplane(offset=cx - length_x / 2).polyline(pts).close().extrude(length_x)


def _add_snap_receivers_generic(
    base: cq.Workplane, inner_w: float, outer_l: float, base_h: float
) -> cq.Workplane:
    """Cut 4 tight-tolerance internal snap-catch receiver grooves on +/-Y walls and 2 pry slots on +/-X rim."""
    groove_l = SNAP_L + 1.0
    groove_h = SNAP_BEAD_H + 0.24
    groove_z = (base_h - 2.05) - 0.12
    groove_depth_y = SNAP_ENGAGE + 0.25
    for sx in (-1, 1):
        for sy in (-1, 1):
            gy = sy * (inner_w / 2 + (groove_depth_y / 2 - 0.10))
            base = base.cut(e.box(groove_l, groove_depth_y, groove_h, sx * SNAP_X_OFF, gy, groove_z))
        px = sx * (outer_l / 2 - 0.6)
        base = base.cut(e.box(1.4, PRY_W, PRY_H + 0.1, px, 0.0, base_h - PRY_H))
    return base


def _add_snap_receivers(base: cq.Workplane) -> cq.Workplane:
    """Cut 4 internal snap-catch receiver grooves on +/-Y walls and 2 pry slots on +/-X rim."""
    return _add_snap_receivers_generic(base, e.INNER_W, e.OUTER_L, e.H)


def make_snap_lid(with_vanity_foot: bool = False, board_x: float = e.BOARD_X) -> cq.Workplane:
    """Build compact flangeless snap-fit lid with blind 22x22x1.2 mm RF radome & radar corner bosses."""
    lid = e.rrect(e.OUTER_L, e.OUTER_W, OUTER_R, e.H, e.LID_T)
    if with_vanity_foot:
        foot_y = -e.OUTER_W / 2 - VANITY_FOOT_OUT / 2 + 1.0
        foot = e.box(VANITY_FOOT_L, VANITY_FOOT_OUT + 2.0, e.LID_T, 0.0, foot_y, e.H)
        lid = lid.union(foot.edges("|Z").fillet(1.5))

    lip_l, lip_w = e.INNER_L - 2 * e.LIP_CLEAR, e.INNER_W - 2 * e.LIP_CLEAR
    lip = (
        e.rrect(lip_l, lip_w, max(e.INNER_R - e.LIP_CLEAR, 0.5), e.H - e.LIP_H, e.LIP_H)
        .cut(e.rrect(lip_l - 2 * e.LIP_T, lip_w - 2 * e.LIP_T, 0.5, e.H - e.LIP_H - 1, e.LIP_H + 2))
    )
    lid = lid.union(lip)

    # 4 outward chamfered snap beads on the +/-Y lip faces (0.45 mm wall engagement per side)
    for sx in (-1, 1):
        for sy in (-1, 1):
            lid = lid.union(_snap_bead_x(sx * SNAP_X_OFF, SNAP_L, e.INNER_W, sy, SNAP_Z_BOT))

    # Blind interior pocket above HLK-LD2410S leaving uniform RADOME_T = 1.20 mm solid top skin
    radome_pocket = e.box(e.RADOME_L, e.RADOME_W, e.RADOME_DEPTH + 0.1, e.RADAR_X, e.Y_RADAR, e.H - 0.1)
    lid = lid.cut(radome_pocket)
    return e._add_lid_holddowns(lid, board_x=board_x)


# --------------------------------------------------------------------------------------
# Model 2: Angled 45 deg Corner / Ceiling Snap-Fit Enclosure + Bracket
# --------------------------------------------------------------------------------------

def make_corner_base() -> cq.Workplane:
    """Compact snap-fit base with lower +/-Y slide rails for the 45 deg corner bracket."""
    base = e.rrect(e.OUTER_L, e.OUTER_W, OUTER_R, 0.0, e.H)
    for sy in (-1, 1):
        ry = sy * (e.OUTER_W / 2 + RAIL_OUT / 2 - 0.5)
        rail = e.box(RAIL_SPAN_X, RAIL_OUT + 1.0, RAIL_THK, 0.0, ry, 0.0)
        stop = e.box(2.4, RAIL_OUT + 1.0, RAIL_THK + 1.8, RAIL_SPAN_X / 2 - 1.2, ry, 0.0)
        base = base.union(rail).union(stop)

    base = base.cut(e.rrect(e.INNER_L, e.INNER_W, e.INNER_R, e.FLOOR, e.DEPTH + 1.0))
    base = _add_snap_receivers(base)
    base = e._add_battery_bay(base)
    base = e._add_board_cradle(base)
    base = e._add_radar_cradle(base)
    return base


def make_corner_lid() -> cq.Workplane:
    """Compact snap-fit lid with blind 1.20 mm RF radome pocket and PCB hold-downs for Model 2."""
    return make_snap_lid(with_vanity_foot=False, board_x=e.BOARD_X)


def make_corner_bracket() -> cq.Workplane:
    """Support-free 90 deg room-corner / ceiling bracket holding corner_base at 45 deg."""
    z_top = -BRACKET_CLEAR
    z_bot = z_top - BRACKET_PLATE_T
    jaw_in_y = e.OUTER_W / 2 + RAIL_OUT + BRACKET_CLEAR
    jaw_out_y = jaw_in_y + 2.2
    lip_in_y = e.OUTER_W / 2 + BRACKET_CLEAR
    lip_z_bot = RAIL_THK + BRACKET_CLEAR
    lip_z_top = lip_z_bot + 1.4

    # Cradle backing plate + +/-Y C-channel jaws
    br = e.box(BRACKET_LEN_X, 2 * jaw_out_y, BRACKET_PLATE_T, 0.0, 0.0, z_bot)
    for sy in (-1, 1):
        wall_y = sy * (jaw_in_y + 1.1)
        br = br.union(e.box(BRACKET_LEN_X, 2.2, lip_z_top - z_bot, 0.0, wall_y, z_bot))
        lip_w = jaw_out_y - lip_in_y
        lip_y = sy * (lip_in_y + lip_w / 2)
        br = br.union(e.box(BRACKET_LEN_X, lip_w, lip_z_top - lip_z_bot, 0.0, lip_y, lip_z_bot))

    # 90 deg orthogonal V-wings tilted at 45 deg below the cradle backing plate + center web
    span_z = z_bot - CORNER_APEX_Z          # 25.0 mm vertical drop (= 25.0 mm Y run at 45 deg)
    pts_outer = [
        (-span_z - CORNER_WING_T * math.sqrt(2), z_bot),
        (0.0, CORNER_APEX_Z - CORNER_WING_T * math.sqrt(2)),
        (span_z + CORNER_WING_T * math.sqrt(2), z_bot),
        (span_z, z_bot),
        (0.0, CORNER_APEX_Z),
        (-span_z, z_bot),
    ]
    v_wings = (
        cq.Workplane("YZ")
        .workplane(offset=-BRACKET_LEN_X / 2)
        .polyline(pts_outer)
        .close()
        .extrude(BRACKET_LEN_X)
    )
    web = e.box(BRACKET_LEN_X, 3.2, span_z + 0.5, 0.0, 0.0, CORNER_APEX_Z)
    br = br.union(v_wings).union(web)

    # Four Ø4.2 mm mounting screw holes perpendicular to the two 45 deg corner wings
    for sx in (-1, 1):
        for sy in (-1, 1):
            mid_y = sy * (span_z * 0.52)
            mid_z = CORNER_APEX_Z + span_z * 0.52
            hole = (
                cq.Workplane("XY")
                .transformed(offset=(sx * 15.0, mid_y, mid_z), rotate=(sy * 45.0, 0.0, 0.0))
                .circle(2.1)
                .extrude(20.0, both=True)
            )
            br = br.cut(hole)
    return br


# --------------------------------------------------------------------------------------
# Model 3: Freestanding Shelf / Vanity Pod with USB-C Pass-Through
# --------------------------------------------------------------------------------------

def make_vanity_base() -> cq.Workplane:
    """Freestanding shelf/vanity base with flat -Y foot and +X USB-C pass-through port."""
    base = e.rrect(e.OUTER_L, e.OUTER_W, OUTER_R, 0.0, e.H)
    foot_y = -e.OUTER_W / 2 - VANITY_FOOT_OUT / 2 + 1.0
    foot = e.box(VANITY_FOOT_L, VANITY_FOOT_OUT + 2.0, e.H, 0.0, foot_y, 0.0).edges("|Z").fillet(1.5)
    base = base.union(foot)

    base = base.cut(e.rrect(e.INNER_L, e.INNER_W, e.INNER_R, e.FLOOR, e.DEPTH + 1.0))
    base = _add_snap_receivers(base)
    base = e._add_battery_bay(base)
    base = e._add_board_cradle(base, board_x=BOARD_X_VANITY, open_pos_x=True)
    base = e._add_radar_cradle(base)

    # Precision USB-C pass-through slot + exterior cable overmold counterbore on +X wall
    slot_cut = _yz_rrect_cut(e.INNER_L / 2 - 1.0, e.WALL + 2.0, e.Y_BRD, Z_USBC, USBC_SLOT_W, USBC_SLOT_H)
    boot_cut = _yz_rrect_cut(
        e.OUTER_L / 2 - USBC_BOOT_D, USBC_BOOT_D + 1.0, e.Y_BRD, Z_USBC, USBC_BOOT_W, USBC_BOOT_H
    )
    return base.cut(slot_cut).cut(boot_cut)


def make_vanity_lid() -> cq.Workplane:
    """Snap-fit lid for Model 3 with flush -Y standing foot, 1.20 mm radome, and PCB hold-downs."""
    return make_snap_lid(with_vanity_foot=True, board_x=BOARD_X_VANITY)


def make_vanity_dummies() -> dict[str, cq.Workplane]:
    """Internal dummies at BOARD_X_VANITY plus external USB-C charging plug dummy."""
    dm = e.make_dummies(board_x=BOARD_X_VANITY)
    tongue = e.box(6.5, 8.4, 2.6, e.INNER_L / 2 + 1.0, e.Y_BRD, Z_USBC - 1.3)
    overmold = e.box(14.0, 11.4, 6.0, e.OUTER_L / 2 + 6.4, e.Y_BRD, Z_USBC - 3.0)
    dm["usb_c_plug"] = tongue.union(overmold)
    return dm


# --------------------------------------------------------------------------------------
# Model 4: Hi-Link HLK-LD2410C (22x16 mm) Compact Battery-Free Enclosure with Panel USB-C Socket
# --------------------------------------------------------------------------------------

def _add_snap_receivers_c(base: cq.Workplane) -> cq.Workplane:
    """Cut 4 internal snap-catch receiver grooves on +/-Y walls and 2 pry slots on +/-X rim (compact Model 4)."""
    return _add_snap_receivers_generic(base, INNER_W_C, OUTER_L_C, H_C)


def _add_radar_c_cradle(base: cq.Workplane) -> cq.Workplane:
    """Monolithic wall-joined radar tower for 22.0 x 16.0 mm HLK-LD2410C in compact 24 mm wide cavity."""
    z_top = e.FLOOR + RADAR_C_RAIL_H + RADAR_C_T            # 21.10 mm
    stop_h = RADAR_C_RAIL_H + RADAR_C_T + 1.05              # 19.75 mm (Z_max = 22.15 mm)
    body_h = (H_C - e.LIP_H - 0.4) - e.FLOOR                # 19.00 mm (clears 2.6 mm lid lip at Z = 21.80 mm)
    rail_l = RADAR_C_L - e.RADAR_RECESS_NEG_X - e.RADAR_RECESS_POS_X
    rail_cx = RADAR_C_X + (e.RADAR_RECESS_NEG_X - e.RADAR_RECESS_POS_X) / 2
    y_in = RADAR_C_W / 2 + e.BOARD_CLEAR                    # 8.15 mm (3.85 mm solid wall to +/-12.0 mm outer walls)

    # 1. +/-Y Side Walls: 3.85 mm thick solid blocks fused directly to BOTH -Y and +Y outer enclosure walls
    for sy in (-1, 1):
        y_wall = sy * y_in
        y_ledge = sy * (y_in - e.RADAR_LEDGE)
        y_outer = sy * (INNER_W_C / 2)
        base = base.union(e.box(rail_l, abs(y_outer - y_ledge), RADAR_C_RAIL_H,
                                rail_cx, (y_outer + y_ledge) / 2, e.FLOOR))
        base = base.union(e.box(rail_l, abs(y_outer - y_wall), body_h,
                                rail_cx, (y_outer + y_wall) / 2, e.FLOOR))
        base = base.union(e.box(rail_l, 1.35, stop_h, rail_cx, y_wall + sy * 0.675, e.FLOOR))
        base = base.union(e._snap_hook_x(rail_cx, 9.0, y_wall, sy, z_top, e.RADAR_SNAP_OVERHANG))

    # 2. -X End Wall: 3.35 mm solid cross-wall fused directly to -X, -Y, and +Y outer enclosure walls
    neg_x_in = RADAR_C_X - RADAR_C_L / 2 - e.BOARD_CLEAR    # -37.65 mm
    neg_x_w = INNER_L_C / 2 + neg_x_in                      # 3.35 mm
    base = base.union(e.box(neg_x_w, INNER_W_C, body_h, -INNER_L_C / 2 + neg_x_w / 2, Y_C, e.FLOOR))
    base = base.union(e.box(1.35, INNER_W_C - 4.4, stop_h, neg_x_in - 0.675, Y_C, e.FLOOR))

    # 3. (+X, +/-Y) Corner L-Buttresses (leave 10.0 mm central +X channel Y = -5.0..+5.0 mm for 5-pin 1.27 mm header)
    pos_x_in = RADAR_C_X + RADAR_C_L / 2 + e.BOARD_CLEAR    # -15.35 mm
    ext_x = e.RADAR_RECESS_POS_X + e.BOARD_CLEAR
    buttress_w_y = INNER_W_C / 2 - 5.0                      # 7.0 mm (Y = +/-5.0 .. +/-12.0 mm)
    for sy in (-1, 1):
        by_full = sy * (INNER_W_C / 2 - buttress_w_y / 2)
        by_stop = sy * ((INNER_W_C / 2 - 2.2 + 5.0) / 2)
        bw_stop = (INNER_W_C / 2 - 2.2) - 5.0
        base = base.union(e.box(ext_x, buttress_w_y, RADAR_C_RAIL_H, pos_x_in - ext_x / 2, by_full, e.FLOOR))
        base = base.union(e.box(1.8, bw_stop, stop_h, pos_x_in + 0.9, by_stop, e.FLOOR))
    return base


def _add_board_c_cradle(
    base: cq.Workplane, inner_w: float = INNER_W_C, board_x: float = BOARD_C_X
) -> cq.Workplane:
    """Wall-joined SuperMini nRF52840 cradle at board_x fused to both -Y and +Y outer walls."""
    z_top = e.FLOOR + e.BOARD_RAIL_H + e.BOARD_T            # 8.10 mm
    stop_h = e.BOARD_RAIL_H + e.BOARD_T + e.STOP_ABOVE      # 7.50 mm (Z_max = 9.90 mm)
    end_pad_l = (e.BOARD_L - e.BOARD_PIN_ROW_L) / 2 - 0.2   # 2.3 mm
    end_pad_w = 3.4
    stop_t = 2.8

    # Central cross-tie stiffening the two inset rails
    base = base.union(e.box(3.2, e.BOARD_W - 2 * e.BOARD_PIN_SPAN_Y - 2.0, e.BOARD_RAIL_H, board_x, Y_C, e.FLOOR))

    for sy in (-1, 1):
        inset_y = Y_C + sy * (e.BOARD_W / 2 - e.BOARD_PIN_SPAN_Y - 1.8)
        base = base.union(e.box(e.BOARD_L - 10.0, e.RAIL_W, e.BOARD_RAIL_H, board_x, inset_y, e.FLOOR))
        y_in = Y_C + sy * (e.BOARD_W / 2 + e.BOARD_CLEAR)   # +/-9.15 mm
        y_out = sy * (inner_w / 2)                          # fuses directly to +/-Y outer wall
        y_w = abs(y_out - y_in)
        for sx in (-1, 1):
            px = board_x + sx * (e.BOARD_L / 2 - end_pad_l / 2)
            py = Y_C + sy * (e.BOARD_W / 2 - end_pad_w / 2)
            base = base.union(e.box(end_pad_l, end_pad_w, e.BOARD_RAIL_H, px, py, e.FLOOR))
            sxp_y = board_x + sx * (e.BOARD_L / 2 + e.BOARD_CLEAR - e.STOP_W / 2)
            base = base.union(e.box(e.STOP_W, y_w, stop_h, sxp_y, (y_in + y_out) / 2, e.FLOOR))
            base = base.union(e._snap_hook_x(px, end_pad_l, y_in, sy, z_top, e.BOARD_SNAP_OVERHANG))
            # Corner X stops (leave 10.0 mm central channel Y = -5.0..+5.0 mm open for radar & USB-C wires)
            sxp = board_x + sx * (e.BOARD_L / 2 + e.BOARD_CLEAR + stop_t / 2)
            syp = Y_C + sy * (e.BOARD_W / 2 + e.BOARD_CLEAR - e.STOP_W / 2)
            base = base.union(e.box(stop_t, e.STOP_W, stop_h, sxp, syp, e.FLOOR))
    return base


def _add_usbc_socket_bay(
    base: cq.Workplane,
    inner_l: float = INNER_L_C,
    inner_w: float = INNER_W_C,
    extra_w: float = USBC_SOCK_EXTRA_W,
    cy: float = Y_C,
    throat_w: float | None = None,
) -> cq.Workplane:
    """Add 3-zone clip-retention bay (lead-in funnel + 1.1 mm locking collar + clip pocket + 13.4 mm coaxial stem sleeve)."""
    outer_l = inner_l + 2 * e.WALL
    x_out = outer_l / 2
    cut_w = USBC_SOCK_CUT_W + extra_w                       # 13.4 mm rear coaxial stem guide width
    lock_w = (USBC_SOCK_CLIP_THROAT_W + extra_w) if throat_w is None else throat_w
    wing_recess_w = USBC_SOCK_WING_W + 1.0 + extra_w        # 16.8 mm snap-clip expansion pocket width

    # 1. Two floor-joined under-stem support rails (X = x_out - 13.4 .. x_out - 1.1 mm, Y = cy +/- 3.8 mm, Z = FLOOR..9.65 mm)
    stem_bot_z = USBC_SOCK_Z - USBC_SOCK_STEM_H / 2         # 9.825 mm
    rail_h = (stem_bot_z - 0.175) - e.FLOOR                 # 7.25 mm
    rail_x0 = x_out - 13.4
    rail_x1 = x_out - USBC_SOCK_PANEL_T
    rail_len = rail_x1 - rail_x0
    rail_cx = (rail_x0 + rail_x1) / 2
    cheek_z_h = USBC_SOCK_Z + 3.2 - e.FLOOR
    for sy in (-1, 1):
        base = base.union(e.box(rail_len, 2.2, rail_h, rail_cx, cy + sy * 3.8, e.FLOOR))
        # Side guide cheeks fused to +/-Y walls & +X wall (stepped inward to lock_w/2 so 3-zone cuts form exact walls)
        cheek_in_y = lock_w / 2 - 0.1
        cheek_w = max(inner_w / 2 - cheek_in_y, 2.2)
        cheek_cy = cy + sy * (cheek_in_y + cheek_w / 2)
        base = base.union(e.box(13.4, cheek_w, cheek_z_h, x_out - 13.4 / 2, cheek_cy, e.FLOOR))

    # 2. Zone 1A: Outer entry lead-in mouth (d = 0.00..0.45 mm, 13.6 x 6.0 mm) for effortless connector alignment
    mouth_cut = (
        cq.Workplane("YZ")
        .workplane(offset=x_out - 0.45)
        .center(cy, USBC_SOCK_Z)
        .rect(cut_w + 0.2, USBC_SOCK_CUT_H + 0.2)
        .extrude(1.0)
        .edges("|X")
        .fillet(0.5)
    )
    # 3. Zone 1B: Clip-locking collar (d = 0.45..1.10 mm, lock_w x 5.8 mm) that snaps into the connector's bezel waist
    collar_cut = (
        cq.Workplane("YZ")
        .workplane(offset=x_out - USBC_SOCK_PANEL_T - 0.1)
        .center(cy, USBC_SOCK_Z)
        .rect(lock_w, USBC_SOCK_CUT_H)
        .extrude(USBC_SOCK_PANEL_T + 0.5)
        .edges("|X")
        .fillet(0.5)
    )
    # 4. Zone 2: Interior snap-clip expansion chamber (d = 1.10..5.80 mm, 16.8 x 5.8 mm) with 90 deg locking shoulder
    pocket_len = USBC_SOCK_POCKET_END - USBC_SOCK_PANEL_T   # 4.70 mm
    pocket_cx = x_out - USBC_SOCK_PANEL_T - pocket_len / 2
    wing_recess = e.box(
        pocket_len,
        wing_recess_w,
        USBC_SOCK_CUT_H,
        pocket_cx,
        cy,
        USBC_SOCK_Z - USBC_SOCK_CUT_H / 2,
    )
    # 5. Zone 3: Coaxial 13.4 x 5.8 mm rear stem guide sleeve (d = 5.80..14.20 mm) with 45 deg lead-in taper
    taper_cut = (
        cq.Workplane("YZ")
        .workplane(offset=x_out - USBC_SOCK_POCKET_END + 0.05)
        .center(cy, USBC_SOCK_Z)
        .rect(wing_recess_w, USBC_SOCK_CUT_H)
        .workplane(offset=-1.20)
        .rect(cut_w, USBC_SOCK_CUT_H)
        .loft()
    )
    stem_guide_cut = (
        cq.Workplane("YZ")
        .workplane(offset=x_out - 14.5)
        .center(cy, USBC_SOCK_Z)
        .rect(cut_w, USBC_SOCK_CUT_H)
        .extrude(14.5 - USBC_SOCK_POCKET_END + 0.2)
        .edges("|X")
        .fillet(0.5)
    )
    return base.cut(mouth_cut).cut(collar_cut).cut(wing_recess).cut(taper_cut).cut(stem_guide_cut)


# Detachable Inverted-V (ʌ) Desktop Stand & Flush -Y Mortise-and-Tenon Interface (Models 4 & 5)
V_STAND_H = 16.0                        # vertical lift of the pod above the desktop (mm)
V_STAND_TOP_W = 28.0                    # upper cradle width along X (-14.0..+14.0 mm)
V_STAND_BOT_W = 58.0                    # splayed desktop footprint width along X (-29.0..+29.0 mm)
V_STAND_DEPTH_Z = 25.4                  # front-to-back stand depth along Z (mm)
V_STAND_LEG_T = 4.2                     # thickness of the splayed inverted-V legs & top bridge (mm)
V_MORTISE_X_OFF = 7.5                   # twin mortise X centers (+/- 7.5 mm, symmetric around X = 0)
V_MORTISE_W_X = 7.4                     # each mortise slot width along X (mm)
V_MORTISE_D_Y = 3.6                     # blind mortise slot depth into -Y bottom wall (mm)
V_MORTISE_L_Z = 10.4                    # mortise slot length along Z (Z = 5.8..16.2 mm)
V_MORTISE_Z0 = 5.8                      # mortise slot start Z (mm)
V_TENON_CLEAR = 0.15                    # slip-fit clearance per side between stand tenon and base mortise (mm)
DESK_CHAMFER = 0.8                      # 45 deg modern outer edge bevel on desktop pods (mm)


def _add_v_stand_mortise(
    base: cq.Workplane,
    outer_w: float,
    mortise_z0: float = V_MORTISE_Z0,
    mortise_l_z: float = V_MORTISE_L_Z,
    y_boss_in: float = -9.20,
) -> cq.Workplane:
    """Add internal sealed backing boss & cut 2 flush blind mortise slots in the -Y bottom wall for the V-stand."""
    y_out = -outer_w / 2
    boss_h_y = y_boss_in - (y_out + e.WALL - 0.4)
    if boss_h_y > 0:
        boss_cy = (y_out + e.WALL - 0.4 + y_boss_in) / 2
        base = base.union(
            e.box(V_STAND_TOP_W, boss_h_y, mortise_z0 + mortise_l_z + 1.8 - e.FLOOR, 0.0, boss_cy, e.FLOOR)
        )
    # Cut two symmetrical blind mortise pockets into the flush -Y bottom face (leaves >=1.6 mm sealed inner wall)
    for sx in (-1, 1):
        slot = e.box(
            V_MORTISE_W_X,
            V_MORTISE_D_Y + 0.2,
            mortise_l_z,
            sx * V_MORTISE_X_OFF,
            y_out + (V_MORTISE_D_Y - 0.2) / 2,
            mortise_z0,
        )
        base = base.cut(slot)
    return base


def make_v_stand(
    outer_w: float = OUTER_W_S,
    depth_z: float = V_STAND_DEPTH_Z,
    bot_w: float = V_STAND_BOT_W,
    mortise_z0: float = V_MORTISE_Z0,
    mortise_l_z: float = V_MORTISE_L_Z,
) -> cq.Workplane:
    """Build detachable modern Inverted-V (ʌ) desktop stand that slots into the -Y mortises."""
    y_top = -outer_w / 2 - V_TENON_CLEAR
    y_bot = y_top - V_STAND_H
    half_top = V_STAND_TOP_W / 2        # 14.0 mm
    half_bot = bot_w / 2                # 29.0 mm (or 25.0 mm on compact Aura v2)
    foot_w = 6.2
    arch_top_y = y_top - V_STAND_LEG_T
    arch_half_top = max(half_top - V_STAND_LEG_T - 1.5, 4.5)
    arch_half_bot = half_bot - foot_w

    # Outer inverted-V (ʌ) trapezoid in XY extruded along Z = 0..depth_z (prints flat on Z=0, zero supports)
    outer_pts = [
        (-half_bot, y_bot),
        (half_bot, y_bot),
        (half_top, y_top),
        (-half_top, y_top),
    ]
    inner_pts = [
        (-arch_half_bot, y_bot - 0.1),
        (arch_half_bot, y_bot - 0.1),
        (arch_half_top, arch_top_y),
        (-arch_half_top, arch_top_y),
    ]
    body = (
        cq.Workplane("XY")
        .polyline(outer_pts)
        .close()
        .extrude(depth_z)
        .edges("|Z")
        .fillet(1.4)
    )
    void = (
        cq.Workplane("XY")
        .workplane(offset=-0.5)
        .polyline(inner_pts)
        .close()
        .extrude(depth_z + 1.0)
        .edges("|Z")
        .fillet(2.2)
    )
    stand = body.cut(void)

    # Twin locking tenon blades on top of the V-stand cradle that slot up (+Y) into the base mortise pockets
    tenon_w_x = V_MORTISE_W_X - 2 * V_TENON_CLEAR           # 7.10 mm
    tenon_h_y = V_MORTISE_D_Y - V_TENON_CLEAR               # 3.45 mm above y_top
    tenon_l_z = mortise_l_z - 2 * V_TENON_CLEAR
    tenon_z0 = mortise_z0 + V_TENON_CLEAR
    for sx in (-1, 1):
        tenon = (
            e.box(
                tenon_w_x,
                tenon_h_y + 0.6,
                tenon_l_z,
                sx * V_MORTISE_X_OFF,
                y_top + (tenon_h_y - 0.6) / 2,
                tenon_z0,
            )
            .edges("|Z")
            .fillet(0.6)
        )
        stand = stand.union(tenon)
    return stand


def make_ld2410c_base() -> cq.Workplane:
    """Sleek desktop battery-free HLK-LD2410C base (86.8 x 28.8 x 24.4 mm, no screw tabs) with V-stand mortises."""
    base = e.rrect(OUTER_L_C, OUTER_W_C, OUTER_R, 0.0, H_C).edges("<Z").chamfer(DESK_CHAMFER)
    base = base.cut(e.rrect(INNER_L_C, INNER_W_C, e.INNER_R, e.FLOOR, DEPTH_C + 1.0))
    base = _add_snap_receivers_c(base)
    base = _add_board_c_cradle(base, inner_w=INNER_W_C)
    base = _add_radar_c_cradle(base)
    base = _add_v_stand_mortise(base, OUTER_W_C)
    return _add_usbc_socket_bay(base, inner_l=INNER_L_C, inner_w=INNER_W_C, extra_w=USBC_SOCK_EXTRA_W)


def make_ld2410c_lid() -> cq.Workplane:
    """Sleek desktop snap-fit lid (86.8 x 28.8 mm) for HLK-LD2410C with 24x18x1.2 mm radome (no MCU hold-downs)."""
    lid = e.rrect(OUTER_L_C, OUTER_W_C, OUTER_R, H_C, e.LID_T).edges(">Z").chamfer(DESK_CHAMFER)

    lip_l, lip_w = INNER_L_C - 2 * e.LIP_CLEAR, INNER_W_C - 2 * e.LIP_CLEAR
    lip = (
        e.rrect(lip_l, lip_w, max(e.INNER_R - e.LIP_CLEAR, 0.5), H_C - e.LIP_H, e.LIP_H)
        .cut(e.rrect(lip_l - 2 * e.LIP_T, lip_w - 2 * e.LIP_T, 0.5, H_C - e.LIP_H - 1, e.LIP_H + 2))
    )
    lid = lid.union(lip)

    snap_z_bot_c = H_C - 2.05
    for sx in (-1, 1):
        for sy in (-1, 1):
            lid = lid.union(_snap_bead_x(sx * SNAP_X_OFF, SNAP_L, INNER_W_C, sy, snap_z_bot_c))

    radome_pocket = e.box(RADOME_C_L, RADOME_C_W, e.RADOME_DEPTH + 0.1, RADAR_C_X, Y_C, H_C - 0.1)
    lid = lid.cut(radome_pocket)

    # 1. Four 2.4x2.4 mm corner hold-down bosses over 22x16 mm HLK-LD2410C (no SuperMini arches so wiring is clear)
    rad_hold_z0 = e.FLOOR + RADAR_C_RAIL_H + RADAR_C_T + 0.30
    rad_hold_h = (H_C + e.RADOME_DEPTH) - rad_hold_z0 + 0.2
    for sx in (-1, 1):
        for sy in (-1, 1):
            lid = lid.union(e.box(2.4, 2.4, rad_hold_h, RADAR_C_X + sx * 9.5, Y_C + sy * 6.6, rad_hold_z0))

    # 2. Top hold-down boss over the 14.0 mm USB-C socket stem (stops 0.325 mm above stem top Z = 15.175 mm)
    sock_hold_z0 = USBC_SOCK_Z + USBC_SOCK_STEM_H / 2 + 0.325
    lid = lid.union(e.box(4.0, 8.0, H_C - sock_hold_z0 + 0.2, +35.0, Y_C, sock_hold_z0))
    return lid


# --------------------------------------------------------------------------------------
# Model 5: Hi-Link HLK-LD2410S (20x20 mm) Sleek Desktop Battery-Free Enclosure with Panel USB-C Socket
# --------------------------------------------------------------------------------------

def _add_radar_s_usb_cradle(base: cq.Workplane) -> cq.Workplane:
    """Monolithic wall-joined radar tower for 20.0 x 20.0 mm HLK-LD2410S in compact 28 mm wide USB-powered cavity."""
    z_top = e.FLOOR + e.RADAR_RAIL_H + e.RADAR_T            # 23.10 mm
    stop_h = e.RADAR_RAIL_H + e.RADAR_T + 1.05              # 21.75 mm (Z_max = 24.15 mm)
    body_h = (H_S - e.LIP_H - 0.4) - e.FLOOR                # 21.00 mm (clears 2.6 mm lid lip at Z = 23.80 mm)
    rail_l = e.RADAR_L - e.RADAR_RECESS_NEG_X - e.RADAR_RECESS_POS_X
    rail_cx = RADAR_S_USB_X + (e.RADAR_RECESS_NEG_X - e.RADAR_RECESS_POS_X) / 2
    y_in = e.RADAR_W / 2 + e.BOARD_CLEAR                    # 10.15 mm (3.85 mm solid wall to +/-14.0 mm outer walls)

    # 1. +/-Y Side Walls: 3.85 mm thick solid blocks fused directly to BOTH -Y and +Y outer enclosure walls
    for sy in (-1, 1):
        y_wall = sy * y_in
        y_ledge = sy * (y_in - e.RADAR_LEDGE)
        y_outer = sy * (INNER_W_S / 2)
        base = base.union(e.box(rail_l, abs(y_outer - y_ledge), e.RADAR_RAIL_H,
                                rail_cx, (y_outer + y_ledge) / 2, e.FLOOR))
        base = base.union(e.box(rail_l, abs(y_outer - y_wall), body_h,
                                rail_cx, (y_outer + y_wall) / 2, e.FLOOR))
        base = base.union(e.box(rail_l, 1.35, stop_h, rail_cx, y_wall + sy * 0.675, e.FLOOR))
        base = base.union(e._snap_hook_x(rail_cx, 9.0, y_wall, sy, z_top, e.RADAR_SNAP_OVERHANG))

    # 2. -X End Wall: 4.35 mm solid cross-wall fused directly to -X, -Y, and +Y outer enclosure walls
    neg_x_in = RADAR_S_USB_X - e.RADAR_L / 2 - e.BOARD_CLEAR  # -36.65 mm
    neg_x_w = INNER_L_S / 2 + neg_x_in                        # 4.35 mm
    base = base.union(e.box(neg_x_w, INNER_W_S, body_h, -INNER_L_S / 2 + neg_x_w / 2, Y_C, e.FLOOR))
    base = base.union(e.box(1.35, INNER_W_S - 4.4, stop_h, neg_x_in - 0.675, Y_C, e.FLOOR))

    # 3. (+X, -Y) Monolithic Corner L-Buttress fused to -Y wall (leaves 19.05 mm wide unobstructed +X exit
    #    channel Y = -5.05..+14.00 mm for the asymmetric 5-pin 2.54 mm female DuPont housing at Y = -3.60..+10.20 mm)
    pos_x_in = RADAR_S_USB_X + e.RADAR_L / 2 + e.BOARD_CLEAR  # -16.35 mm
    ext_x = e.RADAR_RECESS_POS_X + e.BOARD_CLEAR
    pos_y_max = -5.05
    y_bot_outer = -INNER_W_S / 2                              # -14.00 mm
    base = base.union(e.box(ext_x, pos_y_max - y_bot_outer, e.RADAR_RAIL_H,
                            pos_x_in - ext_x / 2, (pos_y_max + y_bot_outer) / 2, e.FLOOR))
    base = base.union(e.box(ext_x, (-y_in) - y_bot_outer, body_h,
                            pos_x_in - ext_x / 2, (-y_in + y_bot_outer) / 2, e.FLOOR))
    y_stop_min = y_bot_outer + 2.2                            # -11.80 mm (clears -Y lid lip)
    base = base.union(e.box(2.5, pos_y_max - y_bot_outer, body_h,
                            pos_x_in + 1.25, (pos_y_max + y_bot_outer) / 2, e.FLOOR))
    base = base.union(e.box(2.5, pos_y_max - y_stop_min, stop_h,
                            pos_x_in + 1.25, (pos_y_max + y_stop_min) / 2, e.FLOOR))
    return base


def make_ld2410s_usb_base() -> cq.Workplane:
    """Sleek desktop battery-free HLK-LD2410S base (86.8 x 32.8 x 26.4 mm, no screw tabs) with V-stand mortises."""
    base = e.rrect(OUTER_L_S, OUTER_W_S, OUTER_R, 0.0, H_S).edges("<Z").chamfer(DESK_CHAMFER)
    base = base.cut(e.rrect(INNER_L_S, INNER_W_S, e.INNER_R, e.FLOOR, DEPTH_S + 1.0))
    base = _add_snap_receivers_generic(base, INNER_W_S, OUTER_L_S, H_S)
    base = _add_board_c_cradle(base, inner_w=INNER_W_S)
    base = _add_radar_s_usb_cradle(base)
    base = _add_v_stand_mortise(base, OUTER_W_S)
    return _add_usbc_socket_bay(base, inner_l=INNER_L_S, inner_w=INNER_W_S, extra_w=USBC_SOCK_EXTRA_W)


def make_ld2410s_usb_lid() -> cq.Workplane:
    """Sleek desktop snap-fit lid (86.8 x 32.8 mm) for 20x20 mm HLK-LD2410S (no MCU hold-downs)."""
    lid = e.rrect(OUTER_L_S, OUTER_W_S, OUTER_R, H_S, e.LID_T).edges(">Z").chamfer(DESK_CHAMFER)

    lip_l, lip_w = INNER_L_S - 2 * e.LIP_CLEAR, INNER_W_S - 2 * e.LIP_CLEAR
    lip = (
        e.rrect(lip_l, lip_w, max(e.INNER_R - e.LIP_CLEAR, 0.5), H_S - e.LIP_H, e.LIP_H)
        .cut(e.rrect(lip_l - 2 * e.LIP_T, lip_w - 2 * e.LIP_T, 0.5, H_S - e.LIP_H - 1, e.LIP_H + 2))
    )
    lid = lid.union(lip)

    snap_z_bot_s = H_S - 2.05
    for sx in (-1, 1):
        for sy in (-1, 1):
            lid = lid.union(_snap_bead_x(sx * SNAP_X_OFF, SNAP_L, INNER_W_S, sy, snap_z_bot_s))

    radome_pocket = e.box(e.RADOME_L, e.RADOME_W, e.RADOME_DEPTH + 0.1, RADAR_S_USB_X, Y_C, H_S - 0.1)
    lid = lid.cut(radome_pocket)

    # 1. Three 2.4x2.4 mm corner hold-down bosses over 20x20 mm HLK-LD2410S non-header corners
    #    (no SuperMini hold-downs so cabling is completely unobstructed)
    rad_hold_z0 = e.FLOOR + e.RADAR_RAIL_H + e.RADAR_T + 0.30
    rad_hold_h = (H_S + e.RADOME_DEPTH) - rad_hold_z0 + 0.2
    for cx, cy in [
        (RADAR_S_USB_X - 8.6, Y_C - 8.6),
        (RADAR_S_USB_X - 8.6, Y_C + 8.6),
        (RADAR_S_USB_X + 8.6, Y_C - 8.6),
    ]:
        lid = lid.union(e.box(2.4, 2.4, rad_hold_h, cx, cy, rad_hold_z0))

    # 2. Top hold-down boss over the 14.0 mm USB-C socket stem (stops 0.325 mm above stem top Z = 15.175 mm)
    sock_hold_z0 = USBC_SOCK_Z + USBC_SOCK_STEM_H / 2 + 0.325
    lid = lid.union(e.box(4.0, 8.0, H_S - sock_hold_z0 + 0.2, +35.0, Y_C, sock_hold_z0))
    return lid


def make_ld2410s_usb_dummies() -> dict[str, cq.Workplane]:
    """Dummies for compact battery-free Model 5: SuperMini + 20x20 mm HLK-LD2410S + 5-pin DuPont + USB-C socket."""
    dm = make_ld2410c_dummies()
    z_rad_bot = e.FLOOR + e.RADAR_RAIL_H
    z_rad_top = z_rad_bot + e.RADAR_T
    radar = e.rrect(e.RADAR_L, e.RADAR_W, e.RADAR_CORNER_R, z_rad_bot, e.RADAR_T).translate((RADAR_S_USB_X, Y_C, 0))
    x_rad_left, x_rad_right = RADAR_S_USB_X - e.RADAR_L / 2, RADAR_S_USB_X + e.RADAR_L / 2
    y_rad_bot, y_rad_top = Y_C - e.RADAR_W / 2, Y_C + e.RADAR_W / 2
    j2_cy = y_rad_top - (0.35 + 13.05) / 2
    radar_parts = (
        e.box(10.0, 10.0, 1.0, RADAR_S_USB_X, Y_C, z_rad_top)
        .union(e.box(2.2, 12.7, e.RADAR_PARTS_H, x_rad_right - 1.47, j2_cy, z_rad_top))
        .union(e.box(8.0, 8.0, 1.0, RADAR_S_USB_X, Y_C, z_rad_bot - 1.0))
        .union(e.box(3.5, 3.2, 1.2, x_rad_left + 2.75, y_rad_bot + 2.60, z_rad_bot - 1.2))
    )
    dupont_5p = e.box(
        e.DUPONT_5P_T, e.DUPONT_5P_W, e.DUPONT_5P_H, x_rad_right - 1.47, j2_cy, z_rad_bot - e.DUPONT_5P_H
    ).union(e.box(3.5, 12.7, 5.5, x_rad_right + 1.5, j2_cy, z_rad_bot - e.DUPONT_5P_H))
    dm["radar"] = radar
    dm["radar_parts"] = radar_parts
    dm["dupont_5p"] = dupont_5p
    return dm


# --------------------------------------------------------------------------------------
# Model 6: "AURA" — Award-Edition Horizon Stadium Monolith (Hidden Rear USB-C + Sculptural V-Pedestal)
# --------------------------------------------------------------------------------------

def _add_aura_rear_usbc_bay(
    base: cq.Workplane,
    extra_w: float = USBC_SOCK_EXTRA_W,
    cx: float = USBC_AURA_X,
    cy: float = Y_C,
    throat_w: float | None = None,
) -> cq.Workplane:
    """Mount AliExpress 2-Pin USB-C socket in REAR (Z=0) face with 3-zone clip lock & 13.4 mm coaxial stem sleeve."""
    cut_w_y = USBC_SOCK_CUT_W + extra_w                         # 13.4 mm coaxial rear stem guide along Y
    lock_w_y = (USBC_SOCK_CLIP_THROAT_W + extra_w) if throat_w is None else throat_w
    cut_h_x = USBC_SOCK_CUT_H                                   # 5.8 mm along X
    wing_w_y = USBC_SOCK_WING_W + 1.0 + extra_w                 # 16.8 mm snap-clip expansion pocket along Y

    # 1. Floor-joined solid housing around the vertical rear-entry USB-C stem (Z = FLOOR..13.80 mm)
    housing_h = 13.8 - e.FLOOR
    housing = e.box(cut_h_x + 4.4, wing_w_y + 3.6, housing_h, cx, cy, e.FLOOR)
    base = base.union(housing)

    # 2. Zone 1A: Outer entry lead-in mouth (Z = -0.50..+0.45 mm, 6.0 x 13.6 mm) for effortless connector alignment
    mouth_cut = (
        cq.Workplane("XY")
        .workplane(offset=-0.50)
        .center(cx, cy)
        .rect(cut_h_x + 0.2, cut_w_y + 0.2)
        .extrude(0.95)
        .edges("|Z")
        .fillet(0.5)
    )
    # 3. Zone 1B: Clip-locking collar (Z = 0.45..1.10 mm, 5.8 x lock_w_y) that snaps into the connector's bezel waist
    collar_cut = (
        cq.Workplane("XY")
        .workplane(offset=-0.10)
        .center(cx, cy)
        .rect(cut_h_x, lock_w_y)
        .extrude(USBC_SOCK_PANEL_T + 0.30)
        .edges("|Z")
        .fillet(0.5)
    )
    # 4. Zone 2: 4-sided snap-clip expansion chamber above the 1.10 mm locking lip (Z = 1.10..5.80 mm)
    #    Steps OUTWARD to 6.6 x 16.8 mm at Z = 1.10 mm, creating an upward-facing 90 deg locking shelf with 0 overhangs
    pocket_h = USBC_SOCK_POCKET_END - USBC_SOCK_PANEL_T         # 4.70 mm
    wing_chamber = e.box(
        cut_h_x + 0.8,
        wing_w_y,
        pocket_h,
        cx,
        cy,
        USBC_SOCK_PANEL_T,
    )
    # 5. Support-free 45 deg centering taper (Z = 5.80..7.50 mm) from 6.6 x 16.8 mm to 5.8 x 13.4 mm
    taper_cut = (
        cq.Workplane("XY")
        .workplane(offset=USBC_SOCK_POCKET_END - 0.05)
        .center(cx, cy)
        .rect(cut_h_x + 0.8, wing_w_y)
        .workplane(offset=1.75)
        .rect(cut_h_x, cut_w_y)
        .loft()
    )
    # 6. Zone 3: Coaxial 13.4 x 5.8 mm rear stem guide sleeve (Z = 7.40..15.00 mm) preventing lateral stem wobble
    stem_guide_cut = (
        cq.Workplane("XY")
        .workplane(offset=USBC_SOCK_POCKET_END + 1.50)
        .center(cx, cy)
        .rect(cut_h_x, cut_w_y)
        .extrude(8.0)
        .edges("|Z")
        .fillet(0.5)
    )
    return base.cut(mouth_cut).cut(collar_cut).cut(wing_chamber).cut(taper_cut).cut(stem_guide_cut)


def _add_aura_radar_cradle(base: cq.Workplane) -> cq.Workplane:
    """Wall-joined radar cradle for 20x20 mm HLK-LD2410S at RADAR_AURA_X inside the stadium cavity."""
    z_top = e.FLOOR + e.RADAR_RAIL_H + e.RADAR_T        # 23.10 mm
    stop_h = e.RADAR_RAIL_H + e.RADAR_T + 1.05          # 21.75 mm
    body_h = (H_AURA - e.LIP_H - 0.4) - e.FLOOR         # 21.00 mm
    rail_l = e.RADAR_L - e.RADAR_RECESS_NEG_X - e.RADAR_RECESS_POS_X
    rail_cx = RADAR_AURA_X + (e.RADAR_RECESS_NEG_X - e.RADAR_RECESS_POS_X) / 2
    y_in = e.RADAR_W / 2 + e.BOARD_CLEAR                # 10.15 mm

    for sy in (-1, 1):
        y_wall = sy * y_in
        y_ledge = sy * (y_in - e.RADAR_LEDGE)
        y_outer = sy * (INNER_W_AURA / 2 - 0.8)
        base = base.union(e.box(rail_l, abs(y_outer - y_ledge), e.RADAR_RAIL_H,
                                rail_cx, (y_outer + y_ledge) / 2, e.FLOOR))
        base = base.union(e.box(rail_l, abs(y_outer - y_wall), body_h,
                                rail_cx, (y_outer + y_wall) / 2, e.FLOOR))
        base = base.union(e.box(rail_l, 1.35, stop_h, rail_cx, y_wall + sy * 0.675, e.FLOOR))
        base = base.union(e._snap_hook_x(rail_cx, 9.0, y_wall, sy, z_top, e.RADAR_SNAP_OVERHANG))

    # -X stop rib behind the 20x20 mm radar (centered at Y=0 where stadium end has maximum width)
    neg_x_in = RADAR_AURA_X - e.RADAR_L / 2 - e.BOARD_CLEAR  # -32.15 mm
    base = base.union(e.box(6.0, 14.0, body_h, neg_x_in - 3.0, Y_C, e.FLOOR))
    base = base.union(e.box(1.5, 13.0, stop_h, neg_x_in - 0.75, Y_C, e.FLOOR))

    # (+X, -Y) corner buttress leaving 19.65 mm wide +X exit channel for 5-pin female DuPont connector
    pos_x_in = RADAR_AURA_X + e.RADAR_L / 2 + e.BOARD_CLEAR  # -11.85 mm
    ext_x = e.RADAR_RECESS_POS_X + e.BOARD_CLEAR
    pos_y_max = -5.05
    y_bot_outer = -INNER_W_AURA / 2 + 0.5
    base = base.union(e.box(ext_x, pos_y_max - y_bot_outer, e.RADAR_RAIL_H,
                            pos_x_in - ext_x / 2, (pos_y_max + y_bot_outer) / 2, e.FLOOR))
    base = base.union(e.box(2.2, pos_y_max - (y_bot_outer + 2.2), stop_h,
                            pos_x_in + 1.1, (pos_y_max + y_bot_outer + 2.2) / 2, e.FLOOR))
    return base


def make_aura_base() -> cq.Workplane:
    """Build 'AURA' full-radius stadium unibody shell (88 x 34 x 26.4 mm) with rear USB-C & flush V-stand mortises."""
    # Sculpted stadium monolith with 1.4 mm x 45 deg rear bevel and 0.5 mm x 45 deg parting-seam shadow reveal
    base = (
        e.rrect(OUTER_L_AURA, OUTER_W_AURA, OUTER_R_AURA, 0.0, H_AURA)
        .edges("<Z")
        .chamfer(1.4)
        .edges(">Z")
        .chamfer(0.5)
    )
    base = base.cut(e.rrect(INNER_L_AURA, INNER_W_AURA, INNER_R_AURA, e.FLOOR, DEPTH_AURA + 1.0))

    # 4 internal snap-catch receiver grooves along the straight +/-Y stadium walls (X = +/-16.0 mm)
    groove_l = SNAP_L + 1.0
    groove_h = SNAP_BEAD_H + 0.24
    groove_z = (H_AURA - 2.05) - 0.12
    groove_depth_y = SNAP_ENGAGE + 0.25
    for sx in (-1, 1):
        for sy in (-1, 1):
            gy = sy * (INNER_W_AURA / 2 + (groove_depth_y / 2 - 0.10))
            base = base.cut(e.box(groove_l, groove_depth_y, groove_h, sx * 16.0, gy, groove_z))

    # Discrete rear-bottom fingernail release notch at X = -39.5 mm (hidden at the curved -X tail)
    base = base.cut(e.box(1.4, 6.0, 0.8, -OUTER_L_AURA / 2 + 0.6, 0.0, H_AURA - 0.7))

    # Internal cradles, flush -Y V-stand mortises, and hidden rear (Z=0) USB-C socket bay
    base = _add_board_c_cradle(base, inner_w=INNER_W_AURA, board_x=BOARD_AURA_X)
    base = _add_aura_radar_cradle(base)
    base = _add_v_stand_mortise(base, OUTER_W_AURA)
    return _add_aura_rear_usbc_bay(base, extra_w=USBC_SOCK_EXTRA_W)


def make_aura_lid() -> cq.Workplane:
    """Build 'AURA' sculpted stadium bezel lid with 45 deg architectural chamfer & horizon shadow groove."""
    lid = (
        e.rrect(OUTER_L_AURA, OUTER_W_AURA, OUTER_R_AURA, H_AURA, e.LID_T)
        .edges(">Z")
        .chamfer(1.8)
        .edges("<Z")
        .chamfer(0.5)
    )
    # Concentric recessed stadium "horizon groove" (0.8 mm wide x 0.45 mm deep) framing the front radome face
    groove_out = e.rrect(OUTER_L_AURA - 7.2, OUTER_W_AURA - 7.2, OUTER_R_AURA - 3.6, H_AURA + e.LID_T - 0.45, 0.6)
    groove_in = e.rrect(OUTER_L_AURA - 8.8, OUTER_W_AURA - 8.8, OUTER_R_AURA - 4.4, H_AURA + e.LID_T - 0.55, 0.8)
    lid = lid.cut(groove_out.cut(groove_in))

    # Full-stadium perimeter lip (0.15 mm/side clearance, 2.6 mm deep)
    lip_l, lip_w = INNER_L_AURA - 2 * e.LIP_CLEAR, INNER_W_AURA - 2 * e.LIP_CLEAR
    lip_r = INNER_R_AURA - e.LIP_CLEAR
    lip = (
        e.rrect(lip_l, lip_w, lip_r, H_AURA - e.LIP_H, e.LIP_H)
        .cut(e.rrect(lip_l - 2 * e.LIP_T, lip_w - 2 * e.LIP_T, lip_r - e.LIP_T, H_AURA - e.LIP_H - 1, e.LIP_H + 2))
    )
    lid = lid.union(lip)

    snap_z_bot_a = H_AURA - 2.05
    for sx in (-1, 1):
        for sy in (-1, 1):
            lid = lid.union(_snap_bead_x(sx * 16.0, SNAP_L, INNER_W_AURA, sy, snap_z_bot_a))

    # Rounded 22x22x1.2 mm blind RF radome pocket over HLK-LD2410S (follows stadium contour)
    radome_pocket = e.rrect(e.RADOME_L, e.RADOME_W, 3.5, H_AURA - 0.1, e.RADOME_DEPTH + 0.1).translate(
        (RADAR_AURA_X, Y_C, 0.0)
    )
    lid = lid.cut(radome_pocket)

    # 1. Three 2.4x2.4 mm corner hold-down bosses over HLK-LD2410S non-header corners (no MCU or USB wire-exit bosses)
    rad_hold_z0 = e.FLOOR + e.RADAR_RAIL_H + e.RADAR_T + 0.30
    rad_hold_h = (H_AURA + e.RADOME_DEPTH) - rad_hold_z0 + 0.2
    for cx, cy in [
        (RADAR_AURA_X - 8.2, Y_C - 8.2),
        (RADAR_AURA_X - 8.2, Y_C + 8.2),
        (RADAR_AURA_X + 8.2, Y_C - 8.2),
    ]:
        lid = lid.union(e.box(2.4, 2.4, rad_hold_h, cx, cy, rad_hold_z0))
    return lid


def make_aura_stand(outer_w: float = OUTER_W_AURA) -> cq.Workplane:
    """Build 'AURA' sculptural tapered Inverted-V (ʌ) pedestal with 45 deg front bevel."""
    stand = make_v_stand(outer_w=outer_w).edges(">Z").chamfer(1.2)
    return stand


# Aliases for explicit Aura-S naming
make_aura_s_base = make_aura_base
make_aura_s_lid = make_aura_lid
make_aura_s_stand = lambda: make_aura_stand(outer_w=OUTER_W_AURA)
make_aura_s_dummies = lambda: make_aura_dummies()


# --------------------------------------------------------------------------------------
# Model 7: "Aura-C" — Award-Edition Horizon Stadium Monolith for 22x16 mm HLK-LD2410C
# --------------------------------------------------------------------------------------

def _add_aura_c_radar_cradle(base: cq.Workplane) -> cq.Workplane:
    """Wall-joined radar cradle for 22.0 x 16.0 mm HLK-LD2410C at RADAR_AURA_C_X inside Aura-C stadium cavity."""
    z_top = e.FLOOR + RADAR_C_RAIL_H + RADAR_C_T            # 21.10 mm
    stop_h = RADAR_C_RAIL_H + RADAR_C_T + 1.05              # 19.75 mm
    body_h = (H_AURA_C - e.LIP_H - 0.4) - e.FLOOR           # 19.00 mm
    rail_l = RADAR_C_L - e.RADAR_RECESS_NEG_X - e.RADAR_RECESS_POS_X
    rail_cx = RADAR_AURA_C_X + (e.RADAR_RECESS_NEG_X - e.RADAR_RECESS_POS_X) / 2
    y_in = RADAR_C_W / 2 + e.BOARD_CLEAR                    # 8.15 mm

    for sy in (-1, 1):
        y_wall = sy * y_in
        y_ledge = sy * (y_in - e.RADAR_LEDGE)
        y_outer = sy * (INNER_W_AURA_C / 2 - 1.2)
        base = base.union(e.box(rail_l, abs(y_outer - y_ledge), RADAR_C_RAIL_H,
                                rail_cx, (y_outer + y_ledge) / 2, e.FLOOR))
        base = base.union(e.box(rail_l, abs(y_outer - y_wall), body_h,
                                rail_cx, (y_outer + y_wall) / 2, e.FLOOR))
        base = base.union(e.box(rail_l, 1.35, stop_h, rail_cx, y_wall + sy * 0.675, e.FLOOR))
        base = base.union(e._snap_hook_x(rail_cx, 9.0, y_wall, sy, z_top, e.RADAR_SNAP_OVERHANG))

    # -X stop rib behind the 22x16 mm HLK-LD2410C
    neg_x_in = RADAR_AURA_C_X - RADAR_C_L / 2 - e.BOARD_CLEAR  # -36.65 mm
    base = base.union(e.box(5.0, 12.0, body_h, neg_x_in - 2.5, Y_C, e.FLOOR))
    base = base.union(e.box(1.5, 11.0, stop_h, neg_x_in - 0.75, Y_C, e.FLOOR))

    # (+X, +/-Y) corner buttresses leaving 10.0 mm central +X channel (Y = -5.0..+5.0 mm) for 5-pin 1.27 mm header
    pos_x_in = RADAR_AURA_C_X + RADAR_C_L / 2 + e.BOARD_CLEAR  # -14.35 mm
    ext_x = e.RADAR_RECESS_POS_X + e.BOARD_CLEAR
    y_outer_b = INNER_W_AURA_C / 2 - 0.5                       # 13.10 mm
    buttress_w_y = y_outer_b - 5.0
    for sy in (-1, 1):
        by_full = sy * (5.0 + buttress_w_y / 2)
        bw_stop = (INNER_W_AURA_C / 2 - 2.2) - 5.0
        by_stop = sy * (5.0 + bw_stop / 2)
        base = base.union(e.box(ext_x, buttress_w_y, RADAR_C_RAIL_H, pos_x_in - ext_x / 2, by_full, e.FLOOR))
        base = base.union(e.box(1.8, bw_stop, stop_h, pos_x_in + 0.9, by_stop, e.FLOOR))
    return base


def make_aura_c_base() -> cq.Workplane:
    """Build 'Aura-C' full-radius stadium unibody shell (92 x 32 x 24.4 mm) for 22x16 mm HLK-LD2410C."""
    base = (
        e.rrect(OUTER_L_AURA, OUTER_W_AURA_C, OUTER_R_AURA_C, 0.0, H_AURA_C)
        .edges("<Z")
        .chamfer(1.4)
        .edges(">Z")
        .chamfer(0.5)
    )
    base = base.cut(e.rrect(INNER_L_AURA, INNER_W_AURA_C, INNER_R_AURA_C, e.FLOOR, DEPTH_AURA_C + 1.0))

    groove_l = SNAP_L + 1.0
    groove_h = SNAP_BEAD_H + 0.24
    groove_z = (H_AURA_C - 2.05) - 0.12
    groove_depth_y = SNAP_ENGAGE + 0.25
    for sx in (-1, 1):
        for sy in (-1, 1):
            gy = sy * (INNER_W_AURA_C / 2 + (groove_depth_y / 2 - 0.10))
            base = base.cut(e.box(groove_l, groove_depth_y, groove_h, sx * 16.0, gy, groove_z))

    base = base.cut(e.box(1.4, 6.0, 0.8, -OUTER_L_AURA / 2 + 0.6, 0.0, H_AURA_C - 0.7))
    base = _add_board_c_cradle(base, inner_w=INNER_W_AURA_C, board_x=BOARD_AURA_X)
    base = _add_aura_c_radar_cradle(base)
    base = _add_v_stand_mortise(base, OUTER_W_AURA_C)
    return _add_aura_rear_usbc_bay(base, extra_w=USBC_SOCK_EXTRA_W)


def make_aura_c_lid() -> cq.Workplane:
    """Build 'Aura-C' sculpted stadium bezel lid (92 x 32 mm) with 24x18x1.2 mm radome for HLK-LD2410C."""
    lid = (
        e.rrect(OUTER_L_AURA, OUTER_W_AURA_C, OUTER_R_AURA_C, H_AURA_C, e.LID_T)
        .edges(">Z")
        .chamfer(1.8)
        .edges("<Z")
        .chamfer(0.5)
    )
    groove_out = e.rrect(OUTER_L_AURA - 7.2, OUTER_W_AURA_C - 7.2, OUTER_R_AURA_C - 3.6, H_AURA_C + e.LID_T - 0.45, 0.6)
    groove_in = e.rrect(OUTER_L_AURA - 8.8, OUTER_W_AURA_C - 8.8, OUTER_R_AURA_C - 4.4, H_AURA_C + e.LID_T - 0.55, 0.8)
    lid = lid.cut(groove_out.cut(groove_in))

    lip_l, lip_w = INNER_L_AURA - 2 * e.LIP_CLEAR, INNER_W_AURA_C - 2 * e.LIP_CLEAR
    lip_r = INNER_R_AURA_C - e.LIP_CLEAR
    lip = (
        e.rrect(lip_l, lip_w, lip_r, H_AURA_C - e.LIP_H, e.LIP_H)
        .cut(e.rrect(lip_l - 2 * e.LIP_T, lip_w - 2 * e.LIP_T, lip_r - e.LIP_T, H_AURA_C - e.LIP_H - 1, e.LIP_H + 2))
    )
    lid = lid.union(lip)

    snap_z_bot_ac = H_AURA_C - 2.05
    for sx in (-1, 1):
        for sy in (-1, 1):
            lid = lid.union(_snap_bead_x(sx * 16.0, SNAP_L, INNER_W_AURA_C, sy, snap_z_bot_ac))

    radome_pocket = e.rrect(RADOME_C_L, RADOME_C_W, 3.0, H_AURA_C - 0.1, e.RADOME_DEPTH + 0.1).translate(
        (RADAR_AURA_C_X, Y_C, 0.0)
    )
    lid = lid.cut(radome_pocket)

    # 1. Four 2.4x2.4 mm corner hold-down bosses over 22x16 mm HLK-LD2410C (no MCU or USB wire-exit bosses)
    rad_hold_z0 = e.FLOOR + RADAR_C_RAIL_H + RADAR_C_T + 0.30
    rad_hold_h = (H_AURA_C + e.RADOME_DEPTH) - rad_hold_z0 + 0.2
    for sx in (-1, 1):
        for sy in (-1, 1):
            lid = lid.union(e.box(2.4, 2.4, rad_hold_h, RADAR_AURA_C_X + sx * 9.5, Y_C + sy * 6.6, rad_hold_z0))
    return lid


def make_aura_c_stand() -> cq.Workplane:
    """Build 'Aura-C' sculptural tapered Inverted-V (ʌ) pedestal with 45 deg front bevel."""
    return make_aura_stand(outer_w=OUTER_W_AURA_C)


def make_aura_c_dummies() -> dict[str, cq.Workplane]:
    """Dummies for Model 7 ('Aura-C'): SuperMini + 22x16 mm HLK-LD2410C + Rear-Entry (Z=0) 13.4 mm USB-C Socket."""
    dm = make_aura_dummies()
    z_rad_bot = e.FLOOR + RADAR_C_RAIL_H
    z_rad_top = z_rad_bot + RADAR_C_T
    radar = e.rrect(RADAR_C_L, RADAR_C_W, RADAR_C_CORNER_R, z_rad_bot, RADAR_C_T).translate((RADAR_AURA_C_X, Y_C, 0))
    x_rad_left, x_rad_right = RADAR_AURA_C_X - RADAR_C_L / 2, RADAR_AURA_C_X + RADAR_C_L / 2
    y_rad_bot = Y_C - RADAR_C_W / 2
    radar_parts = (
        e.box(10.0, 10.0, 1.0, RADAR_AURA_C_X, Y_C, z_rad_top)
        .union(e.box(2.0, 6.8, e.RADAR_PARTS_H, x_rad_right - 1.3, Y_C, z_rad_top))
        .union(e.box(8.0, 8.0, 1.0, RADAR_AURA_C_X, Y_C, z_rad_bot - 1.0))
        .union(e.box(3.5, 3.2, 1.2, x_rad_left + 2.75, y_rad_bot + 2.60, z_rad_bot - 1.2))
    )
    dupont_5p = e.box(2.6, 7.6, 12.0, x_rad_right - 1.3, Y_C, z_rad_bot - 12.0).union(
        e.box(2.8, 7.6, 5.0, x_rad_right + 1.4, Y_C, z_rad_bot - 12.0)
    )
    dm["radar"] = radar
    dm["radar_parts"] = radar_parts
    dm["dupont_5p"] = dupont_5p
    return dm


def make_aura_dummies() -> dict[str, cq.Workplane]:
    """Dummies for Model 6 ('AURA'): SuperMini + 20x20 mm HLK-LD2410S + Rear-Entry (Z=0) USB-C Socket & Plug."""
    z_brd_bot = e.FLOOR + e.BOARD_RAIL_H
    z_brd_top = z_brd_bot + e.BOARD_T
    board = e.box(e.BOARD_L, e.BOARD_W, e.BOARD_T, BOARD_AURA_X, Y_C, z_brd_bot)
    board_parts = (
        e.box(7.5, 9.2, 3.2, BOARD_AURA_X + e.BOARD_L / 2 - 3.2, Y_C, z_brd_top)
        .union(e.box(20.0, 12.0, 1.8, BOARD_AURA_X - 2.0, Y_C, z_brd_top))
        .union(e.box(e.BOARD_PIN_ROW_L, e.BOARD_PIN_SPAN_Y, e.BOARD_PIN_DEPTH,
                     BOARD_AURA_X, Y_C - e.BOARD_W / 2 + e.BOARD_PIN_SPAN_Y / 2, z_brd_bot - e.BOARD_PIN_DEPTH))
        .union(e.box(e.BOARD_PIN_ROW_L, e.BOARD_PIN_SPAN_Y, e.BOARD_PIN_DEPTH,
                     BOARD_AURA_X, Y_C + e.BOARD_W / 2 - e.BOARD_PIN_SPAN_Y / 2, z_brd_bot - e.BOARD_PIN_DEPTH))
    )

    z_rad_bot = e.FLOOR + e.RADAR_RAIL_H
    z_rad_top = z_rad_bot + e.RADAR_T
    radar = e.rrect(e.RADAR_L, e.RADAR_W, e.RADAR_CORNER_R, z_rad_bot, e.RADAR_T).translate((RADAR_AURA_X, Y_C, 0))
    x_rad_left, x_rad_right = RADAR_AURA_X - e.RADAR_L / 2, RADAR_AURA_X + e.RADAR_L / 2
    y_rad_bot, y_rad_top = Y_C - e.RADAR_W / 2, Y_C + e.RADAR_W / 2
    j2_cy = y_rad_top - (0.35 + 13.05) / 2
    radar_parts = (
        e.box(10.0, 10.0, 1.0, RADAR_AURA_X, Y_C, z_rad_top)
        .union(e.box(2.2, 12.7, e.RADAR_PARTS_H, x_rad_right - 1.47, j2_cy, z_rad_top))
        .union(e.box(8.0, 8.0, 1.0, RADAR_AURA_X, Y_C, z_rad_bot - 1.0))
        .union(e.box(3.5, 3.2, 1.2, x_rad_left + 2.75, y_rad_bot + 2.60, z_rad_bot - 1.2))
    )
    dupont_5p = e.box(
        e.DUPONT_5P_T, e.DUPONT_5P_W, e.DUPONT_5P_H, x_rad_right - 1.47, j2_cy, z_rad_bot - e.DUPONT_5P_H
    ).union(e.box(3.5, 12.7, 5.5, x_rad_right + 1.5, j2_cy, z_rad_bot - e.DUPONT_5P_H))

    # Rear-entry (Z=0) AliExpress 2-Pin Panel-Mount USB-C Socket at USBC_AURA_X:
    # - Bezel flush against Z=0 back face (Z = -2.05..-0.05 mm)
    # - 12.3 x 5.35 mm clip-locking waist (Z = 0.00..1.25 mm) inside the 12.8 x 5.8 mm locking collar
    # - 15.8 mm expanded clip barbs (Z = 1.25..5.50 mm) locked behind the Z = 1.10 mm 90 deg shelf
    # - 13.0 x 5.35 mm rigid rear stem (Z = 1.25..14.00 mm) guided coaxially by the 13.4 x 5.8 mm sleeve
    bezel = (
        cq.Workplane("XY")
        .workplane(offset=-USBC_SOCK_BEZEL_T - 0.05)
        .center(USBC_AURA_X, Y_C)
        .rect(USBC_SOCK_BEZEL_H, USBC_SOCK_BEZEL_W)
        .extrude(USBC_SOCK_BEZEL_T)
        .edges("|Z")
        .fillet(4.8)
    )
    waist = (
        e.box(USBC_SOCK_STEM_H, USBC_SOCK_WAIST_W, 1.25, USBC_AURA_X, Y_C, 0.0)
        .edges("|Z")
        .fillet(0.6)
    )
    stem = (
        e.box(USBC_SOCK_STEM_H, USBC_SOCK_STEM_W, USBC_SOCK_STEM_L - 1.25, USBC_AURA_X, Y_C, 1.25)
        .edges("|Z")
        .fillet(0.6)
    )
    wings = e.box(4.6, USBC_SOCK_WING_W, 4.25, USBC_AURA_X, Y_C, 1.25)
    usb_c_socket = bezel.union(waist).union(stem).union(wings)
    usb_c_plug = e.box(6.0, 11.4, 14.0, USBC_AURA_X, Y_C, -USBC_SOCK_BEZEL_T - 14.1)

    return {
        "board": board,
        "board_parts": board_parts,
        "radar": radar,
        "radar_parts": radar_parts,
        "dupont_5p": dupont_5p,
        "usb_c_socket": usb_c_socket,
        "usb_c_plug": usb_c_plug,
    }


# --------------------------------------------------------------------------------------
# Model 8 ("Aura-S v2" / "aura_v2") & Model 9 ("Aura-C v2" / "aura_c_v2")
# Compact Stacked Direct-Solder Stadium Monoliths (64.0 x 34.0/32.0 x 23.4 mm — 45% Smaller Volume)
# --------------------------------------------------------------------------------------

def _add_aura_v2_side_usbc_bay(
    base: cq.Workplane, outer_w: float, outer_r: float, extra_w: float = USBC_SOCK_EXTRA_W
) -> cq.Workplane:
    """Sculpted +X side-entry 3-zone USB-C clip-retention bay with flush flared architectural bezel alcove.

    Because the +X end of the stadium monolith is a semicircle (R = 16.95/15.95 mm), placing a flat 16.5 mm
    oval USB-C bezel against the apex (X = +32.0 mm) would leave unsightly side gaps along the curved nose.
    Instead, this carves a flared architectural oval bezel alcove into the +X stadium nose with a flat vertical
    seating plane at X = +28.50 mm (3.50 mm recessed from the +32.00 mm nose apex), so the 2.0 mm oval bezel
    nests completely flush inside the rounded stadium silhouette with a crisp 45 deg shadow-reveal halo.
    """
    x_seat = USBC_AURA_V2_X_SEAT                # +28.50 mm flat bezel seating plane
    cz = USBC_AURA_V2_Z                         # 11.20 mm vertical center
    w_throat = USBC_SOCK_CLIP_THROAT_W          # 13.20 mm Station #4 clip-locking collar width along Y
    w_guide = USBC_SOCK_CUT_W + extra_w         # 13.40 mm coaxial rear stem guide sleeve width along Y
    h = USBC_SOCK_CUT_H                         # 5.80 mm height along Z
    w_exp = USBC_SOCK_WING_W + 1.0              # 16.80 mm snap-clip expansion chamber width along Y

    # 1. Outer stadium nose bulkhead (X = x_seat - 1.50 .. +32.00 mm, Z = FLOOR .. cz + 5.80 mm)
    #    plus floor-joined under-stem support rails and side guide cheeks (X = x_seat - 14.20 .. x_seat - 1.10 mm)
    #    clipped cleanly inside the outer stadium perimeter so there is zero long interior roof bridging.
    outer_env = e.rrect(OUTER_L_AURA_V2 - 0.6, outer_w - 0.6, outer_r - 0.3, e.FLOOR, H_AURA_V2 - e.FLOOR - 1.0)
    nose_len = (OUTER_L_AURA_V2 / 2) - (x_seat - 1.50)
    nose_cx = (OUTER_L_AURA_V2 / 2 + (x_seat - 1.50)) / 2
    nose_blk = e.box(nose_len, outer_w, (cz + 5.80) - e.FLOOR, nose_cx, Y_C, e.FLOOR)

    stem_bot_z = cz - USBC_SOCK_STEM_H / 2      # 8.525 mm
    rail_h = (stem_bot_z - 0.175) - e.FLOOR     # 5.95 mm
    cheek_h = (cz + h / 2 + 0.40) - e.FLOOR     # 12.10 mm (Z = 2.40..14.50 mm open-top U-channel behind collar)
    guide_len = 14.20 - USBC_SOCK_PANEL_T       # 13.10 mm
    guide_cx = (x_seat - USBC_SOCK_PANEL_T) - guide_len / 2
    for sy in (-1, 1):
        nose_blk = nose_blk.union(e.box(guide_len, 2.2, rail_h, guide_cx, Y_C + sy * 3.8, e.FLOOR))
        cheek_in_y = w_throat / 2 - 0.1         # 6.50 mm
        cheek_out_y = outer_w / 2               # clipped by outer_env
        cheek_w = cheek_out_y - cheek_in_y
        nose_blk = nose_blk.union(
            e.box(guide_len + 0.4, cheek_w, cheek_h, guide_cx, Y_C + sy * (cheek_in_y + cheek_w / 2), e.FLOOR)
        )
    base = base.union(nose_blk.intersect(outer_env))

    # 2. Sculpted Flush Architectural Bezel Alcove (X = +28.50..+32.50 mm):
    #    17.10 x 11.00 mm oval pocket at X = +28.50..+30.30 mm flaring outward at 45 deg to 19.50 x 13.40 mm at X = +32.00 mm
    alcove_w0 = USBC_SOCK_BEZEL_W + 0.60       # 17.10 mm
    alcove_h0 = USBC_SOCK_BEZEL_H + 0.60       # 11.00 mm
    alcove_seat = (
        cq.Workplane("YZ")
        .workplane(offset=x_seat)
        .center(Y_C, cz)
        .rect(alcove_w0, alcove_h0)
        .extrude(4.0)
        .edges("|X")
        .fillet(4.9)
    )
    alcove_flare = (
        cq.Workplane("YZ")
        .workplane(offset=x_seat + 1.60)
        .center(Y_C, cz)
        .rect(alcove_w0 + 2.40, alcove_h0 + 2.40)
        .extrude(2.4)
        .edges("|X")
        .fillet(6.1)
        .faces("<X")
        .edges()
        .chamfer(1.15)
    )
    base = base.cut(alcove_seat.union(alcove_flare))

    # 3. Zone 1A (d = 0.00..0.45 mm from x_seat): Entry lead-in mouth (13.60 x 6.00 mm)
    lead_in = (
        cq.Workplane("YZ")
        .workplane(offset=x_seat - 0.45)
        .center(Y_C, cz)
        .rect(w_guide + 0.20, h + 0.20)
        .extrude(0.60)
        .edges("|X")
        .fillet(0.5)
    )
    # 4. Zone 1B (d = 0.45..1.10 mm from x_seat): Station #4 13.20 x 5.80 mm clip-locking collar
    throat = (
        cq.Workplane("YZ")
        .workplane(offset=x_seat - USBC_SOCK_PANEL_T - 0.10)
        .center(Y_C, cz)
        .rect(w_throat, h)
        .extrude(USBC_SOCK_PANEL_T + 0.30)
        .edges("|X")
        .fillet(0.5)
    )
    # 5. Zone 2 (d = 1.10..5.80 mm from x_seat): 16.80 x 5.80 mm snap-clip expansion chamber
    pocket_len = USBC_SOCK_POCKET_END - USBC_SOCK_PANEL_T
    wing_chamber = e.box(
        pocket_len,
        w_exp,
        h,
        x_seat - USBC_SOCK_PANEL_T - pocket_len / 2,
        Y_C,
        cz - h / 2,
    )
    # 6. Support-free 45 deg transition (d = 5.80..7.00 mm) from 16.80 mm chamber to 13.40 mm guide sleeve
    taper = (
        cq.Workplane("YZ")
        .workplane(offset=x_seat - USBC_SOCK_POCKET_END + 0.05)
        .center(Y_C, cz)
        .rect(w_exp, h)
        .workplane(offset=-1.20)
        .rect(w_guide, h)
        .loft()
    )
    # 7. Zone 3 (d = 5.80..14.60 mm, X = +14.90..+23.70 mm): 13.40 x 5.80 mm coaxial rear stem guide sleeve
    guide = (
        cq.Workplane("YZ")
        .workplane(offset=x_seat - 14.60)
        .center(Y_C, cz)
        .rect(w_guide, h)
        .extrude(14.60 - USBC_SOCK_POCKET_END + 0.20)
        .edges("|X")
        .fillet(0.5)
    )
    return base.cut(lead_in).cut(throat).cut(wing_chamber).cut(taper).cut(guide)


def _add_aura_v2_board_cradle(base: cq.Workplane, inner_w: float) -> cq.Workplane:
    """Lower-tier cradle for direct-soldered SuperMini nRF52840 at BOARD_AURA_V2_X (Z = 5.4..6.6 mm)."""
    z_top = e.FLOOR + BOARD_V2_RAIL_H + e.BOARD_T           # 6.60 mm
    stop_h = BOARD_V2_RAIL_H + e.BOARD_T + e.STOP_ABOVE     # 6.00 mm (Z_max = 8.40 mm)
    end_pad_l = (e.BOARD_L - e.BOARD_PIN_ROW_L) / 2 - 0.2  # 2.30 mm
    end_pad_w = 3.4
    stop_t = 1.6

    # Central cross-tie + two inset longitudinal rails clear of the 28.0 x 2.2 mm direct-solder pad rows
    base = base.union(e.box(3.2, e.BOARD_W - 2 * e.BOARD_PIN_SPAN_Y - 2.0, BOARD_V2_RAIL_H, BOARD_AURA_V2_X, Y_C, e.FLOOR))
    for sy in (-1, 1):
        inset_y = Y_C + sy * (e.BOARD_W / 2 - e.BOARD_PIN_SPAN_Y - 1.8)
        base = base.union(e.box(e.BOARD_L - 10.0, e.RAIL_W, BOARD_V2_RAIL_H, BOARD_AURA_V2_X, inset_y, e.FLOOR))
        y_in = Y_C + sy * (e.BOARD_W / 2 + e.BOARD_CLEAR)  # +/-9.15 mm
        for sx in (-1, 1):
            # Stay inside the curved -X stadium wall at sx = -1 while fusing into the wall
            y_out = sy * (11.2 if sx < 0 else (inner_w / 2 - 0.8))
            y_w = abs(y_out - y_in)
            px = BOARD_AURA_V2_X + sx * (e.BOARD_L / 2 - end_pad_l / 2)
            py = Y_C + sy * (e.BOARD_W / 2 - end_pad_w / 2)
            base = base.union(e.box(end_pad_l, end_pad_w, BOARD_V2_RAIL_H, px, py, e.FLOOR))
            stop_w_x = 2.3
            sxp_y = BOARD_AURA_V2_X + sx * (e.BOARD_L / 2 + e.BOARD_CLEAR - stop_w_x / 2)
            base = base.union(e.box(stop_w_x, y_w, stop_h, sxp_y, (y_in + y_out) / 2, e.FLOOR))
            base = base.union(e._snap_hook_x(px, end_pad_l, y_in, sy, z_top, e.BOARD_SNAP_OVERHANG))
            sxp = BOARD_AURA_V2_X + sx * (e.BOARD_L / 2 + e.BOARD_CLEAR + stop_t / 2)
            syp = Y_C + sy * (e.BOARD_W / 2 + e.BOARD_CLEAR - 3.6 / 2)
            base = base.union(e.box(stop_t, 3.6, stop_h, sxp, syp, e.FLOOR))
    return base


def _add_aura_s_v2_radar_cradle(base: cq.Workplane) -> cq.Workplane:
    """Upper-tier stepped amphitheater cradle for 20x20 mm HLK-LD2410S stacked at Z = 15.9..17.1 mm over SuperMini."""
    z_bot = e.FLOOR + RADAR_V2_RAIL_H                       # 15.90 mm
    z_top = z_bot + e.RADAR_T                               # 17.10 mm
    stop_h = RADAR_V2_RAIL_H + e.RADAR_T + 0.45             # 15.15 mm (Z_max = 17.55 mm, clears lid lip at Z = 17.80 mm)
    rail_l = 13.0                                           # spans X = -17.0..-4.0 mm (between SuperMini corner hooks)
    rail_cx = RADAR_AURA_V2_X                               # -10.50 mm
    y_rad_in = e.RADAR_W / 2 + e.BOARD_CLEAR                # 10.15 mm
    y_rad_ledge = 9.30                                      # 0.70 mm ledge/side; >9.15 mm so SuperMini drops straight through!
    y_wall_out = 11.50                                      # clears lid lip inner face
    neg_x_face = RADAR_AURA_V2_X - e.RADAR_L / 2 - e.BOARD_CLEAR  # -20.65 mm
    pos_x_face = RADAR_AURA_V2_X + e.RADAR_L / 2 + e.BOARD_CLEAR  # -0.35 mm

    for sy in (-1, 1):
        # 1. Stepped amphitheater side column (|Y| = 9.30..13.80 mm up to Z=15.90, stepping out to 10.15 mm above Z=15.90)
        y_outer = sy * (INNER_W_AURA / 2 - 0.8)
        y_l = sy * y_rad_ledge
        y_w = sy * y_rad_in
        y_pocket_out = sy * y_wall_out
        base = base.union(e.box(rail_l, abs(y_outer - y_l), RADAR_V2_RAIL_H, rail_cx, (y_outer + y_l) / 2, e.FLOOR))
        base = base.union(e.box(rail_l, abs(y_pocket_out - y_w), stop_h, rail_cx, (y_pocket_out + y_w) / 2, e.FLOOR))
        base = base.union(e._snap_hook_x(rail_cx, 7.6, y_w, sy, z_top, e.RADAR_SNAP_OVERHANG))

        # 2. Continuous upper side beam (Z = 11.80..15.90 mm, |Y| = 9.30..11.20 mm) spanning X = -22.25..+1.25 mm
        #    uniting the -X and +X radar end-stops with the central side column (zero overlap with crystal or SuperMini)
        z_br_bot = 11.80
        br_h = (e.FLOOR + stop_h) - z_br_bot
        span_x = (pos_x_face + 1.6) - (neg_x_face - 1.6)
        span_cx = (pos_x_face + neg_x_face) / 2
        base = base.union(e.box(span_x, 1.90, z_bot - z_br_bot, span_cx, sy * 10.25, z_br_bot))

        # -X axial stop block (X = -22.25..-20.65 mm, |Y| = 6.20..11.20 mm, Z = 11.80..17.55 mm)
        base = base.union(e.box(1.6, 5.00, br_h, neg_x_face - 0.8, sy * 8.70, z_br_bot))
        if sy < 0:
            # (+X, -Y) axial stop block (leaves +Y side open for asymmetric 5-pin J2 direct-soldered wires)
            base = base.union(e.box(1.6, 5.00, br_h, pos_x_face + 0.8, sy * 8.70, z_br_bot))
    return base


def _add_aura_c_v2_radar_cradle(base: cq.Workplane) -> cq.Workplane:
    """Upper-tier corbelled cradle for 22x16 mm HLK-LD2410C stacked at Z = 15.9..17.1 mm over SuperMini."""
    z_bot = e.FLOOR + RADAR_V2_RAIL_H                       # 15.90 mm
    z_top = z_bot + RADAR_C_T                               # 17.10 mm
    stop_h = RADAR_V2_RAIL_H + RADAR_C_T + 0.45             # 15.15 mm (Z_max = 17.55 mm)
    rail_l = 12.0                                           # spans X = -16.5..-4.5 mm
    rail_cx = RADAR_AURA_V2_X                               # -10.50 mm
    y_rad_in = RADAR_C_W / 2 + e.BOARD_CLEAR                # 8.15 mm
    z_corbel_bot = 11.40                                    # starts 3.0 mm above SuperMini shield (Z = 8.40 mm)
    neg_x_face = RADAR_AURA_V2_X - RADAR_C_L / 2 - e.BOARD_CLEAR  # -21.65 mm
    pos_x_face = RADAR_AURA_V2_X + RADAR_C_L / 2 + e.BOARD_CLEAR  # +0.65 mm

    for sy in (-1, 1):
        # 1. Lower side wall (Z = 2.40..11.40 mm) stays outside |Y| = 9.30 mm to clear 18.0 mm SuperMini
        y_outer = sy * (INNER_W_AURA_C / 2 - 0.8)           # +/-12.80 mm
        y_low_in = sy * 9.30
        base = base.union(
            e.box(rail_l, abs(y_outer - y_low_in), z_corbel_bot - e.FLOOR, rail_cx, (y_outer + y_low_in) / 2, e.FLOOR)
        )
        # 2. Support-free ~24 deg inward corbel (Z = 11.40..15.90 mm) from |Y| = 9.30 mm to |Y| = 7.35 mm
        corbel = (
            cq.Workplane("XY")
            .workplane(offset=z_corbel_bot - 0.1)
            .center(rail_cx, sy * 10.65)
            .rect(rail_l, 2.70)
            .workplane(offset=(z_bot - z_corbel_bot) + 0.1)
            .center(0.0, sy * (8.95 - 10.65))
            .rect(rail_l, 3.20)
            .loft()
        )
        base = base.union(corbel)
        # 3. Upper radar pocket wall (Z = 15.90..17.55 mm, |Y| = 8.15..10.45 mm) + snap hook
        y_w = sy * y_rad_in
        y_p_out = sy * 10.45
        base = base.union(
            e.box(rail_l, abs(y_p_out - y_w), (e.FLOOR + stop_h) - z_bot + 0.2, rail_cx, (y_p_out + y_w) / 2, z_bot - 0.2)
        )
        base = base.union(e._snap_hook_x(rail_cx, 7.2, y_w, sy, z_top, e.RADAR_SNAP_OVERHANG))

        # 4. Continuous upper side beam (Z = 12.20..15.90 mm, |Y| = 8.15..10.25 mm) spanning X = -23.15..+2.15 mm
        #    uniting the -X and +X corner stops with the central corbel (strictly outside |Y| = 8.15 mm and Z <= z_bot)
        z_br_bot = 12.20
        br_h = (e.FLOOR + stop_h) - z_br_bot
        span_x = (pos_x_face + 1.5) - (neg_x_face - 1.5)
        span_cx = (pos_x_face + neg_x_face) / 2
        base = base.union(e.box(span_x, 2.10, z_bot - z_br_bot, span_cx, sy * 9.20, z_br_bot))

        # -X and +X corner stops (|Y| = 5.00..10.25 mm; 10.0 mm central +X wire channel)
        base = base.union(e.box(1.5, 5.25, br_h, neg_x_face - 0.75, sy * 7.625, z_br_bot))
        base = base.union(e.box(1.5, 5.25, br_h, pos_x_face + 0.75, sy * 7.625, z_br_bot))
    return base


def make_aura_s_v2_base() -> cq.Workplane:
    """Build compact 'Aura-S v2' stacked stadium base (64.0 x 34.0 x 20.4 mm) for direct-soldered 20x20 mm HLK-LD2410S."""
    base = (
        e.rrect(OUTER_L_AURA_V2, OUTER_W_AURA, OUTER_R_AURA, 0.0, H_AURA_V2)
        .edges("<Z")
        .chamfer(1.4)
        .edges(">Z")
        .chamfer(0.5)
    )
    base = base.cut(e.rrect(INNER_L_AURA_V2, INNER_W_AURA, INNER_R_AURA, e.FLOOR, DEPTH_AURA_V2 + 1.0))

    groove_l = SNAP_L_AURA_V2 + 1.0
    groove_h = SNAP_BEAD_H + 0.24
    groove_z = (H_AURA_V2 - 2.05) - 0.12
    groove_depth_y = SNAP_ENGAGE + 0.25
    for sx in (-1, 1):
        for sy in (-1, 1):
            gy = sy * (INNER_W_AURA / 2 + (groove_depth_y / 2 - 0.10))
            base = base.cut(e.box(groove_l, groove_depth_y, groove_h, sx * SNAP_X_AURA_V2, gy, groove_z))

    base = base.cut(e.box(1.4, 6.0, 0.8, -OUTER_L_AURA_V2 / 2 + 0.6, 0.0, H_AURA_V2 - 0.7))
    base = _add_aura_v2_board_cradle(base, inner_w=INNER_W_AURA)
    base = _add_aura_s_v2_radar_cradle(base)
    base = _add_v_stand_mortise(
        base, OUTER_W_AURA, mortise_z0=V_MORTISE_V2_Z0, mortise_l_z=V_MORTISE_V2_L_Z, y_boss_in=-10.35
    )
    return _add_aura_v2_side_usbc_bay(base, outer_w=OUTER_W_AURA, outer_r=OUTER_R_AURA, extra_w=USBC_SOCK_EXTRA_W)


def make_aura_s_v2_lid() -> cq.Workplane:
    """Build compact 'Aura-S v2' stadium bezel lid (64.0 x 34.0 mm) with 22x22x1.2 mm blind RF radome."""
    lid = (
        e.rrect(OUTER_L_AURA_V2, OUTER_W_AURA, OUTER_R_AURA, H_AURA_V2, e.LID_T)
        .edges(">Z")
        .chamfer(1.8)
        .edges("<Z")
        .chamfer(0.5)
    )
    groove_out = e.rrect(
        OUTER_L_AURA_V2 - 7.2, OUTER_W_AURA - 7.2, OUTER_R_AURA - 3.6, H_AURA_V2 + e.LID_T - 0.45, 0.6
    )
    groove_in = e.rrect(
        OUTER_L_AURA_V2 - 8.8, OUTER_W_AURA - 8.8, OUTER_R_AURA - 4.4, H_AURA_V2 + e.LID_T - 0.55, 0.8
    )
    lid = lid.cut(groove_out.cut(groove_in))

    lip_l, lip_w = INNER_L_AURA_V2 - 2 * e.LIP_CLEAR, INNER_W_AURA - 2 * e.LIP_CLEAR
    lip_r = INNER_R_AURA - e.LIP_CLEAR
    lip = (
        e.rrect(lip_l, lip_w, lip_r, H_AURA_V2 - e.LIP_H, e.LIP_H)
        .cut(e.rrect(lip_l - 2 * e.LIP_T, lip_w - 2 * e.LIP_T, lip_r - e.LIP_T, H_AURA_V2 - e.LIP_H - 1, e.LIP_H + 2))
    )
    lid = lid.union(lip)

    snap_z_bot = H_AURA_V2 - 2.05
    for sx in (-1, 1):
        for sy in (-1, 1):
            lid = lid.union(_snap_bead_x(sx * SNAP_X_AURA_V2, SNAP_L_AURA_V2, INNER_W_AURA, sy, snap_z_bot))

    radome_pocket = e.rrect(e.RADOME_L, e.RADOME_W, 3.5, H_AURA_V2 - 0.1, e.RADOME_DEPTH + 0.1).translate(
        (RADAR_AURA_V2_X, Y_C, 0.0)
    )
    lid = lid.cut(radome_pocket)

    rad_hold_z0 = e.FLOOR + RADAR_V2_RAIL_H + e.RADAR_T + 0.30
    rad_hold_h = (H_AURA_V2 + e.RADOME_DEPTH) - rad_hold_z0 + 0.2
    for cx, cy in [
        (RADAR_AURA_V2_X - 8.2, Y_C - 8.2),
        (RADAR_AURA_V2_X - 8.2, Y_C + 8.2),
        (RADAR_AURA_V2_X + 8.2, Y_C - 8.2),
    ]:
        lid = lid.union(e.box(2.4, 2.4, rad_hold_h, cx, cy, rad_hold_z0))
    return lid


def make_aura_s_v2_stand() -> cq.Workplane:
    """Build compact 'Aura-S v2' beveled Inverted-V (ʌ) floating pedestal (50 mm footprint, 19.4 mm depth)."""
    return (
        make_v_stand(
            outer_w=OUTER_W_AURA,
            depth_z=V_STAND_V2_DEPTH_Z,
            bot_w=V_STAND_V2_BOT_W,
            mortise_z0=V_MORTISE_V2_Z0,
            mortise_l_z=V_MORTISE_V2_L_Z,
        )
        .edges(">Z")
        .chamfer(1.2)
    )


def make_aura_c_v2_base() -> cq.Workplane:
    """Build compact 'Aura-C v2' stacked stadium base (64.0 x 32.0 x 20.4 mm) for direct-soldered 22x16 mm HLK-LD2410C."""
    base = (
        e.rrect(OUTER_L_AURA_V2, OUTER_W_AURA_C, OUTER_R_AURA_C, 0.0, H_AURA_V2)
        .edges("<Z")
        .chamfer(1.4)
        .edges(">Z")
        .chamfer(0.5)
    )
    base = base.cut(e.rrect(INNER_L_AURA_V2, INNER_W_AURA_C, INNER_R_AURA_C, e.FLOOR, DEPTH_AURA_V2 + 1.0))

    groove_l = SNAP_L_AURA_V2 + 1.0
    groove_h = SNAP_BEAD_H + 0.24
    groove_z = (H_AURA_V2 - 2.05) - 0.12
    groove_depth_y = SNAP_ENGAGE + 0.25
    for sx in (-1, 1):
        for sy in (-1, 1):
            gy = sy * (INNER_W_AURA_C / 2 + (groove_depth_y / 2 - 0.10))
            base = base.cut(e.box(groove_l, groove_depth_y, groove_h, sx * SNAP_X_AURA_V2, gy, groove_z))

    base = base.cut(e.box(1.4, 6.0, 0.8, -OUTER_L_AURA_V2 / 2 + 0.6, 0.0, H_AURA_V2 - 0.7))
    base = _add_aura_v2_board_cradle(base, inner_w=INNER_W_AURA_C)
    base = _add_aura_c_v2_radar_cradle(base)
    base = _add_v_stand_mortise(
        base, OUTER_W_AURA_C, mortise_z0=V_MORTISE_V2_Z0, mortise_l_z=V_MORTISE_V2_L_Z, y_boss_in=-10.35
    )
    return _add_aura_v2_side_usbc_bay(base, outer_w=OUTER_W_AURA_C, outer_r=OUTER_R_AURA_C, extra_w=USBC_SOCK_EXTRA_W)


def make_aura_c_v2_lid() -> cq.Workplane:
    """Build compact 'Aura-C v2' stadium bezel lid (64.0 x 32.0 mm) with 24x18x1.2 mm blind RF radome."""
    lid = (
        e.rrect(OUTER_L_AURA_V2, OUTER_W_AURA_C, OUTER_R_AURA_C, H_AURA_V2, e.LID_T)
        .edges(">Z")
        .chamfer(1.8)
        .edges("<Z")
        .chamfer(0.5)
    )
    groove_out = e.rrect(
        OUTER_L_AURA_V2 - 7.2, OUTER_W_AURA_C - 7.2, OUTER_R_AURA_C - 3.6, H_AURA_V2 + e.LID_T - 0.45, 0.6
    )
    groove_in = e.rrect(
        OUTER_L_AURA_V2 - 8.8, OUTER_W_AURA_C - 8.8, OUTER_R_AURA_C - 4.4, H_AURA_V2 + e.LID_T - 0.55, 0.8
    )
    lid = lid.cut(groove_out.cut(groove_in))

    lip_l, lip_w = INNER_L_AURA_V2 - 2 * e.LIP_CLEAR, INNER_W_AURA_C - 2 * e.LIP_CLEAR
    lip_r = INNER_R_AURA_C - e.LIP_CLEAR
    lip = (
        e.rrect(lip_l, lip_w, lip_r, H_AURA_V2 - e.LIP_H, e.LIP_H)
        .cut(e.rrect(lip_l - 2 * e.LIP_T, lip_w - 2 * e.LIP_T, lip_r - e.LIP_T, H_AURA_V2 - e.LIP_H - 1, e.LIP_H + 2))
    )
    lid = lid.union(lip)

    snap_z_bot = H_AURA_V2 - 2.05
    for sx in (-1, 1):
        for sy in (-1, 1):
            lid = lid.union(_snap_bead_x(sx * SNAP_X_AURA_V2, SNAP_L_AURA_V2, INNER_W_AURA_C, sy, snap_z_bot))

    radome_pocket = e.rrect(RADOME_C_L, RADOME_C_W, 3.0, H_AURA_V2 - 0.1, e.RADOME_DEPTH + 0.1).translate(
        (RADAR_AURA_V2_X, Y_C, 0.0)
    )
    lid = lid.cut(radome_pocket)

    rad_hold_z0 = e.FLOOR + RADAR_V2_RAIL_H + RADAR_C_T + 0.30
    rad_hold_h = (H_AURA_V2 + e.RADOME_DEPTH) - rad_hold_z0 + 0.2
    for sx in (-1, 1):
        for sy in (-1, 1):
            lid = lid.union(e.box(2.4, 2.4, rad_hold_h, RADAR_AURA_V2_X + sx * 9.2, Y_C + sy * 6.4, rad_hold_z0))
    return lid


def make_aura_c_v2_stand() -> cq.Workplane:
    """Build compact 'Aura-C v2' beveled Inverted-V (ʌ) floating pedestal (50 mm footprint, 19.4 mm depth)."""
    return (
        make_v_stand(
            outer_w=OUTER_W_AURA_C,
            depth_z=V_STAND_V2_DEPTH_Z,
            bot_w=V_STAND_V2_BOT_W,
            mortise_z0=V_MORTISE_V2_Z0,
            mortise_l_z=V_MORTISE_V2_L_Z,
        )
        .edges(">Z")
        .chamfer(1.2)
    )


def make_aura_s_v2_dummies() -> dict[str, cq.Workplane]:
    """Dummies for 'Aura-S v2': lower SuperMini + upper stacked 20x20 mm HLK-LD2410S (direct-soldered) + rear USB-C."""
    z_brd_bot = e.FLOOR + BOARD_V2_RAIL_H
    z_brd_top = z_brd_bot + e.BOARD_T
    board = e.box(e.BOARD_L, e.BOARD_W, e.BOARD_T, BOARD_AURA_V2_X, Y_C, z_brd_bot)
    board_parts = (
        e.box(7.5, 9.2, 3.2, BOARD_AURA_V2_X + e.BOARD_L / 2 - 3.2, Y_C, z_brd_top)
        .union(e.box(20.0, 12.0, 1.8, BOARD_AURA_V2_X - 2.0, Y_C, z_brd_top))
        .union(e.box(e.BOARD_PIN_ROW_L, e.BOARD_PIN_SPAN_Y, e.BOARD_PIN_DEPTH,
                     BOARD_AURA_V2_X, Y_C - e.BOARD_W / 2 + e.BOARD_PIN_SPAN_Y / 2, z_brd_bot - e.BOARD_PIN_DEPTH))
        .union(e.box(e.BOARD_PIN_ROW_L, e.BOARD_PIN_SPAN_Y, e.BOARD_PIN_DEPTH,
                     BOARD_AURA_V2_X, Y_C + e.BOARD_W / 2 - e.BOARD_PIN_SPAN_Y / 2, z_brd_bot - e.BOARD_PIN_DEPTH))
    )

    z_rad_bot = e.FLOOR + RADAR_V2_RAIL_H
    z_rad_top = z_rad_bot + e.RADAR_T
    radar = e.rrect(e.RADAR_L, e.RADAR_W, e.RADAR_CORNER_R, z_rad_bot, e.RADAR_T).translate((RADAR_AURA_V2_X, Y_C, 0))
    x_rad_left, x_rad_right = RADAR_AURA_V2_X - e.RADAR_L / 2, RADAR_AURA_V2_X + e.RADAR_L / 2
    y_rad_bot, y_rad_top = Y_C - e.RADAR_W / 2, Y_C + e.RADAR_W / 2
    j2_cy = y_rad_top - (0.35 + 13.05) / 2
    # Direct-soldered pads (1.2 mm solder dome height instead of 2.6 mm pin header)
    radar_parts = (
        e.box(10.0, 10.0, 1.0, RADAR_AURA_V2_X, Y_C, z_rad_top)
        .union(e.box(1.8, 11.5, 1.2, x_rad_right - 1.47, j2_cy, z_rad_top))
        .union(e.box(8.0, 8.0, 1.0, RADAR_AURA_V2_X, Y_C, z_rad_bot - 1.0))
        .union(e.box(3.5, 3.2, 1.2, x_rad_left + 2.75, y_rad_bot + 2.60, z_rad_bot - 1.2))
    )
    # Direct-soldered wire harness dropping from radar +X solder pads to SuperMini pads below
    direct_wires = e.box(2.4, 8.0, 5.8, x_rad_right - 1.2, Y_C + 1.5, z_brd_top + 2.2)

    x_seat = USBC_AURA_V2_X_SEAT
    cz = USBC_AURA_V2_Z
    bezel = (
        cq.Workplane("YZ")
        .workplane(offset=x_seat + 0.05)
        .center(Y_C, cz)
        .rect(USBC_SOCK_BEZEL_W, USBC_SOCK_BEZEL_H)
        .extrude(USBC_SOCK_BEZEL_T)
        .edges("|X")
        .fillet(4.8)
    )
    waist = (
        e.box(
            1.25,
            USBC_SOCK_WAIST_W,
            USBC_SOCK_STEM_H,
            x_seat - 1.25 / 2,
            Y_C,
            cz - USBC_SOCK_STEM_H / 2,
        )
        .edges("|X")
        .fillet(0.6)
    )
    stem = (
        e.box(
            USBC_SOCK_STEM_L - 1.25,
            USBC_SOCK_STEM_W,
            USBC_SOCK_STEM_H,
            x_seat - 1.25 - (USBC_SOCK_STEM_L - 1.25) / 2,
            Y_C,
            cz - USBC_SOCK_STEM_H / 2,
        )
        .edges("|X")
        .fillet(0.6)
    )
    wings = e.box(
        4.25,
        USBC_SOCK_WING_W,
        4.6,
        x_seat - 1.25 - 4.25 / 2,
        Y_C,
        cz - 2.3,
    )
    usb_c_socket = bezel.union(waist).union(stem).union(wings)
    usb_c_plug = e.box(14.0, 11.4, 6.0, x_seat + USBC_SOCK_BEZEL_T + 7.1, Y_C, cz - 3.0)

    return {
        "board": board,
        "board_parts": board_parts,
        "radar": radar,
        "radar_parts": radar_parts,
        "direct_wires": direct_wires,
        "usb_c_socket": usb_c_socket,
        "usb_c_plug": usb_c_plug,
    }


def make_aura_c_v2_dummies() -> dict[str, cq.Workplane]:
    """Dummies for 'Aura-C v2': lower SuperMini + upper stacked 22x16 mm HLK-LD2410C (direct-soldered) + rear USB-C."""
    dm = make_aura_s_v2_dummies()
    z_rad_bot = e.FLOOR + RADAR_V2_RAIL_H
    z_rad_top = z_rad_bot + RADAR_C_T
    radar = e.rrect(RADAR_C_L, RADAR_C_W, RADAR_C_CORNER_R, z_rad_bot, RADAR_C_T).translate((RADAR_AURA_V2_X, Y_C, 0))
    x_rad_left, x_rad_right = RADAR_AURA_V2_X - RADAR_C_L / 2, RADAR_AURA_V2_X + RADAR_C_L / 2
    y_rad_bot = Y_C - RADAR_C_W / 2
    radar_parts = (
        e.box(10.0, 10.0, 1.0, RADAR_AURA_V2_X, Y_C, z_rad_top)
        .union(e.box(1.8, 6.8, 1.2, x_rad_right - 1.3, Y_C, z_rad_top))
        .union(e.box(8.0, 8.0, 1.0, RADAR_AURA_V2_X, Y_C, z_rad_bot - 1.0))
        .union(e.box(3.5, 3.2, 1.2, x_rad_left + 2.75, y_rad_bot + 2.60, z_rad_bot - 1.2))
    )
    dm["radar"] = radar
    dm["radar_parts"] = radar_parts
    dm["direct_wires"] = e.box(2.2, 6.8, 5.8, x_rad_right - 1.2, Y_C, e.FLOOR + BOARD_V2_RAIL_H + e.BOARD_T + 2.2)
    return dm


# Aliases for aura_v2 default (HLK-LD2410S)
make_aura_v2_base = make_aura_s_v2_base
make_aura_v2_lid = make_aura_s_v2_lid
make_aura_v2_stand = make_aura_s_v2_stand
make_aura_v2_dummies = make_aura_s_v2_dummies


# --------------------------------------------------------------------------------------
# 4-Station Dual-Orientation USB-C Clip-Retention Test Gauge (12.6, 12.8, 13.0, 13.2 mm clip throats)
# --------------------------------------------------------------------------------------

def make_usbc_socket_fit_test() -> cq.Workplane:
    """Build 4-station dual-orientation USB-C clip-retention test block (Z=0 Aura rear bay + +X side bay per station)."""
    pitch_y = 24.0
    n_stations = len(USBC_RETENTION_TEST_THROATS)
    total_w_y = n_stations * pitch_y + 2 * e.WALL
    wall_h = 18.0
    inner_x0 = 8.0
    aura_test_x = 18.0                                      # Z=0 rear-entry Aura test bay center X
    inner_x1 = INNER_L_C / 2                                # +41.0 mm (+X side-entry test bay inner wall)
    outer_x1 = OUTER_L_C / 2                                # +43.4 mm (+X side-entry test bay outer face)
    label_tab_len = 11.5                                    # front horizontal label apron (X = +43.4..+54.9 mm)
    base_len_x = (outer_x1 + label_tab_len) - inner_x0

    # Continuous floor + front label apron + side boundary walls + +X socket wall
    gauge = e.box(base_len_x, total_w_y, e.FLOOR, inner_x0 + base_len_x / 2, 0.0, 0.0)
    gauge = gauge.union(e.box(e.WALL, total_w_y, wall_h, inner_x1 + e.WALL / 2, 0.0, 0.0))
    for sy in (-1, 1):
        end_y = sy * (total_w_y / 2 - e.WALL / 2)
        gauge = gauge.union(e.box(outer_x1 - inner_x0, e.WALL, wall_h, (inner_x0 + outer_x1) / 2, end_y, 0.0))

    for i, throat_w in enumerate(USBC_RETENTION_TEST_THROATS):
        cy = (i - (n_stations - 1) / 2) * pitch_y
        # 1. +X side-entry 3-zone clip-retention bay (matches ld2410c & ld2410s_usb)
        gauge = _add_usbc_socket_bay(
            gauge, inner_l=INNER_L_C, inner_w=pitch_y, extra_w=0.0, cy=cy, throat_w=throat_w
        )
        # 2. Z=0 rear-entry 3-zone clip-retention bay (matches Aura-S & Aura-C)
        gauge = _add_aura_rear_usbc_bay(
            gauge, extra_w=0.0, cx=aura_test_x, cy=cy, throat_w=throat_w
        )
        if i > 0:
            div_y = cy - pitch_y / 2
            gauge = gauge.union(e.box(outer_x1 - inner_x0, 1.6, wall_h, (inner_x0 + outer_x1) / 2, div_y, 0.0))

        # Embossed descriptive text on the flat front apron (support-free XY plane, 0.8 mm raised):
        # Shows the clip-locking collar width ("12.6mm", "12.8mm", "13.0mm", "13.2mm") paired with the 13.4 mm stem sleeve
        throat_label = f"{throat_w:.1f}mm"
        stem_label = f"(13.4)"
        txt_throat = (
            cq.Workplane("XY")
            .workplane(offset=e.FLOOR - 0.1)
            .transformed(offset=(outer_x1 + 3.8, cy, 0.0), rotate=(0.0, 0.0, 90.0))
            .text(throat_label, fontsize=4.1, distance=0.9, halign="center", valign="center")
        )
        txt_stem = (
            cq.Workplane("XY")
            .workplane(offset=e.FLOOR - 0.1)
            .transformed(offset=(outer_x1 + 8.3, cy, 0.0), rotate=(0.0, 0.0, 90.0))
            .text(stem_label, fontsize=3.4, distance=0.9, halign="center", valign="center")
        )
        gauge = gauge.union(txt_throat).union(txt_stem)
    return gauge


def make_ld2410c_dummies() -> dict[str, cq.Workplane]:
    """Dummies for compact battery-free Model 4: SuperMini + 22x16 mm HLK-LD2410C + AliExpress USB-C socket."""
    z_brd_bot = e.FLOOR + e.BOARD_RAIL_H
    z_brd_top = z_brd_bot + e.BOARD_T
    board = e.box(e.BOARD_L, e.BOARD_W, e.BOARD_T, BOARD_C_X, Y_C, z_brd_bot)
    board_parts = (
        e.box(7.5, 9.2, 3.2, BOARD_C_X + e.BOARD_L / 2 - 3.2, Y_C, z_brd_top)
        .union(e.box(20.0, 12.0, 1.8, BOARD_C_X - 2.0, Y_C, z_brd_top))
        .union(e.box(e.BOARD_PIN_ROW_L, e.BOARD_PIN_SPAN_Y, e.BOARD_PIN_DEPTH,
                     BOARD_C_X, Y_C - e.BOARD_W / 2 + e.BOARD_PIN_SPAN_Y / 2, z_brd_bot - e.BOARD_PIN_DEPTH))
        .union(e.box(e.BOARD_PIN_ROW_L, e.BOARD_PIN_SPAN_Y, e.BOARD_PIN_DEPTH,
                     BOARD_C_X, Y_C + e.BOARD_W / 2 - e.BOARD_PIN_SPAN_Y / 2, z_brd_bot - e.BOARD_PIN_DEPTH))
    )

    z_rad_bot = e.FLOOR + RADAR_C_RAIL_H
    z_rad_top = z_rad_bot + RADAR_C_T
    radar = e.rrect(RADAR_C_L, RADAR_C_W, RADAR_C_CORNER_R, z_rad_bot, RADAR_C_T).translate((RADAR_C_X, Y_C, 0))
    x_rad_left, x_rad_right = RADAR_C_X - RADAR_C_L / 2, RADAR_C_X + RADAR_C_L / 2
    y_rad_bot = Y_C - RADAR_C_W / 2
    radar_parts = (
        e.box(10.0, 10.0, 1.0, RADAR_C_X, Y_C, z_rad_top)
        .union(e.box(2.0, 6.8, e.RADAR_PARTS_H, x_rad_right - 1.3, Y_C, z_rad_top))
        .union(e.box(8.0, 8.0, 1.0, RADAR_C_X, Y_C, z_rad_bot - 1.0))
        .union(e.box(3.5, 3.2, 1.2, x_rad_left + 2.75, y_rad_bot + 2.60, z_rad_bot - 1.2))
    )
    # 5-pin 1.27 mm pitch connector & wire harness exiting +X edge of HLK-LD2410C
    dupont_5p = e.box(2.6, 7.6, 12.0, x_rad_right - 1.3, Y_C, z_rad_bot - 12.0).union(
        e.box(2.8, 7.6, 5.0, x_rad_right + 1.4, Y_C, z_rad_bot - 12.0)
    )

    # AliExpress 2-Pin Panel-Mount USB-C Socket (1005008559159734):
    # - 16.5 x 10.4 x 2.0 mm exterior oval bezel flush against +X outer wall (X = +43.45..+45.45 mm)
    # - 12.3 x 5.35 mm clip-locking waist (d = 0..1.25 mm) inside the 12.8 x 5.8 mm locking collar
    # - 15.8 mm snap-fit clip barbs (d = 1.25..5.50 mm) locked behind the d = 1.10 mm 90 deg shoulder
    # - 13.0 x 5.35 mm rigid rear stem (d = 1.25..14.00 mm) guided coaxially by the 13.4 x 5.8 mm sleeve
    x_wall_out = OUTER_L_C / 2
    bezel = (
        cq.Workplane("YZ")
        .workplane(offset=x_wall_out + 0.05)
        .center(Y_C, USBC_SOCK_Z)
        .rect(USBC_SOCK_BEZEL_W, USBC_SOCK_BEZEL_H)
        .extrude(USBC_SOCK_BEZEL_T)
        .edges("|X")
        .fillet(4.8)
    )
    waist = (
        e.box(
            1.25,
            USBC_SOCK_WAIST_W,
            USBC_SOCK_STEM_H,
            x_wall_out - 1.25 / 2,
            Y_C,
            USBC_SOCK_Z - USBC_SOCK_STEM_H / 2,
        )
        .edges("|X")
        .fillet(0.6)
    )
    stem = (
        e.box(
            USBC_SOCK_STEM_L - 1.25,
            USBC_SOCK_STEM_W,
            USBC_SOCK_STEM_H,
            x_wall_out - 1.25 - (USBC_SOCK_STEM_L - 1.25) / 2,
            Y_C,
            USBC_SOCK_Z - USBC_SOCK_STEM_H / 2,
        )
        .edges("|X")
        .fillet(0.6)
    )
    wings = e.box(
        4.25,
        USBC_SOCK_WING_W,
        4.6,
        x_wall_out - 1.25 - 4.25 / 2,
        Y_C,
        USBC_SOCK_Z - 2.3,
    )
    usb_c_socket = bezel.union(waist).union(stem).union(wings)
    usb_c_plug = e.box(14.0, 11.4, 6.0, x_wall_out + USBC_SOCK_BEZEL_T + 7.0, Y_C, USBC_SOCK_Z - 3.0)

    return {
        "board": board,
        "board_parts": board_parts,
        "radar": radar,
        "radar_parts": radar_parts,
        "dupont_5p": dupont_5p,
        "usb_c_socket": usb_c_socket,
        "usb_c_plug": usb_c_plug,
    }


def _export_pod_variant(
    out_dir: Path,
    prefix: str,
    base: cq.Workplane,
    lid: cq.Workplane,
    dummies: dict[str, cq.Workplane],
    base_h: float = e.H,
    stand: cq.Workplane | None = None,
) -> None:
    """Export base/lid STEP & STL plus assembly and fit-check STEP files for a 2-piece pod variant."""
    cq.exporters.export(base, str(out_dir / f"{prefix}_base.step"))
    cq.exporters.export(base, str(out_dir / f"{prefix}_base.stl"), tolerance=0.05, angularTolerance=0.1)
    lid_print = lid.translate((0, 0, -base_h - e.LID_T)).rotate((0, 0, 0), (1, 0, 0), 180)
    cq.exporters.export(lid, str(out_dir / f"{prefix}_lid.step"))
    cq.exporters.export(lid_print, str(out_dir / f"{prefix}_lid.stl"), tolerance=0.05, angularTolerance=0.1)

    asm = cq.Assembly(name=f"{prefix}_sensor_enclosure")
    asm.add(base, name=f"{prefix}_base", color=cq.Color(0.85, 0.85, 0.85))
    asm.add(lid, name=f"{prefix}_lid", color=cq.Color(0.3, 0.5, 0.8, 0.6))
    if stand is not None:
        asm.add(stand, name="v_stand", color=cq.Color(0.45, 0.45, 0.48))
    asm.export(str(out_dir / f"{prefix}_assembly.step"))

    fit = cq.Assembly(name=f"{prefix}_fit_check")
    fit.add(base, name=f"{prefix}_base", color=cq.Color(0.85, 0.85, 0.85))
    fit.add(lid, name=f"{prefix}_lid", color=cq.Color(0.3, 0.5, 0.8, 0.4))
    if stand is not None:
        fit.add(stand, name="v_stand", color=cq.Color(0.45, 0.45, 0.48))
    for k, shp in dummies.items():
        fit.add(shp, name=k, color=cq.Color(0.9, 0.3, 0.2))
    fit.export(str(out_dir / f"{prefix}_fit_check.step"))


def build_variants(out_dir: Path) -> None:
    """Export all STL and STEP artifacts for Models 2-5, the detachable V-stand, and the USB-C fit-test gauge."""
    out_dir.mkdir(parents=True, exist_ok=True)

    # Model 2: 45 deg Corner / Ceiling Snap-Fit Enclosure
    c_base, c_lid, c_br = make_corner_base(), make_corner_lid(), make_corner_bracket()
    c_dm = e.make_dummies()
    cq.exporters.export(c_base, str(out_dir / "corner_base.step"))
    cq.exporters.export(c_base, str(out_dir / "corner_base.stl"), tolerance=0.05, angularTolerance=0.1)
    c_lid_print = c_lid.translate((0, 0, -e.H - e.LID_T)).rotate((0, 0, 0), (1, 0, 0), 180)
    cq.exporters.export(c_lid, str(out_dir / "corner_lid.step"))
    cq.exporters.export(c_lid_print, str(out_dir / "corner_lid.stl"), tolerance=0.05, angularTolerance=0.1)
    # Orient bracket on its flat -X face for support-free printing
    c_br_print = c_br.translate((BRACKET_LEN_X / 2, 0, 0)).rotate((0, 0, 0), (0, 1, 0), -90)
    cq.exporters.export(c_br, str(out_dir / "corner_bracket.step"))
    cq.exporters.export(c_br_print, str(out_dir / "corner_bracket.stl"), tolerance=0.05, angularTolerance=0.1)

    c_asm = cq.Assembly(name="corner_sensor_enclosure")
    c_asm.add(c_base, name="corner_base", color=cq.Color(0.85, 0.85, 0.85))
    c_asm.add(c_lid, name="corner_lid", color=cq.Color(0.3, 0.5, 0.8, 0.6))
    c_asm.add(c_br, name="corner_bracket", color=cq.Color(0.45, 0.45, 0.48))
    c_asm.export(str(out_dir / "corner_assembly.step"))

    c_fit = cq.Assembly(name="corner_fit_check")
    c_fit.add(c_base, name="corner_base", color=cq.Color(0.85, 0.85, 0.85))
    c_fit.add(c_lid, name="corner_lid", color=cq.Color(0.3, 0.5, 0.8, 0.4))
    c_fit.add(c_br, name="corner_bracket", color=cq.Color(0.45, 0.45, 0.48))
    for k, shp in c_dm.items():
        c_fit.add(shp, name=k, color=cq.Color(0.9, 0.3, 0.2))
    c_fit.export(str(out_dir / "corner_fit_check.step"))

    # Model 3: Freestanding Shelf / Vanity Pod with USB-C Pass-Through (HLK-LD2410S)
    _export_pod_variant(out_dir, "vanity", make_vanity_base(), make_vanity_lid(), make_vanity_dummies(), base_h=e.H)

    # Detachable Inverted-V (ʌ) Desktop Stand (slots into the flush -Y mortises of Model 4 & Model 5)
    v_stand_c = make_v_stand(outer_w=OUTER_W_C)
    v_stand_s = make_v_stand(outer_w=OUTER_W_S)
    cq.exporters.export(v_stand_s, str(out_dir / "v_stand.step"))
    cq.exporters.export(v_stand_s, str(out_dir / "v_stand.stl"), tolerance=0.05, angularTolerance=0.1)

    # Model 4: Sleek Desktop Battery-Free HLK-LD2410C (22x16 mm) Enclosure + Detachable V-Stand
    _export_pod_variant(
        out_dir, "ld2410c", make_ld2410c_base(), make_ld2410c_lid(), make_ld2410c_dummies(), base_h=H_C, stand=v_stand_c
    )

    # Model 5: Sleek Desktop Battery-Free HLK-LD2410S (20x20 mm) Enclosure + Detachable V-Stand
    _export_pod_variant(
        out_dir,
        "ld2410s_usb",
        make_ld2410s_usb_base(),
        make_ld2410s_usb_lid(),
        make_ld2410s_usb_dummies(),
        base_h=H_S,
        stand=v_stand_s,
    )

    # Model 6: "Aura-S" (v1) — Award-Edition Horizon Stadium Monolith for 20x20 mm HLK-LD2410S
    aura_s_base, aura_s_lid, aura_s_stand, aura_s_dm = (
        make_aura_s_base(),
        make_aura_s_lid(),
        make_aura_s_stand(),
        make_aura_s_dummies(),
    )
    for stand_prefix in ("aura_v1", "aura_s_v1", "aura_s"):
        cq.exporters.export(aura_s_stand, str(out_dir / f"{stand_prefix}_stand.step"))
        cq.exporters.export(aura_s_stand, str(out_dir / f"{stand_prefix}_stand.stl"), tolerance=0.05, angularTolerance=0.1)
    for pod_prefix in ("aura_v1", "aura_s_v1", "aura_s"):
        _export_pod_variant(
            out_dir,
            pod_prefix,
            aura_s_base,
            aura_s_lid,
            aura_s_dm,
            base_h=H_AURA,
            stand=aura_s_stand,
        )

    # Model 7: "Aura-C" (v1) — Award-Edition Horizon Stadium Monolith for 22x16 mm HLK-LD2410C
    aura_c_base, aura_c_lid, aura_c_stand, aura_c_dm = (
        make_aura_c_base(),
        make_aura_c_lid(),
        make_aura_c_stand(),
        make_aura_c_dummies(),
    )
    for stand_prefix in ("aura_c_v1", "aura_c"):
        cq.exporters.export(aura_c_stand, str(out_dir / f"{stand_prefix}_stand.step"))
        cq.exporters.export(aura_c_stand, str(out_dir / f"{stand_prefix}_stand.stl"), tolerance=0.05, angularTolerance=0.1)
    for pod_prefix in ("aura_c_v1", "aura_c"):
        _export_pod_variant(
            out_dir,
            pod_prefix,
            aura_c_base,
            aura_c_lid,
            aura_c_dm,
            base_h=H_AURA_C,
            stand=aura_c_stand,
        )

    # Model 8: "Aura-S v2" ("aura_v2" / "aura_s_v2") — Compact Stacked Direct-Solder Monolith (20x20 mm HLK-LD2410S)
    as_v2_base, as_v2_lid, as_v2_stand, as_v2_dm = (
        make_aura_s_v2_base(),
        make_aura_s_v2_lid(),
        make_aura_s_v2_stand(),
        make_aura_s_v2_dummies(),
    )
    for stand_prefix in ("aura_v2", "aura_s_v2"):
        cq.exporters.export(as_v2_stand, str(out_dir / f"{stand_prefix}_stand.step"))
        cq.exporters.export(as_v2_stand, str(out_dir / f"{stand_prefix}_stand.stl"), tolerance=0.05, angularTolerance=0.1)
    for pod_prefix in ("aura_v2", "aura_s_v2"):
        _export_pod_variant(
            out_dir,
            pod_prefix,
            as_v2_base,
            as_v2_lid,
            as_v2_dm,
            base_h=H_AURA_V2,
            stand=as_v2_stand,
        )

    # Model 9: "Aura-C v2" ("aura_c_v2") — Compact Stacked Direct-Solder Monolith (22x16 mm HLK-LD2410C)
    ac_v2_base, ac_v2_lid, ac_v2_stand, ac_v2_dm = (
        make_aura_c_v2_base(),
        make_aura_c_v2_lid(),
        make_aura_c_v2_stand(),
        make_aura_c_v2_dummies(),
    )
    cq.exporters.export(ac_v2_stand, str(out_dir / "aura_c_v2_stand.step"))
    cq.exporters.export(ac_v2_stand, str(out_dir / "aura_c_v2_stand.stl"), tolerance=0.05, angularTolerance=0.1)
    _export_pod_variant(
        out_dir,
        "aura_c_v2",
        ac_v2_base,
        ac_v2_lid,
        ac_v2_dm,
        base_h=H_AURA_V2,
        stand=ac_v2_stand,
    )

    # 4-Station USB-C Socket Fit-Test Gauge (+0.5, +1.0, +1.5, +2.0 mm wider)
    usbc_test = make_usbc_socket_fit_test()
    cq.exporters.export(usbc_test, str(out_dir / "usbc_socket_fit_test.step"))
    cq.exporters.export(usbc_test, str(out_dir / "usbc_socket_fit_test.stl"), tolerance=0.05, angularTolerance=0.1)


if __name__ == "__main__":
    build_variants(Path(__file__).parent / "out")
