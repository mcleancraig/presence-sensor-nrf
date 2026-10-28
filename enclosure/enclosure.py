"""
Parametric bathroom/outdoor enclosure for the presence sensor
(SuperMini nRF52840 + Hi-Link HLK-LD2410S 24 GHz mmWave radar + one 18650 cell).

Run:  python enclosure.py            (needs `pip install cadquery`)
Out:  out/base.step, out/lid.step, out/assembly.step, out/fit_check.step, out/*.stl

Coordinates: X along the battery, Y across, Z up. Z = 0 is the underside of the base.
The cavity is centred on the origin in XY. All dimensions are in mm.
"""

from dataclasses import dataclass
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

# 18650 cell and contact plates (-Y lane)
CELL_D = 18.4
CELL_LEN = 65.0
CELL_RAISE = 2.0            # gap under the cell, room for the plates' solder tabs
BAY_LEN = 69.0              # between the inner faces of the two plate slots (cell + spring)
LANE_W = CELL_D + 1.0
LANE_MARGIN = 2.0           # battery lane distance from the -Y wall
SLOT_W = 12.4               # plate width + clearance
PLATE_T = 0.5               # contact plate thickness
SLOT_T = 0.8                # plate thickness + clearance
PLATE_H = 12.0              # plate height (for the fit-check dummy)
DIMPLE_H = 1.0              # how far the + plate's dimple stands proud of the plate
CAP_RISE = 0.4              # flat-top cell: + cap height above the end shoulder
BLOCK_BACK = 1.6            # material behind the slot
# The lips in front of the slot lie inside the cell's end-face footprint (plate is narrower than
# the cell), so they must be thinner than dimple + cap or the cell rests on the lips instead of
# the + contact. check() enforces this. Slice with Arachne wall generator on Bambu Lab A1.
BLOCK_LIP = 0.6             # material in front of the slot (retains the plate)
BLOCK_SIDE = 2.0            # material beside the slot
WINDOW_W = 10.0             # opening in the lip; lips overlap the plate edges by ~1.2 mm
WINDOW_FROM = 3.0           # window starts this far above the floor
WIRE_NOTCH_W = 4.0          # exit for the solder tab / wire behind each slot
WIRE_NOTCH_H = 5.0
SADDLE_X = (-20.0, 20.0)    # saddle rib X positions
SADDLE_T = 3.0

# Electronics lane (+Y): SuperMini nRF52840 (+X) and HLK-LD2410S 24 GHz radar (-X)
LANE_GAP = 3.2              # gap between battery lane and electronics lane
BOARD_CLEAR = 0.3           # XY clearance around each PCB inside its corner stops
RAIL_LEDGE = 1.0            # width of PCB underside edge supported by each rail
RAIL_W = 1.5                # total rail wall thickness
STOP_T = 1.2                # corner stop wall thickness
STOP_W = 3.0                # corner stop arm length
STOP_ABOVE = 1.0            # corner stops rise this far above the PCB top face

# SuperMini nRF52840 cradle (+X side of +Y lane)
BOARD_L = 33.0              # nominal SuperMini PCB length (X)
BOARD_W = 18.0              # nominal SuperMini PCB width (Y)
BOARD_T = 1.2               # PCB thickness
BOARD_X = 20.5              # SuperMini centre X
RAIL_H = 2.5                # lifts SuperMini above bottom-side B+/B- pads and wiring

# Hi-Link HLK-LD2410S 24 GHz mmWave radar cradle (-X side of +Y lane)
# Note: Standard HLK-LD2410S PCB is 35.0 x 20.0 mm. If using the compact 22 x 16 mm
# sub-variant, set RADAR_L = 22.0 and RADAR_W = 16.0 below.
RADAR_L = 35.0              # nominal HLK-LD2410S PCB length (X)
RADAR_W = 20.0              # nominal HLK-LD2410S PCB width (Y)
RADAR_T = 1.2               # radar PCB thickness
RADAR_X = -19.5             # radar centre X
RADAR_RAIL_H = 16.0         # elevates patch antenna array toward the lid RF radome window
RADAR_PARTS_H = 2.5         # max component/shield height on top of the radar PCB

# Steam-proof lid with blind 1.2 mm RF radome pocket
LID_T = 3.0
LIP_CLEAR = 0.3             # locating lip clearance to the cavity wall
LIP_T = 1.6
LIP_H = 2.0
RADOME_L = 36.0             # blind interior pocket length over HLK-LD2410S antenna array
RADOME_W = 21.0             # blind interior pocket width
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
AXIS_Z = FLOOR + CELL_RAISE + CELL_D / 2    # cell axis height (absolute)
SLOT_X = BAY_LEN / 2 + SLOT_T / 2           # slot centre line (+/-)
BLOCK_TOP = FLOOR + CELL_RAISE + CELL_D / 2 + PLATE_H / 2 + 2.0
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


@dataclass(slots=True, frozen=True)
class PcbCradleSpec:
    pcb_l: float
    pcb_w: float
    pcb_t: float
    cx: float
    cy: float
    rail_h: float


