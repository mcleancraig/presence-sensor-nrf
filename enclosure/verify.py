"""
Builds the presence sensor enclosure and checks the fit numerically: dummy parts
(18650 cell, contact plates, SuperMini nRF52840 board + through-hole pins/parts,
HLK-LD2410S 20x20 mm radar + J2 5-pin header shroud/pins/solder-tails/crystal)
must not intersect the printed base or lid, and the lid must not intersect the base.
Also verifies the + contact reach, radar/SuperMini under-board clearances, and the
1.2 mm blind RF radome thickness.

Run:  python verify.py
"""

from pathlib import Path

import cadquery as cq

import enclosure as e


def overlap(a: cq.Workplane, b: cq.Workplane) -> float:
    """Intersection volume of two CadQuery workplanes, mm^3."""
    common = a.val().intersect(b.val())
    return common.Volume() if common.isValid() else float("nan")


def main() -> None:
    base, lid, dummies = e.build(Path(__file__).parent / "out")

    failures = 0
    for name, shape in (("base", base), ("lid", lid)):
        s = shape.val()
        bb = s.BoundingBox(0.01)
        solids_count = len(shape.solids().vals())
        valid = bool(s.isValid()) and solids_count == 1
        failures += not valid
        print(
            f"{name:5s} valid={s.isValid()} solids={solids_count} "
            f"size={bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm  "
            f"volume={s.Volume() / 1000:.1f} cm^3"
        )

    checks = [("lid", lid, "base", base)]
    checks += [(n, d, "base", base) for n, d in dummies.items()]
    checks += [(n, d, "lid", lid) for n, d in dummies.items()]
    for an, a, bn, b in checks:
        v = overlap(a, b)
        ok = v < 0.01
        failures += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {an:15s} vs {bn:5s} overlap {v:8.3f} mm^3")

    # + contact must reach past the 0.6 mm retaining lips; report spring compression
    plate_face = e.SLOT_X + e.SLOT_T / 2 - e.PLATE_T          # plate front face, pushed back
    lip_face = e.BAY_LEN / 2 - e.BLOCK_LIP
    reach = lip_face - (plate_face - e.DIMPLE_H - e.CAP_RISE)
    reach_ok = reach >= 0.30
    failures += not reach_ok
    print(f"{'ok  ' if reach_ok else 'FAIL'} + contact reaches {reach:.2f} mm past the lip face (must be >= 0.30 mm)")

    spring_len = 2 * plate_face - e.DIMPLE_H - e.CELL_LEN
    print(f"info spring compressed to {spring_len:.2f} mm with the cell against the + dimple")
    print(f"info cell top to lid lip bottom: {e.H - e.LIP_H - (e.AXIS_Z + e.CELL_D / 2):.2f} mm")
    print(
        f"info HLK-LD2410S ({e.RADAR_L:.1f}x{e.RADAR_W:.1f}x{e.RADAR_T:.1f} mm, R={e.RADAR_CORNER_R:.1f} mm): "
        f"-Z under-radar clearance={e.RADAR_RAIL_H:.1f} mm, SuperMini -Z clearance={e.BOARD_RAIL_H:.1f} mm"
    )

    # Verify radome thickness above the HLK-LD2410S antenna array
    radome_probe = e.box(1.0, 1.0, e.LID_T + 2.0, e.RADAR_X, e.Y_RADAR, e.H - 1.0)
    radome_wall = lid.val().intersect(radome_probe.val())
    radome_t_measured = radome_wall.BoundingBox().zlen
    radome_ok = abs(radome_t_measured - e.RADOME_T) < 0.01
    failures += not radome_ok
    air_gap = (e.H + e.RADOME_DEPTH) - (e.FLOOR + e.RADAR_RAIL_H + e.RADAR_T)
    print(
        f"{'ok  ' if radome_ok else 'FAIL'} blind RF radome ({e.RADOME_L:.0f}x{e.RADOME_W:.0f} mm) "
        f"thickness={radome_t_measured:.2f} mm (target {e.RADOME_T:.2f} mm), "
        f"antenna-to-radome air gap={air_gap:.2f} mm"
    )

    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
