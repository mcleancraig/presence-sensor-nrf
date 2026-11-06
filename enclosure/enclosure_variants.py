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

  Model 4 (HLK-LD2410C Constant USB-C Power Enclosure — 22x16 mm HLK-LD2410C):
    - ld2410c_base.stl / .step   : Constant USB-C pass-through base for 22x16 mm HLK-LD2410C
                                   (includes flat -Y shelf foot + +/-X wall-mount screw tabs)
    - ld2410c_lid.stl / .step    : Matching snap-fit lid with blind 24x18x1.2 mm RF radome pocket
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
SNAP_X_OFF = 22.0                       # snap catch X positions (+/- 22.0 mm)
SNAP_L = 10.0                           # snap bead length along X
SNAP_BEAD_W = 0.45                      # outward bead protrusion past lip outer face
SNAP_BEAD_H = 0.90                      # vertical height of snap bead
SNAP_Z_BOT = e.H - 1.55                 # snap bead bottom Z (24.85 mm)
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

# AliExpress 2-Pin Panel-Mount USB-C Socket (1005008559159734) at +X wall
USBC_SOCK_Z = 12.5                      # socket center Z (clears +X mounting tab at Z=4.0 and lid at Z=24.4)
USBC_SOCK_BEZEL_W = 16.5                # exterior oval bezel width along Y (mm)
USBC_SOCK_BEZEL_H = 10.4                # exterior oval bezel height along Z (mm)
USBC_SOCK_BEZEL_T = 2.0                 # exterior oval bezel thickness along X (mm)
USBC_SOCK_STEM_L = 14.0                 # insertion stem length behind bezel along X (mm)
USBC_SOCK_STEM_W = 12.0                 # insertion stem width along Y (mm)
USBC_SOCK_STEM_H = 5.35                 # insertion stem height along Z (mm)
USBC_SOCK_WING_W = 15.7                 # uncompressed width across +/-Y snap-fit wings (mm)
USBC_SOCK_CUT_W = 12.4                  # through-wall cutout width along Y (12.0 + 0.4 mm clearance)
USBC_SOCK_CUT_H = 5.8                   # through-wall cutout height along Z (5.35 + 0.45 mm clearance)
USBC_SOCK_PANEL_T = 1.6                 # local +X panel web thickness for snap-wing lock (mm)


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


def _add_snap_receivers(base: cq.Workplane) -> cq.Workplane:
    """Cut 4 internal snap-catch receiver grooves on +/-Y walls and 2 pry slots on +/-X rim."""
    groove_l = SNAP_L + 1.4
    groove_h = SNAP_BEAD_H + 0.50
    groove_z = SNAP_Z_BOT - 0.25
    for sx in (-1, 1):
        for sy in (-1, 1):
            gy = sy * (e.INNER_W / 2 + 0.15)
            base = base.cut(e.box(groove_l, 0.70, groove_h, sx * SNAP_X_OFF, gy, groove_z))
        px = sx * (e.OUTER_L / 2 - 0.6)
        base = base.cut(e.box(1.4, PRY_W, PRY_H + 0.1, px, 0.0, e.H - PRY_H))
    return base


def make_snap_lid(with_vanity_foot: bool = False, board_x: float = e.BOARD_X) -> cq.Workplane:
    """Build compact flangeless snap-fit lid with blind 22x22x1.2 mm RF radome & PCB hold-downs."""
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

    # 4 outward snap beads on the +/-Y lip faces
    for sx in (-1, 1):
        for sy in (-1, 1):
            by = sy * (e.INNER_W / 2 - e.LIP_CLEAR + SNAP_BEAD_W / 2 - 0.05)
            bead = e.box(SNAP_L, SNAP_BEAD_W + 0.10, SNAP_BEAD_H, sx * SNAP_X_OFF, by, SNAP_Z_BOT)
            lid = lid.union(bead)

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
    groove_l = SNAP_L + 1.4
    groove_h = SNAP_BEAD_H + 0.50
    groove_z = (H_C - 1.55) - 0.25
    for sx in (-1, 1):
        for sy in (-1, 1):
            gy = sy * (INNER_W_C / 2 + 0.15)
            base = base.cut(e.box(groove_l, 0.70, groove_h, sx * SNAP_X_OFF, gy, groove_z))
        px = sx * (OUTER_L_C / 2 - 0.6)
        base = base.cut(e.box(1.4, PRY_W, PRY_H + 0.1, px, 0.0, H_C - PRY_H))
    return base