def _add_pcb_cradle(base: cq.Workplane, spec: PcbCradleSpec) -> cq.Workplane:
    """Add supportless vertical side rails and L-shaped corner stops for a PCB."""
    stop_h = spec.rail_h + spec.pcb_t + STOP_ABOVE
    for sy in (-1, 1):
        ry = spec.cy + sy * (spec.pcb_w / 2 - RAIL_LEDGE + RAIL_W / 2)
        base = base.union(box(spec.pcb_l, RAIL_W, spec.rail_h, spec.cx, ry, FLOOR))
        for sx in (-1, 1):
            # X-end stop (retains PCB along X, spaced out by BOARD_CLEAR)
            sxp = spec.cx + sx * (spec.pcb_l / 2 + BOARD_CLEAR + STOP_T / 2)
            syp = spec.cy + sy * (spec.pcb_w / 2 + BOARD_CLEAR - STOP_W / 2)
            base = base.union(box(STOP_T, STOP_W, stop_h, sxp, syp, FLOOR))
            # Y-side stop (retains PCB along Y, spaced out by BOARD_CLEAR)
            sxp_y = spec.cx + sx * (spec.pcb_l / 2 + BOARD_CLEAR - STOP_W / 2)
            syp_y = spec.cy + sy * (spec.pcb_w / 2 + BOARD_CLEAR + STOP_T / 2)
            base = base.union(box(STOP_W, STOP_T, stop_h, sxp_y, syp_y, FLOOR))
    return base


def _add_battery_bay(base: cq.Workplane) -> cq.Workplane:
    """Add 18650 end blocks with 0.6 mm retaining lips, wire notches, and cell saddles."""
    block_len = BLOCK_LIP + SLOT_T + BLOCK_BACK
    block_w = SLOT_W + 2 * BLOCK_SIDE
    for sx in (-1, 1):
        inner_face = sx * BAY_LEN / 2
        bx = inner_face + sx * (block_len / 2 - BLOCK_LIP)
        block = box(block_len, block_w, BLOCK_TOP - FLOOR, bx, Y_BAT, FLOOR)
        slot = box(SLOT_T, SLOT_W, BLOCK_TOP, sx * SLOT_X, Y_BAT, FLOOR)
        window = box(BLOCK_LIP + 0.2, WINDOW_W, BLOCK_TOP, inner_face - sx * (BLOCK_LIP / 2), Y_BAT,
                     FLOOR + WINDOW_FROM)
        notch = box(BLOCK_BACK + 0.2, WIRE_NOTCH_W, WIRE_NOTCH_H,
                    sx * (SLOT_X + SLOT_T / 2 + BLOCK_BACK / 2), Y_BAT, FLOOR)
        base = base.union(block.cut(slot).cut(window).cut(notch))

    cradle = (cq.Workplane("YZ").workplane(offset=-OUTER_L).center(Y_BAT, AXIS_Z)
              .circle(CELL_D / 2 + 0.2).extrude(2 * OUTER_L))
    for sx_pos in SADDLE_X:
        rib = box(SADDLE_T, LANE_W, AXIS_Z - FLOOR, sx_pos, Y_BAT, FLOOR)
        base = base.union(rib.cut(cradle))
    return base


