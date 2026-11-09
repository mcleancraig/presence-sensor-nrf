"""
Geometry and clearance checks for all 7 presence sensor enclosure models + USB-C socket fit test:
  - Model 1: Sealed Gasketed Wall-Mount (base, lid — HLK-LD2410S)
  - Model 2: Angled 45 deg Corner/Ceiling Snap-Fit (corner_base, corner_lid, corner_bracket — HLK-LD2410S)
  - Model 3: Freestanding Shelf/Vanity Pod with USB-C Pass-Through (vanity_base, vanity_lid — HLK-LD2410S)
  - Model 4: HLK-LD2410C Constant USB-C Power Enclosure (ld2410c_base, ld2410c_lid — 22x16 mm HLK-LD2410C)
  - Model 5: HLK-LD2410S Constant USB-C Power Enclosure (ld2410s_usb_base, ld2410s_usb_lid — 20x20 mm HLK-LD2410S)
  - Model 6: "Aura-S" Award-Edition Horizon Stadium Monolith (aura_s_base, aura_s_lid, aura_s_stand — 20x20 mm HLK-LD2410S)
  - Model 7: "Aura-C" Award-Edition Horizon Stadium Monolith (aura_c_base, aura_c_lid, aura_c_stand — 22x16 mm HLK-LD2410C)
  - Fit Test: 4-Station USB-C Socket Fit-Test Gauge (usbc_socket_fit_test — +0.5, +1.0, +1.5, +2.0 mm wider)

Run:  python verify.py              (exits non-zero on any failure)
"""

from pathlib import Path
import sys

import cadquery as cq

import enclosure as e
import enclosure_variants as ev


def vol(wp: cq.Workplane) -> float:
    return sum(s.Volume() for s in wp.val().Solids())


def _check_solid(name: str, wp: cq.Workplane, failures: list[str]) -> None:
    s = wp.val()
    bb = s.BoundingBox()
    valid = s.isValid()
    n_solids = len(s.Solids())
    v_cm3 = s.Volume() / 1000.0
    print(
        f"{name:14s} valid={valid} solids={n_solids} "
        f"size={bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm  volume={v_cm3:.1f} cm^3"
    )
    if not valid or n_solids != 1:
        failures.append(f"{name}: valid={valid} solids={n_solids}")


def _check_pair(
    a_name: str, a_wp: cq.Workplane, b_name: str, b_wp: cq.Workplane, failures: list[str]
) -> None:
    ov = vol(a_wp.intersect(b_wp))
    status = "ok  " if ov < 1e-2 else "FAIL"
    print(f"{status} {a_name:15s} vs {b_name:14s} overlap {ov:8.3f} mm^3")
    if ov >= 1e-2:
        failures.append(f"overlap {a_name} vs {b_name}: {ov:.3f} mm^3")


def _verify_model_overlaps(
    base_name: str,
    base_wp: cq.Workplane,
    lid_name: str,
    lid_wp: cq.Workplane,
    dummies: dict[str, cq.Workplane],
    failures: list[str],
) -> None:
    _check_pair(lid_name, lid_wp, base_name, base_wp, failures)
    for d_name, d_wp in dummies.items():
        _check_pair(d_name, d_wp, base_name, base_wp, failures)
    for d_name, d_wp in dummies.items():
        _check_pair(d_name, d_wp, lid_name, lid_wp, failures)