def _add_radar_c_cradle(base: cq.Workplane) -> cq.Workplane:
    """Monolithic wall-joined radar tower for 22.0 x 16.0 mm HLK-LD2410C in compact 24 mm wide cavity."""
    z_top = e.FLOOR + RADAR_C_RAIL_H + RADAR_C_T            # 21.10 mm
    stop_h = RADAR_C_RAIL_H + RADAR_C_T + 1.05              # 19.75 mm (Z_max = 22.15 mm < lid lip 22.40 mm)
    body_h = (H_C - e.LIP_H - 0.4) - e.FLOOR                # 19.60 mm
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
    base = base.union(e.box(neg_x_w, INNER_W_C - 4.4, stop_h, -INNER_L_C / 2 + neg_x_w / 2, Y_C, e.FLOOR))

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


def _add_board_c_cradle(base: cq.Workplane) -> cq.Workplane:
    """Wall-joined SuperMini nRF52840 cradle at BOARD_C_X fused to both -Y and +Y outer walls."""
    z_top = e.FLOOR + e.BOARD_RAIL_H + e.BOARD_T            # 8.10 mm
    stop_h = e.BOARD_RAIL_H + e.BOARD_T + e.STOP_ABOVE      # 7.50 mm (Z_max = 9.90 mm)
    end_pad_l = (e.BOARD_L - e.BOARD_PIN_ROW_L) / 2 - 0.2   # 2.3 mm
    end_pad_w = 3.4
    stop_t = 2.8

    # Central cross-tie stiffening the two inset rails
    base = base.union(e.box(3.2, e.BOARD_W - 2 * e.BOARD_PIN_SPAN_Y - 2.0, e.BOARD_RAIL_H, BOARD_C_X, Y_C, e.FLOOR))

    for sy in (-1, 1):
        inset_y = Y_C + sy * (e.BOARD_W / 2 - e.BOARD_PIN_SPAN_Y - 1.8)
        base = base.union(e.box(e.BOARD_L - 10.0, e.RAIL_W, e.BOARD_RAIL_H, BOARD_C_X, inset_y, e.FLOOR))
        y_in = Y_C + sy * (e.BOARD_W / 2 + e.BOARD_CLEAR)   # +/-9.15 mm
        y_out = sy * (INNER_W_C / 2)                        # +/-12.00 mm (2.85 mm solid wall each side)
        y_w = abs(y_out - y_in)
        for sx in (-1, 1):
            px = BOARD_C_X + sx * (e.BOARD_L / 2 - end_pad_l / 2)
            py = Y_C + sy * (e.BOARD_W / 2 - end_pad_w / 2)
            base = base.union(e.box(end_pad_l, end_pad_w, e.BOARD_RAIL_H, px, py, e.FLOOR))
            sxp_y = BOARD_C_X + sx * (e.BOARD_L / 2 + e.BOARD_CLEAR - e.STOP_W / 2)
            base = base.union(e.box(e.STOP_W, y_w, stop_h, sxp_y, (y_in + y_out) / 2, e.FLOOR))
            base = base.union(e._snap_hook_x(px, end_pad_l, y_in, sy, z_top, e.BOARD_SNAP_OVERHANG))
            # Corner X stops (leave 10.0 mm central channel Y = -5.0..+5.0 mm open for radar & USB-C wires)
            sxp = BOARD_C_X + sx * (e.BOARD_L / 2 + e.BOARD_CLEAR + stop_t / 2)
            syp = Y_C + sy * (e.BOARD_W / 2 + e.BOARD_CLEAR - e.STOP_W / 2)
            base = base.union(e.box(stop_t, e.STOP_W, stop_h, sxp, syp, e.FLOOR))
    return base


