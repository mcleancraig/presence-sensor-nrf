"""
Parametric bathroom/outdoor enclosure for the presence sensor
(SuperMini nRF52840 + Hi-Link HLK-LD2410S 24 GHz mmWave radar + one 18650 cell).

Run:  python enclosure.py            (needs `pip install cadquery`)
Out:  out/base.step, out/lid.step, out/assembly.step, out/fit_check.step, out/*.stl

Coordinates: X along the battery, Y across, Z up. Z = 0 is the underside of the base.
The cavity is centred on the origin in XY. All dimensions are in mm.
"""

from pathlib import Path

import cadquery as cq

# --------------------------------------------------------------------------------------
# Parameters
# --------------------------------------------------------------------------------------

# Shell
WALL = 2.4                  # side wall thickness (6 perimeters at 0.4 mm nozzle)
FLOOR = 2.4                 # base floor thickness
INNER_L = 82.0              # cavity length (X)
INNER_W = 48.0              # cavity width (Y) — fits 18650 lane (-Y) + 20 mm radar lane (+Y)
DEPTH = 24.0                # cavity depth, floor top to base rim
INNER_R = 2.0               # cavity corner radius

# Top flange (carries the gasket groove and the heat inserts, outside the sealed volume)
FLANGE_W = 8.0              # how far the flange sticks out beyond the wall
FLANGE_T = 7.0              # flange thickness (must exceed INSERT_DEPTH)
FLANGE_R = 4.0              # flange outer corner radius (centred on the screw axis)

# Gasket groove in the flange top (2 mm EPDM/silicone cord or printed TPU)
GROOVE_OFFSET = 3.6         # groove centreline distance outside the cavity edge
GROOVE_W = 2.2
GROOVE_D = 1.5
GROOVE_R = 4.0              # centreline corner radius

# M3 heat inserts (base) and clearance holes (lid)
INSERT_D = 4.0              # hole for a standard M3 x 5.7 x 4.6 mm heat-set insert
INSERT_DEPTH = 6.0
SCREW_CLEAR_D = 3.4
SCREW_OFFSET = 6.4          # screw axis distance outside the cavity edge (both X and Y)

# Wall-mount tabs at the X ends, level with the base underside
TAB_W = 12.0
TAB_LEN = 16.0              # beyond the wall; the hole must clear the flange overhang
TAB_T = 4.0
TAB_HOLE_D = 4.5
TAB_HOLE_FROM_WALL = 11.5

# 18650 cell and wall-buttressed 10x10 mm contact plate bulkheads (-Y lane)
CELL_D = 18.4
CELL_LEN = 65.0
CELL_RAISE = 2.0            # gap under the cell, room for wiring/solder tabs
BAY_LEN = 69.0              # between the inner faces of the two plate slots (cell + spring)
LANE_W = CELL_D + 1.0
LANE_MARGIN = 2.0           # battery lane distance from the -Y wall
PLATE_W = 10.0              # user's positive & negative contact plate width (Y)
PLATE_H = 10.0              # user's positive & negative contact plate height (Z)
PLATE_T = 0.5               # contact plate thickness (X)
SLOT_W = 10.5               # 10.0 mm plate + 0.50 mm slip-fit tolerance (0.25 mm per side)
SLOT_T = 0.8                # 0.50 mm plate + 0.30 mm clearance
DIMPLE_H = 1.0              # how far the + plate's dimple stands proud of the plate
CAP_RISE = 0.4              # flat-top cell: + cap height above the end shoulder
# Wall-joined backing behind each contact plate slot extends all the way to the +/-X cavity wall
BLOCK_BACK = INNER_L / 2 - (BAY_LEN / 2 + SLOT_T)   # 5.7 mm solid backing fused to +/-X walls
# The lips in front of the slot lie inside the cell's end-face footprint (plate is narrower than
# the cell), so they must be thinner than dimple + cap or the cell rests on the lips instead of
# the + contact. check() enforces this. Slice with Arachne wall generator on Bambu Lab A1.
BLOCK_LIP = 0.6             # material in front of the slot (retains the plate)
BLOCK_SIDE = 4.55           # thickened +Y cheek beside the 10.5 mm slot (-Y side fuses to -Y wall)
WINDOW_W = 7.6              # central front window; leaves 1.45 mm lips (1.20 mm overlap/side on 10 mm plate)
WIRE_NOTCH_W = 5.0          # 5.0 mm wide rear/bottom/top solder-tab & wire relief channel
WIRE_NOTCH_H = 5.5
SADDLE_X = (-20.0, 20.0)    # saddle rib X positions
SADDLE_T = 4.0              # thickened 4.0 mm cell saddles joined to -Y wall and electronics cradles