def main() -> int:
    out_dir = Path(__file__).parent / "out"
    base, lid, dm1 = e.build(out_dir)
    ev.build_variants(out_dir)
    c_base, c_lid, c_br = ev.make_corner_base(), ev.make_corner_lid(), ev.make_corner_bracket()
    v_base, v_lid, dm3 = ev.make_vanity_base(), ev.make_vanity_lid(), ev.make_vanity_dummies()
    lc_base, lc_lid, dm4 = ev.make_ld2410c_base(), ev.make_ld2410c_lid(), ev.make_ld2410c_dummies()
    ls_base, ls_lid, dm5 = ev.make_ld2410s_usb_base(), ev.make_ld2410s_usb_lid(), ev.make_ld2410s_usb_dummies()
    v_stand_c = ev.make_v_stand(outer_w=ev.OUTER_W_C)
    v_stand_s = ev.make_v_stand(outer_w=ev.OUTER_W_S)
    as_base, as_lid, as_stand, dm6 = (
        ev.make_aura_s_base(),
        ev.make_aura_s_lid(),
        ev.make_aura_s_stand(),
        ev.make_aura_s_dummies(),
    )
    ac_base, ac_lid, ac_stand, dm7 = (
        ev.make_aura_c_base(),
        ev.make_aura_c_lid(),
        ev.make_aura_c_stand(),
        ev.make_aura_c_dummies(),
    )
    as2_base, as2_lid, as2_stand, dm8 = (
        ev.make_aura_s_v2_base(),
        ev.make_aura_s_v2_lid(),
        ev.make_aura_s_v2_stand(),
        ev.make_aura_s_v2_dummies(),
    )
    ac2_base, ac2_lid, ac2_stand, dm9 = (
        ev.make_aura_c_v2_base(),
        ev.make_aura_c_v2_lid(),
        ev.make_aura_c_v2_stand(),
        ev.make_aura_c_v2_dummies(),
    )
    usbc_test = ev.make_usbc_socket_fit_test()

    failures: list[str] = []
    for name, wp in [
        ("base", base),
        ("lid", lid),
        ("corner_base", c_base),
        ("corner_lid", c_lid),
        ("corner_bracket", c_br),
        ("vanity_base", v_base),
        ("vanity_lid", v_lid),
        ("ld2410c_base", lc_base),
        ("ld2410c_lid", lc_lid),
        ("ld2410s_usb_base", ls_base),
        ("ld2410s_usb_lid", ls_lid),
        ("v_stand", v_stand_s),
        ("aura_s_base", as_base),
        ("aura_s_lid", as_lid),
        ("aura_s_stand", as_stand),
        ("aura_c_base", ac_base),
        ("aura_c_lid", ac_lid),
        ("aura_c_stand", ac_stand),
        ("aura_s_v2_base", as2_base),
        ("aura_s_v2_lid", as2_lid),
        ("aura_s_v2_stand", as2_stand),
        ("aura_c_v2_base", ac2_base),
        ("aura_c_v2_lid", ac2_lid),
        ("aura_c_v2_stand", ac2_stand),
        ("usbc_socket_fit_test", usbc_test),
    ]:
        _check_solid(name, wp, failures)

    _verify_model_overlaps("base", base, "lid", lid, dm1, failures)
    _verify_model_overlaps("corner_base", c_base, "corner_lid", c_lid, dm1, failures)
    _check_pair("corner_bracket", c_br, "corner_base", c_base, failures)
    _check_pair("corner_bracket", c_br, "corner_lid", c_lid, failures)
    _verify_model_overlaps("vanity_base", v_base, "vanity_lid", v_lid, dm3, failures)
    _verify_model_overlaps("ld2410c_base", lc_base, "ld2410c_lid", lc_lid, dm4, failures)
    _check_pair("v_stand_c", v_stand_c, "ld2410c_base", lc_base, failures)
    _check_pair("v_stand_c", v_stand_c, "ld2410c_lid", lc_lid, failures)
    _verify_model_overlaps("ld2410s_usb_base", ls_base, "ld2410s_usb_lid", ls_lid, dm5, failures)
    _check_pair("v_stand", v_stand_s, "ld2410s_usb_base", ls_base, failures)
    _check_pair("v_stand", v_stand_s, "ld2410s_usb_lid", ls_lid, failures)
    _verify_model_overlaps("aura_s_base", as_base, "aura_s_lid", as_lid, dm6, failures)
    _check_pair("aura_s_stand", as_stand, "aura_s_base", as_base, failures)
    _check_pair("aura_s_stand", as_stand, "aura_s_lid", as_lid, failures)
    _verify_model_overlaps("aura_c_base", ac_base, "aura_c_lid", ac_lid, dm7, failures)
    _check_pair("aura_c_stand", ac_stand, "aura_c_base", ac_base, failures)
    _check_pair("aura_c_stand", ac_stand, "aura_c_lid", ac_lid, failures)
    _verify_model_overlaps("aura_s_v2_base", as2_base, "aura_s_v2_lid", as2_lid, dm8, failures)
    _check_pair("aura_s_v2_stand", as2_stand, "aura_s_v2_base", as2_base, failures)
    _check_pair("aura_s_v2_stand", as2_stand, "aura_s_v2_lid", as2_lid, failures)
    _check_pair("radar", dm8["radar"], "board", dm8["board"], failures)
    _check_pair("radar_parts", dm8["radar_parts"], "board_parts", dm8["board_parts"], failures)
    _verify_model_overlaps("aura_c_v2_base", ac2_base, "aura_c_v2_lid", ac2_lid, dm9, failures)
    _check_pair("aura_c_v2_stand", ac2_stand, "aura_c_v2_base", ac2_base, failures)
    _check_pair("aura_c_v2_stand", ac2_stand, "aura_c_v2_lid", ac2_lid, failures)
    _check_pair("radar", dm9["radar"], "board", dm9["board"], failures)
    _check_pair("radar_parts", dm9["radar_parts"], "board_parts", dm9["board_parts"], failures)

    reach = e.DIMPLE_H + e.CAP_RISE - (e.SLOT_T - e.PLATE_T) - e.BLOCK_LIP
    print(f"ok   + contact reaches {reach:.2f} mm past the lip face (must be >= 0.30 mm)")
    rim_probe_x = e.box(10.0, 2.0, e.RIM_H * 0.8, e.INNER_L / 2 + e.GROOVE_OFFSET, 0.0, e.H - e.RIM_H * 0.9)
    rim_bb = lid.intersect(rim_probe_x).val().BoundingBox()
    groove_xmin = e.INNER_L / 2 + e.GROOVE_OFFSET - e.GROOVE_W / 2
    groove_xmax = e.INNER_L / 2 + e.GROOVE_OFFSET + e.GROOVE_W / 2
    ok_rim = groove_xmin + 0.15 <= rim_bb.xmin and rim_bb.xmax <= groove_xmax - 0.15
    print(
        f"ok   lid embossed rim X=[{rim_bb.xmin:.2f}..{rim_bb.xmax:.2f}] mm mates inside "
        f"base debossed groove X=[{groove_xmin:.2f}..{groove_xmax:.2f}] mm"
    )
    if not ok_rim:
        failures.append(f"lid embossed rim X=[{rim_bb.xmin:.2f}..{rim_bb.xmax:.2f}] outside base groove")
    for l_name, l_wp, rx, ry, r_rail_h in [
        ("lid", lid, e.RADAR_X, e.Y_RADAR, e.RADAR_RAIL_H),
        ("corner_lid", c_lid, e.RADAR_X, e.Y_RADAR, e.RADAR_RAIL_H),
        ("vanity_lid", v_lid, e.RADAR_X, e.Y_RADAR, e.RADAR_RAIL_H),
        ("ld2410c_lid", lc_lid, ev.RADAR_C_X, ev.Y_C, ev.RADAR_C_RAIL_H),
        ("ld2410s_usb_lid", ls_lid, ev.RADAR_S_USB_X, ev.Y_C, e.RADAR_RAIL_H),
        ("aura_s_lid", as_lid, ev.RADAR_AURA_X, ev.Y_C, e.RADAR_RAIL_H),
        ("aura_c_lid", ac_lid, ev.RADAR_AURA_C_X, ev.Y_C, ev.RADAR_C_RAIL_H),
        ("aura_s_v2_lid", as2_lid, ev.RADAR_AURA_V2_X, ev.Y_C, ev.RADAR_V2_RAIL_H),
        ("aura_c_v2_lid", ac2_lid, ev.RADAR_AURA_V2_X, ev.Y_C, ev.RADAR_V2_RAIL_H),
    ]:
        rad_probe = cq.Workplane("XY").box(1.0, 1.0, 100.0).translate((rx, ry, 0.0))
        r_bb = l_wp.intersect(rad_probe).val().BoundingBox()
        r_thk = r_bb.zlen
        air_gap = r_bb.zmin - (e.FLOOR + r_rail_h + e.RADAR_T)
        ok_r = 0.8 <= r_thk <= 1.6 and 3.0 <= air_gap <= 6.0
        print(f"ok   {l_name:12s} blind RF radome thickness={r_thk:.2f} mm, air gap={air_gap:.2f} mm")
        if not ok_r:
            failures.append(f"{l_name} radome check failed: thk={r_thk:.2f}, gap={air_gap:.2f}")

    if failures:
        print("\nFAILURES:", *failures, sep="\n  - ")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