def _add_usbc_socket_bay(base: cq.Workplane) -> cq.Workplane:
    """Add internal support cradle, through-wall slot, and snap-wing lock for AliExpress USB-C socket (1005008559159734)."""
    # 1. Two floor-joined under-stem support rails (X = +30.0..+41.0 mm, Y = +/-3.8 mm, Z = FLOOR..9.65 mm)
    stem_bot_z = USBC_SOCK_Z - USBC_SOCK_STEM_H / 2         # 9.825 mm
    rail_h = (stem_bot_z - 0.175) - e.FLOOR                 # 7.25 mm
    rail_len = 11.0
    rail_cx = INNER_L_C / 2 - rail_len / 2                  # +35.50 mm
    for sy in (-1, 1):
        base = base.union(e.box(rail_len, 2.2, rail_h, rail_cx, sy * 3.8, e.FLOOR))
        # Side stiffening cheeks fused to +/-Y outer walls outside the 15.7 mm snap wings (Y = +/-8.15..+/-12.0 mm)
        cheek_w = INNER_W_C / 2 - 8.15                      # 3.85 mm
        cheek_cy = sy * (8.15 + cheek_w / 2)
        base = base.union(e.box(rail_len, cheek_w, USBC_SOCK_Z + 2.2 - e.FLOOR, rail_cx, cheek_cy, e.FLOOR))

    # 2. Through-wall rectangular cutout (12.4 x 5.8 mm) in +X wall for the 12.0 x 5.35 mm stem
    slot_cut = (
        cq.Workplane("YZ")
        .workplane(offset=INNER_L_C / 2 - 1.0)
        .center(Y_C, USBC_SOCK_Z)
        .rect(USBC_SOCK_CUT_W, USBC_SOCK_CUT_H)
        .extrude(e.WALL + 2.0)
        .edges("|X")
        .fillet(0.5)
    )
    # 3. Interior snap-wing locking recess behind the 1.60 mm +X panel web (lets 15.7 mm snap wings lock open)
    recess_x0 = INNER_L_C / 2 - 0.4
    recess_len = (OUTER_L_C / 2 - USBC_SOCK_PANEL_T) - recess_x0
    wing_recess = e.box(
        recess_len,
        USBC_SOCK_WING_W + 0.7,
        USBC_SOCK_CUT_H,
        recess_x0 + recess_len / 2,
        Y_C,
        USBC_SOCK_Z - USBC_SOCK_CUT_H / 2,
    )
    return base.cut(slot_cut).cut(wing_recess)


def make_ld2410c_base() -> cq.Workplane:
    """Compact battery-free HLK-LD2410C base (86.8 x 28.8 x 24.4 mm) with panel-mount USB-C socket bay."""
    base = e.rrect(OUTER_L_C, OUTER_W_C, OUTER_R, 0.0, H_C)
    foot_y = -OUTER_W_C / 2 - VANITY_FOOT_OUT / 2 + 1.0
    foot = e.box(VANITY_FOOT_L, VANITY_FOOT_OUT + 2.0, H_C, 0.0, foot_y, 0.0).edges("|Z").fillet(1.5)
    base = base.union(foot)

    for sx in (-1, 1):
        cx = sx * (OUTER_L_C / 2 + e.TAB_LEN / 2)
        tab = e.box(e.TAB_LEN, e.TAB_W, e.TAB_T, cx, 0.0, 0.0).edges("|Z").fillet(2.0)
        hole = (
            cq.Workplane("XY")
            .center(sx * (OUTER_L_C / 2 + e.TAB_HOLE_FROM_WALL), 0.0)
            .circle(e.TAB_HOLE_D / 2)
            .extrude(e.TAB_T)
        )
        base = base.union(tab).cut(hole)

    base = base.cut(e.rrect(INNER_L_C, INNER_W_C, e.INNER_R, e.FLOOR, DEPTH_C + 1.0))
    base = _add_snap_receivers_c(base)
    base = _add_board_c_cradle(base)
    base = _add_radar_c_cradle(base)
    return _add_usbc_socket_bay(base)