# Electronics lane (+Y): SuperMini nRF52840 (+X) and HLK-LD2410S 24 GHz radar (-X)
LANE_GAP = 3.0              # gap between battery lane and electronics lane
BOARD_CLEAR = 0.15          # snug 0.15 mm XY clearance around each PCB inside its cradle
RAIL_W = 1.8                # inset support rail wall thickness
STOP_T = 3.2                # reinforced >=3.2 mm structural stop wall thickness
STOP_W = 4.2                # corner stop arm length
STOP_ABOVE = 1.8            # corner stops + snap hooks rise 1.8 mm above PCB top face
BOARD_SNAP_OVERHANG = 0.65  # positive inward snap-hook catch overhang on all 4 nRF corners

# SuperMini nRF52840 cradle (+X side of +Y lane)
# 24 through-hole GPIO/power pads sit 1.38 mm from the +/-Y edges (0.0..2.2 mm pad span).
# The cradle supports the PCB at its 4 corners (outside the 28 mm pin rows) plus two inset
# longitudinal rails inside the pin rows, with wall-joined +Y buttresses and 4 snap-in catches.
BOARD_L = 33.0              # nominal SuperMini PCB length (X)
BOARD_W = 18.0              # nominal SuperMini PCB width (Y)
BOARD_T = 1.2               # SuperMini PCB thickness
BOARD_X = 20.5              # SuperMini centre X
BOARD_RAIL_H = 4.5          # 4.5 mm under-board clearance for through-hole solder joints + wiring
RAIL_H = BOARD_RAIL_H       # alias preserved for section/verification scripts
BOARD_PIN_ROW_L = 28.0      # length of the 12-pin 2.54 mm rows along +/-Y edges
BOARD_PIN_SPAN_Y = 2.2      # inward width of through-hole pads/solder fillets from +/-Y edges
BOARD_PIN_DEPTH = 2.5       # downward (-Z) protrusion of soldered wire tails below SuperMini

# Hi-Link HLK-LD2410S 24 GHz mmWave radar monolithic wall-joined tower (-X side of +Y lane)
# Per Hi-Link HLK-LD2410S User Manual V1.2 Sec. 7 Fig. 7-1: strictly 20.00 x 20.00 x 1.20 mm
# square PCB with R = 2.00 mm rounded corners and an asymmetric 5-pin 2.54 mm J2 header
# (Pin 5 OT2 = 1.62 mm from +Y edge .. Pin 1 3V3 = 11.78 mm from +Y edge) oriented on the +X
# edge facing the SuperMini, connected via a 1x5 female DuPont housing (13.8 x 3.2 x 16.5 mm).
RADAR_L = 20.0              # HLK-LD2410S PCB length (X)
RADAR_W = 20.0              # HLK-LD2410S PCB width (Y)
RADAR_T = 1.2               # HLK-LD2410S PCB thickness (1.20 mm +/- 10%)
RADAR_CORNER_R = 2.0        # R = 2.00 mm rounded corners on all 4 corners
RADAR_X = -19.5             # radar centre X
RADAR_RAIL_H = 19.5         # 19.5 mm under-radar (-Z) clearance for 5-pin female DuPont + wire loop
RADAR_LEDGE = 0.8           # inward +/-Y support ledge width (clears -Z crystal at 1.0 mm)
RADAR_RECESS_POS_X = 3.5    # ledge pullback from +X edge (clears 5-pin female DuPont connector)
RADAR_RECESS_NEG_X = 2.5    # ledge pullback from -X edge (clears -Z YXC 3225 crystal & J1 SWD)
RADAR_PARTS_H = 1.8         # max +Z protrusion (J2 top-side solder tails = 1.8 mm, ICL1112 = 1.0 mm)
DUPONT_5P_W = 13.8          # 5-pin (1x5) female DuPont connector width along Y (12.7 mm + clip/margin)
DUPONT_5P_T = 3.2           # 5-pin female DuPont connector thickness along X (2.54 mm + latch wall)
DUPONT_5P_H = 16.5          # 14.0 mm female DuPont housing + 2.5 mm wire bend below radar (-Z)
RADAR_J2_BELOW_H = DUPONT_5P_H
RADAR_SNAP_OVERHANG = 0.45  # inward snap-lip catch overhang on +/-Y radar cradle walls

# Steam-proof lid with embossed rim mating into base debossed groove, blind 1.2 mm RF radome & hold-downs
LID_T = 3.0
RIM_CLEAR = 0.20            # radial slip-fit clearance per side inside base debossed groove (2.20 -> 1.80 mm)
RIM_Z_CLEAR = 0.25          # vertical bottom clearance inside 1.50 mm deep base groove (1.25 mm tongue height)
RIM_W = GROOVE_W - 2 * RIM_CLEAR
RIM_H = GROOVE_D - RIM_Z_CLEAR
LIP_CLEAR = 0.15            # tight 0.15 mm/side perimeter registration for snap-fit lids
LIP_T = 1.6
LIP_H = 2.6                 # 2.6 mm deep perimeter lip for secure snap-fit retention
RADOME_L = 22.0             # blind interior pocket length over 20x20 mm HLK-LD2410S
RADOME_W = 22.0             # blind interior pocket width
RADOME_T = 1.2              # solid top wall thickness (<0.2 dB loss at 24 GHz, lambda ~ 12.5 mm)
RADOME_DEPTH = LID_T - RADOME_T

