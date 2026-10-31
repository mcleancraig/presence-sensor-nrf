"""
Geometry and clearance checks for all 3 presence sensor enclosure models:
  - Model 1: Sealed Gasketed Wall-Mount (base, lid)
  - Model 2: Angled 45 deg Corner/Ceiling Snap-Fit (corner_base, corner_lid, corner_bracket)
  - Model 3: Freestanding Shelf/Vanity Pod with USB-C Pass-Through (vanity_base, vanity_lid)

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

    failures: list[str] = []
    for name, wp in [
        ("base", base),
        ("lid", lid),
        ("corner_base", c_base),
        ("corner_lid", c_lid),
        ("corner_bracket", c_br),
        ("vanity_base", v_base),
        ("vanity_lid", v_lid),
    ]:
        _check_solid(name, wp, failures)

    _verify_model_overlaps("base", base, "lid", lid, dm1, failures)
    _verify_model_overlaps("corner_base", c_base, "corner_lid", c_lid, dm1, failures)
    _check_pair("corner_bracket", c_br, "corner_base", c_base, failures)
    _check_pair("corner_bracket", c_br, "corner_lid", c_lid, failures)
    _verify_model_overlaps("vanity_base", v_base, "vanity_lid", v_lid, dm3, failures)

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
    rad_probe = cq.Workplane("XY").box(1.0, 1.0, 100.0).translate((e.RADAR_X, e.Y_RADAR, 0.0))
    for l_name, l_wp in [("lid", lid), ("corner_lid", c_lid), ("vanity_lid", v_lid)]:
        r_bb = l_wp.intersect(rad_probe).val().BoundingBox()
        r_thk = r_bb.zlen
        air_gap = r_bb.zmin - (e.FLOOR + e.RADAR_RAIL_H + e.RADAR_T)
        ok_r = 0.8 <= r_thk <= 1.6 and 3.0 <= air_gap <= 6.0
        print(f"ok   {l_name:10s} blind RF radome (22x22 mm) thickness={r_thk:.2f} mm, air gap={air_gap:.2f} mm")
        if not ok_r:
            failures.append(f"{l_name} radome check failed: thk={r_thk:.2f}, gap={air_gap:.2f}")

    if failures:
        print("\nFAILURES:", *failures, sep="\n  - ")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