def make_ld2410c_lid() -> cq.Workplane:
    """Compact battery-free snap-fit lid (86.8 x 28.8 mm) for HLK-LD2410C with 24x18x1.2 mm radome & hold-downs."""
    lid = e.rrect(OUTER_L_C, OUTER_W_C, OUTER_R, H_C, e.LID_T)
    foot_y = -OUTER_W_C / 2 - VANITY_FOOT_OUT / 2 + 1.0
    foot = e.box(VANITY_FOOT_L, VANITY_FOOT_OUT + 2.0, e.LID_T, 0.0, foot_y, H_C)
    lid = lid.union(foot.edges("|Z").fillet(1.5))

    lip_l, lip_w = INNER_L_C - 2 * e.LIP_CLEAR, INNER_W_C - 2 * e.LIP_CLEAR
    lip = (
        e.rrect(lip_l, lip_w, max(e.INNER_R - e.LIP_CLEAR, 0.5), H_C - e.LIP_H, e.LIP_H)
        .cut(e.rrect(lip_l - 2 * e.LIP_T, lip_w - 2 * e.LIP_T, 0.5, H_C - e.LIP_H - 1, e.LIP_H + 2))
    )
    lid = lid.union(lip)

    snap_z_bot_c = H_C - 1.55
    for sx in (-1, 1):
        for sy in (-1, 1):
            by = sy * (INNER_W_C / 2 - e.LIP_CLEAR + SNAP_BEAD_W / 2 - 0.05)
            bead = e.box(SNAP_L, SNAP_BEAD_W + 0.10, SNAP_BEAD_H, sx * SNAP_X_OFF, by, snap_z_bot_c)
            lid = lid.union(bead)

    radome_pocket = e.box(RADOME_C_L, RADOME_C_W, e.RADOME_DEPTH + 0.1, RADAR_C_X, Y_C, H_C - 0.1)
    lid = lid.cut(radome_pocket)

    # 1. SuperMini portal-arch hold-downs at BOARD_C_X +/- 15.15 mm
    z_brd_top = e.FLOOR + e.BOARD_RAIL_H + e.BOARD_T
    foot_z0, bridge_z0 = z_brd_top + 0.35, z_brd_top + 3.90
    for sx in (-1, 1):
        arch_x = BOARD_C_X + sx * 15.15
        lid = lid.union(e.box(2.1, 16.1, H_C - bridge_z0 + 0.2, arch_x, Y_C, bridge_z0))
        for sy in (-1, 1):
            lid = lid.union(e.box(2.1, 1.8, bridge_z0 - foot_z0 + 0.2, arch_x, Y_C + sy * 7.15, foot_z0))

    # 2. Four 2.4x2.4 mm corner hold-down bosses over 22x16 mm HLK-LD2410C
    rad_hold_z0 = e.FLOOR + RADAR_C_RAIL_H + RADAR_C_T + 0.30
    rad_hold_h = (H_C + e.RADOME_DEPTH) - rad_hold_z0 + 0.2
    for sx in (-1, 1):
        for sy in (-1, 1):
            lid = lid.union(e.box(2.4, 2.4, rad_hold_h, RADAR_C_X + sx * 9.5, Y_C + sy * 6.6, rad_hold_z0))

    # 3. Top hold-down boss over the 14.0 mm USB-C socket stem (stops 0.325 mm above stem top Z = 15.175 mm)
    sock_hold_z0 = USBC_SOCK_Z + USBC_SOCK_STEM_H / 2 + 0.325
    lid = lid.union(e.box(4.0, 8.0, H_C - sock_hold_z0 + 0.2, +35.0, Y_C, sock_hold_z0))
    return lid


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
    # - 16.5 x 10.4 x 2.0 mm exterior oval bezel flush against +X outer wall (X = +43.4..+45.4 mm)
    # - 12.0 x 5.35 x 14.0 mm insertion stem extending inside cavity to X = +29.4 mm
    # - 15.7 mm snap-fit side wings locked inside the interior recess (X = +32.0..+41.5 mm)
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
    stem = (
        e.box(
            USBC_SOCK_STEM_L,
            USBC_SOCK_STEM_W,
            USBC_SOCK_STEM_H,
            x_wall_out - USBC_SOCK_STEM_L / 2,
            Y_C,
            USBC_SOCK_Z - USBC_SOCK_STEM_H / 2,
        )
        .edges("|X")
        .fillet(0.6)
    )
    wings = e.box(
        9.5,
        USBC_SOCK_WING_W,
        4.6,
        x_wall_out - USBC_SOCK_PANEL_T - 0.3 - 9.5 / 2,
        Y_C,
        USBC_SOCK_Z - 2.3,
    )
    usb_c_socket = bezel.union(stem).union(wings)
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
    asm.export(str(out_dir / f"{prefix}_assembly.step"))

    fit = cq.Assembly(name=f"{prefix}_fit_check")
    fit.add(base, name=f"{prefix}_base", color=cq.Color(0.85, 0.85, 0.85))
    fit.add(lid, name=f"{prefix}_lid", color=cq.Color(0.3, 0.5, 0.8, 0.4))
    for k, shp in dummies.items():
        fit.add(shp, name=k, color=cq.Color(0.9, 0.3, 0.2))
    fit.export(str(out_dir / f"{prefix}_fit_check.step"))


def build_variants(out_dir: Path) -> None:
    """Export all STL and STEP artifacts for Model 2 (Corner), Model 3 (Vanity), and Model 4 (LD2410C)."""
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

    # Model 4: Compact Battery-Free HLK-LD2410C (22x16 mm) Enclosure with Panel-Mount USB-C Socket
    _export_pod_variant(out_dir, "ld2410c", make_ld2410c_base(), make_ld2410c_lid(), make_ld2410c_dummies(), base_h=H_C)


if __name__ == "__main__":
    build_variants(Path(__file__).parent / "out")