# --------------------------------------------------------------------------------------
# Derived values
# --------------------------------------------------------------------------------------

H = FLOOR + DEPTH                           # base height (26.4 mm)
OUTER_L = INNER_L + 2 * WALL
OUTER_W = INNER_W + 2 * WALL
FL_L = OUTER_L + 2 * FLANGE_W               # flange / lid outline
FL_W = OUTER_W + 2 * FLANGE_W

Y_BAT = -INNER_W / 2 + LANE_MARGIN + LANE_W / 2
Y_ELEC = Y_BAT + LANE_W / 2 + LANE_GAP + RADAR_W / 2
Y_BRD = Y_ELEC
Y_RADAR = Y_ELEC
AXIS_Z = FLOOR + CELL_RAISE + CELL_D / 2    # cell axis height (13.60 mm absolute)
SLOT_X = BAY_LEN / 2 + SLOT_T / 2           # slot centre line (+/- 34.90 mm)
Z_SLOT_BOT = AXIS_Z - PLATE_H / 2 - 0.15    # solid bottom stop ledge inside slot (8.45 mm)
BLOCK_TOP = AXIS_Z + PLATE_H / 2 + 0.35     # 10.50 mm tall capture pocket top (18.95 mm)
SCREW_PTS = [(sx * (INNER_L / 2 + SCREW_OFFSET), sy * (INNER_W / 2 + SCREW_OFFSET))
             for sx in (-1, 1) for sy in (-1, 1)]


def rrect(length: float, width: float, radius: float, z0: float, height: float) -> cq.Workplane:
    """Rounded-rectangle prism centred on the Z axis."""
    return (cq.Workplane("XY").workplane(offset=z0)
            .rect(length, width).extrude(height)
            .edges("|Z").fillet(radius))


def box(x: float, y: float, z: float, cx: float, cy: float, z0: float) -> cq.Workplane:
    """Axis-aligned box with the given centre in XY and bottom at z0."""
    return cq.Workplane("XY").box(x, y, z, centered=(True, True, False)).translate((cx, cy, z0))


def _snap_hook_x(
    cx: float, length_x: float, y_wall: float, sy: int, z_pcb_top: float, overhang: float
) -> cq.Workplane:
    """Cantilevered snap-hook along X with a flat bottom catch ledge and 45 deg top entry bevel."""
    z0 = z_pcb_top + 0.15
    z2 = z_pcb_top + max(overhang + 0.55, 1.05)
    z1 = z2 - overhang
    y_root = y_wall + sy * 0.60
    y_tip = y_wall - sy * overhang
    pts = [(y_root, z0), (y_tip, z0), (y_tip, z1), (y_root, z2)]
    return cq.Workplane("YZ").workplane(offset=cx - length_x / 2).polyline(pts).close().extrude(length_x)


def _add_board_cradle(
    base: cq.Workplane, board_x: float = BOARD_X, open_pos_x: bool = False
) -> cq.Workplane:
    """Wall-joined SuperMini nRF52840 cradle with >=3.2 mm buttresses and 4 corner 45-deg snap-hooks."""
    z_top = FLOOR + BOARD_RAIL_H + BOARD_T
    stop_h = BOARD_RAIL_H + BOARD_T + STOP_ABOVE
    end_pad_l = (BOARD_L - BOARD_PIN_ROW_L) / 2 - 0.2     # 2.3 mm at -X/+X ends outside 28 mm pin rows
    end_pad_w = 3.4
    # Central cross-tie stiffening the two inset rails
    base = base.union(box(3.2, BOARD_W - 2 * BOARD_PIN_SPAN_Y - 2.0, BOARD_RAIL_H, board_x, Y_BRD, FLOOR))
    # Structural bridge tying the -Y nRF cradle directly into the +X 18650 saddle (X = +20.0 mm)
    bridge_y0 = Y_BAT + LANE_W / 2
    bridge_y1 = Y_BRD - BOARD_W / 2 - BOARD_CLEAR
    base = base.union(
        box(SADDLE_T, bridge_y1 - bridge_y0, stop_h, SADDLE_X[1], (bridge_y0 + bridge_y1) / 2, FLOOR)
    )
    for sy in (-1, 1):
        inset_y = Y_BRD + sy * (BOARD_W / 2 - BOARD_PIN_SPAN_Y - 1.8)
        base = base.union(box(BOARD_L - 10.0, RAIL_W, BOARD_RAIL_H, board_x, inset_y, FLOOR))
        for sx in (-1, 1):
            px = board_x + sx * (BOARD_L / 2 - end_pad_l / 2)
            py = Y_BRD + sy * (BOARD_W / 2 - end_pad_w / 2)
            base = base.union(box(end_pad_l, end_pad_w, BOARD_RAIL_H, px, py, FLOOR))
            # Y-side retainer: +Y fuses to +Y outer wall (4.45 mm); -Y fuses to battery bay buttress (3.85 mm)
            y_in = Y_BRD + sy * (BOARD_W / 2 + BOARD_CLEAR)
            y_out = INNER_W / 2 if sy == 1 else bridge_y0
            y_w = abs(y_out - y_in)
            sxp_y = board_x + sx * (BOARD_L / 2 + BOARD_CLEAR - STOP_W / 2)
            base = base.union(box(STOP_W, y_w, stop_h, sxp_y, (y_in + y_out) / 2, FLOOR))
            # Positive corner snap-hook with 0.65 mm overhang and 45 deg top entry bevel
            base = base.union(_snap_hook_x(px, end_pad_l, y_in, sy, z_top, BOARD_SNAP_OVERHANG))
            if not (open_pos_x and sx == 1):
                sxp = board_x + sx * (BOARD_L / 2 + BOARD_CLEAR + STOP_T / 2)
                syp = Y_BRD + sy * (BOARD_W / 2 + BOARD_CLEAR - STOP_W / 2)
                base = base.union(box(STOP_T, STOP_W, stop_h, sxp, syp, FLOOR))
    return base