def check() -> None:
    """Fail early on parameter combinations that cannot be printed or assembled."""
    assert Y_BAT - LANE_W / 2 >= -INNER_W / 2, "battery lane does not fit in the cavity width"
    assert Y_RADAR + RADAR_W / 2 + BOARD_CLEAR + STOP_T <= INNER_W / 2 - 1.0, (
        "radar cradle does not fit in the cavity width"
    )
    assert Y_BRD + BOARD_W / 2 + BOARD_CLEAR + STOP_T <= INNER_W / 2 - 1.0, (
        "SuperMini cradle does not fit in the cavity width"
    )
    assert (RADAR_X + RADAR_L / 2 + BOARD_CLEAR + STOP_T) < (
        BOARD_X - BOARD_L / 2 - BOARD_CLEAR - STOP_T
    ), "radar cradle and SuperMini cradle overlap along X"
    assert SLOT_X + SLOT_T / 2 + BLOCK_BACK + 2.0 < INNER_L / 2, "no wire room behind the battery blocks"
    assert BLOCK_TOP < H - LIP_H - 0.5, "battery blocks hit the lid lip"
    # + contact: plate pushed back in its slot, dimple must reach past the lip face with margin
    reach = DIMPLE_H + CAP_RISE - (SLOT_T - PLATE_T) - BLOCK_LIP
    assert reach >= 0.3, f"+ contact only reaches {reach:.2f} mm past the lips (cell would rest on them)"
    assert (SLOT_W - WINDOW_W) / 2 >= 0.8, "lips overlap the plate edges too little to retain it"
    assert FLANGE_T > INSERT_DEPTH + 0.8, "flange too thin for the heat inserts"
    # The flange corner arc is centred on the screw axis, so the insert wall = FLANGE_R - INSERT_D / 2
    assert abs(SCREW_OFFSET - (WALL + FLANGE_W - FLANGE_R)) < 1e-6, "flange corner not centred on screw"
    assert FLANGE_R - INSERT_D / 2 >= 1.5, "insert wall to the flange edge too thin"
    # Closest approach of the groove's corner arc to the insert hole
    arc_c = GROOVE_OFFSET - GROOVE_R
    gap = 2 ** 0.5 * (SCREW_OFFSET - arc_c) - GROOVE_R - GROOVE_W / 2 - INSERT_D / 2
    assert gap >= 1.0, f"gasket groove only {gap:.2f} mm from an insert hole"
    # Radome window checks
    assert 0.8 <= RADOME_T <= 1.6, f"radome thickness {RADOME_T:.2f} mm outside 0.8..1.6 mm range"
    assert RADOME_L >= RADAR_L and RADOME_W >= RADAR_W, "radome pocket smaller than radar PCB"
    assert abs(RADAR_X) + RADOME_L / 2 < INNER_L / 2 - LIP_CLEAR - LIP_T, "radome pocket hits lid lip (X)"
    assert abs(Y_RADAR) + RADOME_W / 2 < INNER_W / 2 - LIP_CLEAR - LIP_T, "radome pocket hits lid lip (Y)"
    assert FLOOR + RADAR_RAIL_H + RADAR_T + RADAR_PARTS_H < H - 1.0, "radar components hit lid underside"


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

    # 18650 battery bay (-Y lane)
    base = _add_battery_bay(base)

    # SuperMini nRF52840 cradle (+X side of +Y lane)
    board_spec = PcbCradleSpec(BOARD_L, BOARD_W, BOARD_T, BOARD_X, Y_BRD, RAIL_H)
    base = _add_pcb_cradle(base, board_spec)

    # HLK-LD2410S 24 GHz radar cradle (-X side of +Y lane, elevated toward radome)
    radar_spec = PcbCradleSpec(RADAR_L, RADAR_W, RADAR_T, RADAR_X, Y_RADAR, RADAR_RAIL_H)
    base = _add_pcb_cradle(base, radar_spec)

    return base


# --------------------------------------------------------------------------------------
# Lid (modelled in place: underside at Z = H, solid outer top with blind 1.2 mm radome)
# --------------------------------------------------------------------------------------

def make_lid() -> cq.Workplane:
    lid = rrect(FL_L, FL_W, FLANGE_R, H, LID_T)
    lip_l, lip_w = INNER_L - 2 * LIP_CLEAR, INNER_W - 2 * LIP_CLEAR
    lip = (rrect(lip_l, lip_w, max(INNER_R - LIP_CLEAR, 0.5), H - LIP_H, LIP_H)
           .cut(rrect(lip_l - 2 * LIP_T, lip_w - 2 * LIP_T, 0.5, H - LIP_H - 1, LIP_H + 2)))
    lid = lid.union(lip)
    for x, y in SCREW_PTS:
        lid = lid.cut(cq.Workplane("XY").workplane(offset=H - 1).center(x, y)
                      .circle(SCREW_CLEAR_D / 2).extrude(LID_T + 2))
    # Blind interior pocket above HLK-LD2410S antenna array leaving uniform RADOME_T = 1.2 mm top wall
    radome_pocket = box(RADOME_L, RADOME_W, RADOME_DEPTH + 0.1, RADAR_X, Y_RADAR, H - 0.1)
    lid = lid.cut(radome_pocket)
    return lid


# --------------------------------------------------------------------------------------
# Dummy parts for the fit check (not printed)
# --------------------------------------------------------------------------------------

def make_dummies() -> dict[str, cq.Workplane]:
    cell = (cq.Workplane("YZ").workplane(offset=-CELL_LEN / 2).center(Y_BAT, AXIS_Z)
            .circle(CELL_D / 2).extrude(CELL_LEN))
    back = SLOT_X + (SLOT_T - PLATE_T) / 2  # plates pushed against the back of the slot
    plates = [box(PLATE_T, SLOT_W - 0.6, PLATE_H, sx * back, Y_BAT, AXIS_Z - PLATE_H / 2) for sx in (-1, 1)]
    board = box(BOARD_L, BOARD_W, BOARD_T, BOARD_X, Y_BRD, FLOOR + RAIL_H)
    board_parts = box(28.0, 16.0, 3.0, BOARD_X + 1.5, Y_BRD, FLOOR + RAIL_H + BOARD_T)
    radar = box(RADAR_L, RADAR_W, RADAR_T, RADAR_X, Y_RADAR, FLOOR + RADAR_RAIL_H)
    radar_parts = box(
        RADAR_L - 4.0,
        RADAR_W - 3.0,
        RADAR_PARTS_H,
        RADAR_X,
        Y_RADAR,
        FLOOR + RADAR_RAIL_H + RADAR_T,
    )
    return {
        "cell": cell,
        "plate_neg": plates[0],
        "plate_pos": plates[1],
        "board": board,
        "board_parts": board_parts,
        "radar": radar,
        "radar_parts": radar_parts,
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
    return base, lid, dummies


if __name__ == "__main__":
    build(Path(__file__).parent / "out")
