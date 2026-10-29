"""
Additional parametric enclosure variants for the presence sensor
(SuperMini nRF52840 + Hi-Link HLK-LD2410S 20x20 mm 24 GHz radar + one 18650 cell):

  Model 2 (Corner / Ceiling 45 deg Mount):
    - corner_base.stl / .step    : Compact flangeless snap-fit base with side slide rails
    - corner_lid.stl / .step     : Snap-fit lid with blind 22x22x1.2 mm RF radome pocket
    - corner_bracket.stl / .step : 90 deg room-corner / ceiling bracket holding the sensor at 45 deg

  Model 3 (Freestanding Vanity / Shelf Pod with USB-C Pass-Through):
    - vanity_base.stl / .step    : Upright shelf/vanity base (-Y stabilizer foot + USB-C port)
    - vanity_lid.stl / .step     : Matching snap-fit lid with flush -Y standing foot & 1.2 mm radome
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


def make_snap_lid(with_vanity_foot: bool = False) -> cq.Workplane:
    """Build compact flangeless snap-fit lid with blind 22x22x1.2 mm RF radome pocket."""
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
    return lid.cut(radome_pocket)


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
    """Compact snap-fit lid with blind 1.20 mm RF radome pocket for Model 2."""
    return make_snap_lid(with_vanity_foot=False)


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
    """Snap-fit lid for Model 3 with flush -Y standing foot and blind 1.20 mm RF radome."""
    return make_snap_lid(with_vanity_foot=True)


def make_vanity_dummies() -> dict[str, cq.Workplane]:
    """Internal dummies at BOARD_X_VANITY plus external USB-C charging plug dummy."""
    dm = e.make_dummies(board_x=BOARD_X_VANITY)
    tongue = e.box(6.5, 8.4, 2.6, e.INNER_L / 2 + 1.0, e.Y_BRD, Z_USBC - 1.3)
    overmold = e.box(14.0, 11.4, 6.0, e.OUTER_L / 2 + 6.4, e.Y_BRD, Z_USBC - 3.0)
    dm["usb_c_plug"] = tongue.union(overmold)
    return dm


def build_variants(out_dir: Path) -> None:
    """Export all STL and STEP artifacts for Model 2 (Corner) and Model 3 (Vanity)."""
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

    # Model 3: Freestanding Shelf / Vanity Pod with USB-C Pass-Through
    v_base, v_lid, v_dm = make_vanity_base(), make_vanity_lid(), make_vanity_dummies()
    cq.exporters.export(v_base, str(out_dir / "vanity_base.step"))
    cq.exporters.export(v_base, str(out_dir / "vanity_base.stl"), tolerance=0.05, angularTolerance=0.1)
    v_lid_print = v_lid.translate((0, 0, -e.H - e.LID_T)).rotate((0, 0, 0), (1, 0, 0), 180)
    cq.exporters.export(v_lid, str(out_dir / "vanity_lid.step"))
    cq.exporters.export(v_lid_print, str(out_dir / "vanity_lid.stl"), tolerance=0.05, angularTolerance=0.1)

    v_asm = cq.Assembly(name="vanity_sensor_enclosure")
    v_asm.add(v_base, name="vanity_base", color=cq.Color(0.85, 0.85, 0.85))
    v_asm.add(v_lid, name="vanity_lid", color=cq.Color(0.3, 0.5, 0.8, 0.6))
    v_asm.export(str(out_dir / "vanity_assembly.step"))

    v_fit = cq.Assembly(name="vanity_fit_check")
    v_fit.add(v_base, name="vanity_base", color=cq.Color(0.85, 0.85, 0.85))
    v_fit.add(v_lid, name="vanity_lid", color=cq.Color(0.3, 0.5, 0.8, 0.4))
    for k, shp in v_dm.items():
        v_fit.add(shp, name=k, color=cq.Color(0.9, 0.3, 0.2))
    v_fit.export(str(out_dir / "vanity_fit_check.step"))


if __name__ == "__main__":
    build_variants(Path(__file__).parent / "out")