def _add_radar_cradle(base: cq.Workplane) -> cq.Workplane:
    """Monolithic wall-joined U-box radar tower (zero thin free-standing uprights) for 20x20 mm LD2410S."""
    z_top = FLOOR + RADAR_RAIL_H + RADAR_T
    stop_h = RADAR_RAIL_H + RADAR_T + 1.05               # Z = 24.15 mm (clears lid lip at Z = 24.40 mm)
    body_h = (H - LIP_H - 0.4) - FLOOR                   # Z = 24.00 mm where joined to +Y wall under lip
    rail_l = RADAR_L - RADAR_RECESS_NEG_X - RADAR_RECESS_POS_X
    rail_cx = RADAR_X + (RADAR_RECESS_NEG_X - RADAR_RECESS_POS_X) / 2
    y_bot_in = Y_RADAR - RADAR_W / 2 - BOARD_CLEAR       # +0.25 mm
    y_top_in = Y_RADAR + RADAR_W / 2 + BOARD_CLEAR       # +20.55 mm
    y_saddle = Y_BAT + LANE_W / 2                        # -2.60 mm (fuses into -X 18650 saddle)

    # 1. +Y North Wall: 4.4 mm thick solid block fused directly to +Y outer enclosure wall (Y=+24.0 mm)
    base = base.union(box(rail_l, INNER_W / 2 - (y_top_in - RADAR_LEDGE), RADAR_RAIL_H,
                          rail_cx, (INNER_W / 2 + y_top_in - RADAR_LEDGE) / 2, FLOOR))
    base = base.union(box(rail_l, INNER_W / 2 - y_top_in, body_h, rail_cx, (INNER_W / 2 + y_top_in) / 2, FLOOR))
    base = base.union(box(rail_l, 1.35, stop_h, rail_cx, y_top_in + 0.675, FLOOR))

    # 2. -Y South Wall: 3.65 mm thick solid wall fused directly into the -X 18650 cell saddle
    base = base.union(box(rail_l, (y_bot_in + RADAR_LEDGE) - y_saddle, RADAR_RAIL_H,
                          rail_cx, (y_bot_in + RADAR_LEDGE + y_saddle) / 2, FLOOR))
    base = base.union(box(rail_l, y_bot_in - y_saddle, stop_h, rail_cx, (y_bot_in + y_saddle) / 2, FLOOR))

    # 3. Snap-in retaining lips (0.45 mm inward overhang + 45 deg top entry ramp) along middle of +/-Y walls
    for sy, y_wall in ((-1, y_bot_in), (1, y_top_in)):
        base = base.union(_snap_hook_x(rail_cx, 9.0, y_wall, sy, z_top, RADAR_SNAP_OVERHANG))

    # 4. -X Continuous 3.8 mm Cross-Wall joining -Y wall, +Y wall, +Y shell wall & -X battery block
    neg_x_in = RADAR_X - RADAR_L / 2 - BOARD_CLEAR       # -29.65 mm
    neg_x_w = 3.8
    base = base.union(box(neg_x_w, INNER_W / 2 - y_saddle, body_h,
                          neg_x_in - neg_x_w / 2, (INNER_W / 2 + y_saddle) / 2, FLOOR))
    base = base.union(box(neg_x_w, 21.8 - y_saddle, stop_h,
                          neg_x_in - neg_x_w / 2, (21.8 + y_saddle) / 2, FLOOR))

    # 5. (+X, -Y) Monolithic Corner L-Buttress (3.5 x 7.95 mm, fused to -Y wall; leaves 18.65 mm wide
    #    unobstructed +X exit channel Y = +5.35..+24.0 mm for 5-pin female DuPont housing at Y = +6.8..+20.6 mm)
    pos_x_in = RADAR_X + RADAR_L / 2 + BOARD_CLEAR       # -9.35 mm
    pos_y_max = +5.35                                    # 1.45 mm clear of DuPont housing at Y = +6.80 mm
    base = base.union(box(RADAR_RECESS_POS_X + BOARD_CLEAR, pos_y_max - y_saddle, RADAR_RAIL_H,
                          pos_x_in - (RADAR_RECESS_POS_X + BOARD_CLEAR) / 2, (pos_y_max + y_saddle) / 2, FLOOR))
    base = base.union(box(RADAR_RECESS_POS_X + BOARD_CLEAR, y_bot_in - y_saddle, stop_h,
                          pos_x_in - (RADAR_RECESS_POS_X + BOARD_CLEAR) / 2, (y_bot_in + y_saddle) / 2, FLOOR))
    base = base.union(box(3.5, pos_y_max - y_saddle, stop_h, pos_x_in + 1.75, (pos_y_max + y_saddle) / 2, FLOOR))
    return base


def _add_battery_bay(base: cq.Workplane) -> cq.Workplane:
    """Add wall-joined 18650 end bulkheads (10x10 mm plate pockets centered on AXIS_Z), ribs, and saddles."""
    block_len = BLOCK_LIP + SLOT_T + BLOCK_BACK          # 7.1 mm total X thickness (fused to +/-X walls)
    y_min = -INNER_W / 2                                 # -24.0 mm (fused to -Y outer wall)
    y_max = Y_BAT + SLOT_W / 2 + BLOCK_SIDE              # -2.5 mm
    block_w = y_max - y_min                              # 21.5 mm total Y width
    block_cy = (y_min + y_max) / 2
    slot_h = BLOCK_TOP - Z_SLOT_BOT + 1.0
    for sx in (-1, 1):
        inner_face = sx * BAY_LEN / 2
        bx = inner_face + sx * (block_len / 2 - BLOCK_LIP)
        block = box(block_len, block_w, BLOCK_TOP - FLOOR, bx, block_cy, FLOOR)
        # 10.50 x 10.50 mm contact plate pocket starting at Z_SLOT_BOT (solid stop ledge at FLOOR+6.05 mm)
        slot = box(SLOT_T, SLOT_W, slot_h, sx * SLOT_X, Y_BAT, Z_SLOT_BOT)
        # 45 deg top entry funnel chamfer on the slot (Z = BLOCK_TOP - 0.50 .. BLOCK_TOP + 0.05)
        funnel = (
            cq.Workplane("XY")
            .workplane(offset=BLOCK_TOP - 0.50)
            .center(sx * SLOT_X, Y_BAT)
            .rect(SLOT_T, SLOT_W)
            .workplane(offset=0.55)
            .rect(SLOT_T + 0.60, SLOT_W + 1.10)
            .loft()
        )
        window = box(BLOCK_LIP + 0.2, WINDOW_W, slot_h, inner_face - sx * (BLOCK_LIP / 2), Y_BAT, Z_SLOT_BOT)
        # 5.0 mm wide bottom solder-tab drop-through & +Y wire exit channel below Z_SLOT_BOT
        # (keeps the full 5.70 mm back wall 100% solid behind the 10x10 mm plate at Z_SLOT_BOT..BLOCK_TOP)
        chimney = box(SLOT_T + 2.2, WIRE_NOTCH_W, Z_SLOT_BOT - FLOOR + 0.2,
                      sx * (SLOT_X + 0.9), Y_BAT, FLOOR)
        notch = box(SLOT_T + 2.4, y_max - Y_BAT + 1.0, WIRE_NOTCH_H,
                    sx * (SLOT_X + 1.0), (Y_BAT + y_max) / 2, FLOOR)
        base = base.union(block.cut(slot).cut(funnel).cut(window).cut(chimney).cut(notch))

    cradle = (cq.Workplane("YZ").workplane(offset=-OUTER_L).center(Y_BAT, AXIS_Z)
              .circle(CELL_D / 2 + 0.2).extrude(2 * OUTER_L))
    # Longitudinal buttress ribs tying the inner faces of both end bulkheads into the 4.0 mm saddles
    rib_span_x = BAY_LEN - 2 * BLOCK_LIP
    buttress_neg_y = box(rib_span_x, 4.2, AXIS_Z - FLOOR - 1.0, 0.0, y_min + 2.1, FLOOR).cut(cradle)
    buttress_pos_y = box(rib_span_x, BLOCK_SIDE, AXIS_Z - FLOOR - 1.0, 0.0, y_max - BLOCK_SIDE / 2, FLOOR).cut(cradle)
    base = base.union(buttress_neg_y).union(buttress_pos_y)
    for sx_pos in SADDLE_X:
        rib = box(SADDLE_T, block_w, AXIS_Z - FLOOR, sx_pos, block_cy, FLOOR)
        base = base.union(rib.cut(cradle))
    return base


def _add_lid_holddowns(lid: cq.Workplane, board_x: float = BOARD_X) -> cq.Workplane:
    """Add lid underside corner bosses over HLK-LD2410S corners (no SuperMini arches so wiring is unobstructed)."""
    del board_x
    z_rad_top = FLOOR + RADAR_RAIL_H + RADAR_T
    # Three 2.4x2.4 mm corner hold-down bosses over HLK-LD2410S (-X,-Y), (-X,+Y), and (+X,-Y) corners
    # (stops 0.30 mm above radar PCB top face at Z = 23.40 mm; leaves 14.8 mm clear antenna span & J2)
    rad_hold_z0 = z_rad_top + 0.30                       # Z = 23.40 mm
    rad_hold_h = (H + RADOME_DEPTH) - rad_hold_z0 + 0.2
    for cx, cy in [(-28.1, +1.80), (-28.1, +19.00), (-10.9, +1.80)]:
        lid = lid.union(box(2.4, 2.4, rad_hold_h, cx, cy, rad_hold_z0))
    return lid


def check() -> None:
    """Fail early on parameter combinations that cannot be printed or assembled."""
    assert RADAR_L == 20.0 and RADAR_W == 20.0, "HLK-LD2410S is strictly 20.0 x 20.0 mm"
    assert PLATE_W == 10.0 and PLATE_H == 10.0, "user battery contact plates are strictly 10.0 x 10.0 mm"
    assert abs(SLOT_W - (PLATE_W + 0.5)) < 1e-6, "10 mm plate slot requires 10.50 mm slip-fit width"
    assert Z_SLOT_BOT > FLOOR + 5.0, "10x10 mm plate slot must have solid bottom stop ledge centered on AXIS_Z"
    assert Y_BAT - LANE_W / 2 >= -INNER_W / 2, "battery lane does not fit in the cavity width"
    assert Y_RADAR + RADAR_W / 2 + BOARD_CLEAR <= INNER_W / 2 - 2.0, "radar does not fit in cavity width"
    assert Y_BRD + BOARD_W / 2 + BOARD_CLEAR <= INNER_W / 2 - 2.0, "SuperMini does not fit in cavity width"
    assert (RADAR_X + RADAR_L / 2 + BOARD_CLEAR + 3.5) < (
        BOARD_X - BOARD_L / 2 - BOARD_CLEAR - STOP_T
    ), "radar cradle and SuperMini cradle overlap along X"
    assert BLOCK_BACK >= 4.5, "battery terminal backing must be >= 4.5 mm and joined to +/-X wall"
    assert STOP_T >= 3.0 and SADDLE_T >= 3.5, "structural stops and saddles must be >= 3.0 mm thick"
    assert BLOCK_TOP < H - LIP_H - 0.5, "battery blocks hit the lid lip"
    # + contact: plate pushed back in its slot, dimple must reach past the lip face with margin
    reach = DIMPLE_H + CAP_RISE - (SLOT_T - PLATE_T) - BLOCK_LIP
    assert reach >= 0.3, f"+ contact only reaches {reach:.2f} mm past the lips (cell would rest on them)"
    assert (PLATE_W - WINDOW_W) / 2 >= 1.0, "lips overlap the 10 mm plate edges too little to retain it"
    assert FLANGE_T > INSERT_DEPTH + 0.8, "flange too thin for the heat inserts"
    assert abs(SCREW_OFFSET - (WALL + FLANGE_W - FLANGE_R)) < 1e-6, "flange corner not centred on screw"
    assert FLANGE_R - INSERT_D / 2 >= 1.5, "insert wall to the flange edge too thin"
    arc_c = GROOVE_OFFSET - GROOVE_R
    gap = 2 ** 0.5 * (SCREW_OFFSET - arc_c) - GROOVE_R - GROOVE_W / 2 - INSERT_D / 2
    assert gap >= 1.0, f"gasket groove only {gap:.2f} mm from an insert hole"
    assert 0.3 <= GROOVE_W - RIM_W <= 0.6, "lid embossed rim must have 0.15..0.30 mm clearance/side in base groove"
    assert 0.15 <= GROOVE_D - RIM_H <= 0.5, "lid embossed rim must not bottom out in base debossed groove"
    assert 0.8 <= RADOME_T <= 1.6, f"radome thickness {RADOME_T:.2f} mm outside 0.8..1.6 mm range"
    assert RADOME_L >= RADAR_L and RADOME_W >= RADAR_W, "radome pocket smaller than radar PCB"
    assert abs(RADAR_X) + RADOME_L / 2 < INNER_L / 2 - LIP_CLEAR - LIP_T, "radome pocket hits lid lip (X)"
    assert abs(Y_RADAR) + RADOME_W / 2 < INNER_W / 2 - LIP_CLEAR - LIP_T, "radome pocket hits lid lip (Y)"
    assert FLOOR + RADAR_RAIL_H + RADAR_T + RADAR_PARTS_H < H - 1.0, "radar +Z solder tails hit lid"
    assert RADAR_RAIL_H >= DUPONT_5P_H + 2.5, "insufficient -Z clearance under radar for 5-pin female DuPont"
    assert BOARD_RAIL_H >= BOARD_PIN_DEPTH + 1.5, "insufficient -Z clearance under SuperMini pins"


# --------------------------------------------------------------------------------------
# Base
# --------------------------------------------------------------------------------------

def make_base() -> cq.Workplane:
    chamfer_z = H - FLANGE_T - FLANGE_W     # 45 degree supportless chamfer under the flange

    shell = rrect(OUTER_L, OUTER_W, INNER_R + WALL, 0, H)
    flange = rrect(FL_L, FL_W, FLANGE_R, H - FLANGE_T, FLANGE_T)
    support = (cq.Workplane("XY").workplane(offset=chamfer_z)
               .rect(OUTER_L, OUTER_W).workplane(offset=FLANGE_W).rect(FL_L, FL_W).loft())
    base = shell.union(flange).union(support)

    # Wall-mount tabs
    for sx in (-1, 1):
        cx = sx * (OUTER_L / 2 + TAB_LEN / 2)
        tab = box(TAB_LEN, TAB_W, TAB_T, cx, 0, 0).edges("|Z").fillet(2.0)
        hole = (cq.Workplane("XY").center(sx * (OUTER_L / 2 + TAB_HOLE_FROM_WALL), 0)
                .circle(TAB_HOLE_D / 2).extrude(TAB_T))
        base = base.union(tab).cut(hole)

    # Cavity
    base = base.cut(rrect(INNER_L, INNER_W, INNER_R, FLOOR, DEPTH + 1))

    # Gasket groove
    g_out = rrect(INNER_L + 2 * (GROOVE_OFFSET + GROOVE_W / 2),
                  INNER_W + 2 * (GROOVE_OFFSET + GROOVE_W / 2),
                  GROOVE_R + GROOVE_W / 2, H - GROOVE_D, GROOVE_D + 1)
    g_in = rrect(INNER_L + 2 * (GROOVE_OFFSET - GROOVE_W / 2),
                 INNER_W + 2 * (GROOVE_OFFSET - GROOVE_W / 2),
                 GROOVE_R - GROOVE_W / 2, H - GROOVE_D - 1, GROOVE_D + 3)
    base = base.cut(g_out.cut(g_in))

    # Heat insert holes (blind, in the flange outside the gasket loop)
    for x, y in SCREW_PTS:
        base = base.cut(cq.Workplane("XY").workplane(offset=H - INSERT_DEPTH)
                        .center(x, y).circle(INSERT_D / 2).extrude(INSERT_DEPTH + 1))

    # 18650 battery bay (-Y lane, wall-joined bulkheads)
    base = _add_battery_bay(base)

    # SuperMini nRF52840 cradle (+X side of +Y lane, wall-joined + snap-hooks)
    base = _add_board_cradle(base)

    # HLK-LD2410S 24 GHz radar cradle (-X side of +Y lane, monolithic wall-joined tower)
    base = _add_radar_cradle(base)

    return base


# --------------------------------------------------------------------------------------
# Lid (modelled in place: underside at Z = H, solid outer top with blind 1.2 mm radome)
# --------------------------------------------------------------------------------------

def make_lid() -> cq.Workplane:
    lid = rrect(FL_L, FL_W, FLANGE_R, H, LID_T)
    rim_out = rrect(INNER_L + 2 * (GROOVE_OFFSET + RIM_W / 2),
                    INNER_W + 2 * (GROOVE_OFFSET + RIM_W / 2),
                    GROOVE_R + RIM_W / 2, H - RIM_H, RIM_H)
    rim_in = rrect(INNER_L + 2 * (GROOVE_OFFSET - RIM_W / 2),
                   INNER_W + 2 * (GROOVE_OFFSET - RIM_W / 2),
                   GROOVE_R - RIM_W / 2, H - RIM_H - 1, RIM_H + 2)
    lid = lid.union(rim_out.cut(rim_in))
    for x, y in SCREW_PTS:
        lid = lid.cut(cq.Workplane("XY").workplane(offset=H - 1).center(x, y)
                      .circle(SCREW_CLEAR_D / 2).extrude(LID_T + 2))
    # Blind interior pocket above HLK-LD2410S antenna array leaving uniform RADOME_T = 1.2 mm top wall
    radome_pocket = box(RADOME_L, RADOME_W, RADOME_DEPTH + 0.1, RADAR_X, Y_RADAR, H - 0.1)
    lid = lid.cut(radome_pocket)
    return _add_lid_holddowns(lid, board_x=BOARD_X)


# --------------------------------------------------------------------------------------
# Dummy parts for the fit check (not printed)
# --------------------------------------------------------------------------------------

def make_dummies(board_x: float = BOARD_X) -> dict[str, cq.Workplane]:
    cell = (cq.Workplane("YZ").workplane(offset=-CELL_LEN / 2).center(Y_BAT, AXIS_Z)
            .circle(CELL_D / 2).extrude(CELL_LEN))
    back = SLOT_X + (SLOT_T - PLATE_T) / 2  # 10x10 mm plates pushed against the back of the slot
    plates = [box(PLATE_T, PLATE_W, PLATE_H, sx * back, Y_BAT, AXIS_Z - PLATE_H / 2) for sx in (-1, 1)]

    # SuperMini nRF52840 PCB + top-side components/USB-C + bottom-side through-hole solder joints
    z_brd_bot = FLOOR + BOARD_RAIL_H
    z_brd_top = z_brd_bot + BOARD_T
    board = box(BOARD_L, BOARD_W, BOARD_T, board_x, Y_BRD, z_brd_bot)
    board_parts = box(22.0, 12.0, 3.0, board_x - 1.0, Y_BRD, z_brd_top).union(
        box(7.5, 9.2, 3.2, board_x + BOARD_L / 2 - 3.75, Y_BRD, z_brd_top)
    )
    for sy in (-1, 1):
        pin_row_y = Y_BRD + sy * (BOARD_W / 2 - BOARD_PIN_SPAN_Y / 2)
        board_parts = board_parts.union(
            box(BOARD_PIN_ROW_L, BOARD_PIN_SPAN_Y, BOARD_PIN_DEPTH, board_x, pin_row_y, z_brd_bot - BOARD_PIN_DEPTH)
        )
    board_parts = board_parts.union(
        box(2.2, 6.0, BOARD_PIN_DEPTH, board_x - BOARD_L / 2 + 1.5, Y_BRD, z_brd_bot - BOARD_PIN_DEPTH)
    )

    # HLK-LD2410S 20.0 x 20.0 x 1.2 mm PCB + ICL1112/MCU/crystal + 5-pin (1x5) female DuPont housing
    z_rad_bot = FLOOR + RADAR_RAIL_H
    z_rad_top = z_rad_bot + RADAR_T
    radar = rrect(RADAR_L, RADAR_W, RADAR_CORNER_R, z_rad_bot, RADAR_T).translate((RADAR_X, Y_RADAR, 0))
    x_rad_left, x_rad_right = RADAR_X - RADAR_L / 2, RADAR_X + RADAR_L / 2
    y_rad_bot, y_rad_top = Y_RADAR - RADAR_W / 2, Y_RADAR + RADAR_W / 2
    j2_cy = y_rad_top - (0.35 + 13.05) / 2
    radar_parts = (
        box(10.0, 10.0, 1.0, RADAR_X, Y_RADAR, z_rad_top)
        .union(box(2.2, 12.7, RADAR_PARTS_H, x_rad_right - 1.47, j2_cy, z_rad_top))
        .union(box(8.0, 8.0, 1.0, RADAR_X, Y_RADAR, z_rad_bot - 1.0))
        .union(box(3.5, 3.2, 1.2, x_rad_left + 2.75, y_rad_bot + 2.60, z_rad_bot - 1.2))
    )
    dupont_5p = box(
        DUPONT_5P_T, DUPONT_5P_W, DUPONT_5P_H, x_rad_right - 1.47, j2_cy, z_rad_bot - DUPONT_5P_H
    ).union(box(3.5, 12.7, 5.5, x_rad_right + 1.5, j2_cy, z_rad_bot - DUPONT_5P_H))
    return {
        "cell": cell, "plate_neg": plates[0], "plate_pos": plates[1], "board": board,
        "board_parts": board_parts, "radar": radar, "radar_parts": radar_parts, "dupont_5p": dupont_5p,
    }


def build(out_dir: Path) -> tuple[cq.Workplane, cq.Workplane, dict[str, cq.Workplane]]:
    check()
    out_dir.mkdir(parents=True, exist_ok=True)
    base, lid, dummies = make_base(), make_lid(), make_dummies()

    cq.exporters.export(base, str(out_dir / "base.step"))
    cq.exporters.export(base, str(out_dir / "base.stl"), tolerance=0.05, angularTolerance=0.1)
    # Lid for printing: flipped so its flat solid outer top lies directly on the print bed
    lid_print = lid.translate((0, 0, -H - LID_T)).rotate((0, 0, 0), (1, 0, 0), 180)
    cq.exporters.export(lid, str(out_dir / "lid.step"))
    cq.exporters.export(lid_print, str(out_dir / "lid.stl"), tolerance=0.05, angularTolerance=0.1)

    asm = cq.Assembly(name="presence_sensor_enclosure")
    asm.add(base, name="base", color=cq.Color(0.85, 0.85, 0.85))
    asm.add(lid, name="lid", color=cq.Color(0.3, 0.5, 0.8, 0.6))
    asm.export(str(out_dir / "assembly.step"))

    fit = cq.Assembly(name="fit_check")
    fit.add(base, name="base", color=cq.Color(0.85, 0.85, 0.85))
    fit.add(lid, name="lid", color=cq.Color(0.3, 0.5, 0.8, 0.4))
    for name, shape in dummies.items():
        fit.add(shape, name=name, color=cq.Color(0.9, 0.3, 0.2))
    fit.export(str(out_dir / "fit_check.step"))
    cq.exporters.export(fit.toCompound(), str(out_dir / "fit_check.stl"), tolerance=0.05, angularTolerance=0.1)
    return base, lid, dummies


if __name__ == "__main__":
    build(Path(__file__).parent / "out")
