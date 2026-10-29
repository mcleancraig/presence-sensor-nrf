"""
Renders exact 2D cross-sections of all 3 presence sensor enclosure models with all dummy parts
(18650 cell, contact plates, SuperMini nRF52840 board + through-hole pins, HLK-LD2410S
20x20 mm radar + J2 5-pin header, 45 deg corner bracket, and USB-C plug) to out/sections/*.png.

Run:  python sections.py            (needs cadquery and matplotlib)
"""

from dataclasses import dataclass
from pathlib import Path

import cadquery as cq
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Patch
import numpy as np

import enclosure as e
import enclosure_variants as ev

COLORS: dict[str, str] = {
    "base": "#9a9a9a",
    "lid": "#5b7fc7",
    "corner_base": "#8e949e",
    "corner_lid": "#4a78c2",
    "corner_bracket": "#555b66",
    "vanity_base": "#8e949e",
    "vanity_lid": "#4a78c2",
    "cell": "#dd4433",
    "plate_neg": "#3355dd",
    "plate_pos": "#3355dd",
    "board": "#2ca02c",
    "board_parts": "#66c266",
    "radar": "#e67e22",
    "radar_parts": "#f39c12",
    "usb_c_plug": "#8e44ad",
}


@dataclass(slots=True, frozen=True)
class SectionSpec:
    name: str
    origin: tuple[float, float, float]
    normal: tuple[float, float, float]
    axes: tuple[int, int]
    title: str


def section(wp: cq.Workplane, origin: tuple[float, float, float], normal: tuple[float, float, float]) -> cq.Shape:
    plane = cq.Face.makePlane(1000, 1000, cq.Vector(*origin), cq.Vector(*normal))
    return wp.val().intersect(plane)


def plot(out_dir: Path, shapes: dict[str, cq.Workplane], spec: SectionSpec) -> None:
    fig, ax = plt.subplots(figsize=(13, 6))
    present_keys: list[str] = []
    for k, wp in shapes.items():
        sec = section(wp, spec.origin, spec.normal)
        faces = sec.Faces()
        if not faces:
            continue
        present_keys.append(k)
        for f in faces:
            v, t = f.tessellate(0.05)
            if not v or not t:
                continue
            pts = np.array([(p.x, p.y, p.z) for p in v])[:, list(spec.axes)]
            polys = [pts[list(tri)] for tri in t]
            ax.add_collection(
                PolyCollection(
                    polys,
                    facecolors=COLORS[k],
                    edgecolors=COLORS[k],
                    linewidths=0.3,
                    alpha=0.85 if k.endswith("_parts") else 1.0,
                )
            )
    ax.autoscale()
    ax.set_aspect("equal")
    ax.grid(True, lw=0.3)
    ax.set_title(spec.title)
    ax.set_xlabel("XYZ"[spec.axes[0]] + " (mm)")
    ax.set_ylabel("XYZ"[spec.axes[1]] + " (mm)")
    if present_keys:
        handles = [Patch(facecolor=COLORS[k], label=k) for k in present_keys]
        ax.legend(handles=handles, loc="upper right", fontsize=8, framealpha=0.9)
    fig.tight_layout()
    fig.savefig(out_dir / f"{spec.name}.png", dpi=120)
    plt.close(fig)


def _model1_specs() -> list[SectionSpec]:
    z_board = e.FLOOR + e.BOARD_RAIL_H + e.BOARD_T / 2
    z_radar = e.FLOOR + e.RADAR_RAIL_H + e.RADAR_T / 2
    z_radome = e.H + e.RADOME_DEPTH / 2
    z_flange = e.H - 0.5
    return [
        SectionSpec("z_mid_cell", (0.0, 0.0, e.AXIS_Z), (0, 0, 1), (0, 1),
                    f"XY section at Z={e.AXIS_Z:.1f} mm (18650 cell mid-plane, contact plates, radar J2 header pins)"),
        SectionSpec("z_board", (0.0, 0.0, z_board), (0, 0, 1), (0, 1),
                    f"XY section at Z={z_board:.1f} mm (SuperMini nRF52840 PCB, corner stops, cell saddles)"),
        SectionSpec("z_radar", (0.0, 0.0, z_radar), (0, 0, 1), (0, 1),
                    f"XY section at Z={z_radar:.1f} mm (20x20 mm HLK-LD2410S PCB, open +X J2 exit, corner stops)"),
        SectionSpec("z_radome", (0.0, 0.0, z_radome), (0, 0, 1), (0, 1),
                    f"XY section at Z={z_radome:.1f} mm (blind 22x22 mm RF radome pocket in lid, M3 screw holes)"),
        SectionSpec("z_flange", (0.0, 0.0, z_flange), (0, 0, 1), (0, 1),
                    f"XY section at Z={z_flange:.1f} mm (EPDM gasket groove, M3 heat-set insert bosses, lid locating lip)"),
        SectionSpec("y_battery", (0.0, e.Y_BAT, 0.0), (0, 1, 0), (0, 2),
                    f"XZ section at Y={e.Y_BAT:.1f} mm (18650 battery axis, 0.6 mm slot lips, wire notches, saddles)"),
        SectionSpec("y_electronics", (0.0, e.Y_ELEC, 0.0), (0, 1, 0), (0, 2),
                    f"XZ section at Y={e.Y_ELEC:.1f} mm (20x20 mm HLK-LD2410S + J2 header under 1.2 mm radome + SuperMini)"),
        SectionSpec("x_center", (0.0, 0.0, 0.0), (1, 0, 0), (1, 2),
                    "YZ section at X=0.0 mm (enclosure centre: 18650 cell lane vs electronics lane)"),
        SectionSpec("x_radar", (e.RADAR_X, 0.0, 0.0), (1, 0, 0), (1, 2),
                    f"YZ section at X={e.RADAR_X:.1f} mm (20x20 mm HLK-LD2410S cradle, 1.2 mm blind radome, 18650 saddle)"),
        SectionSpec("x_board", (e.BOARD_X, 0.0, 0.0), (1, 0, 0), (1, 2),
                    f"YZ section at X={e.BOARD_X:.1f} mm (SuperMini nRF52840 cradle, -Z pin relief, 18650 saddle)"),
        SectionSpec("x_slot_neg", (-e.SLOT_X, 0.0, 0.0), (1, 0, 0), (1, 2),
                    f"YZ section at X={-e.SLOT_X:.1f} mm (- spring contact plate slot & side wall)"),
        SectionSpec("x_slot_pos", (e.SLOT_X, 0.0, 0.0), (1, 0, 0), (1, 2),
                    f"YZ section at X={e.SLOT_X:.1f} mm (+ dimple contact plate slot & side wall)"),
    ]


def main() -> None:
    out_dir = Path(__file__).parent / "out" / "sections"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Model 1 sections
    base, lid, dm1 = e.make_base(), e.make_lid(), e.make_dummies()
    shapes1: dict[str, cq.Workplane] = {"base": base, "lid": lid, **dm1}
    for spec in _model1_specs():
        plot(out_dir, shapes1, spec)

    # Model 2 (45 deg Corner Snap-Fit + Bracket) sections
    c_base, c_lid, c_br = ev.make_corner_base(), ev.make_corner_lid(), ev.make_corner_bracket()
    shapes2: dict[str, cq.Workplane] = {"corner_base": c_base, "corner_lid": c_lid, "corner_bracket": c_br, **dm1}
    plot(out_dir, shapes2, SectionSpec(
        "corner_snap_y", (0.0, e.Y_ELEC, 0.0), (0, 1, 0), (0, 2),
        f"Model 2 XZ section at Y={e.Y_ELEC:.1f} mm (Snap-Fit Corner Enclosure + 45 deg Bracket + Pry Slots)"
    ))
    plot(out_dir, shapes2, SectionSpec(
        "corner_bracket_x", (-ev.SNAP_X_OFF, 0.0, 0.0), (1, 0, 0), (1, 2),
        f"Model 2 YZ section at X={-ev.SNAP_X_OFF:.1f} mm (Snap-Fit Catches, Slide Rails & 90 deg / 45 deg Corner Bracket)"
    ))

    # Model 3 (Freestanding Vanity Pod with USB-C Pass-Through) sections
    v_base, v_lid, dm3 = ev.make_vanity_base(), ev.make_vanity_lid(), ev.make_vanity_dummies()
    shapes3: dict[str, cq.Workplane] = {"vanity_base": v_base, "vanity_lid": v_lid, **dm3}
    plot(out_dir, shapes3, SectionSpec(
        "vanity_usbc_y", (0.0, e.Y_ELEC, 0.0), (0, 1, 0), (0, 2),
        f"Model 3 XZ section at Y={e.Y_ELEC:.1f} mm (Freestanding Vanity Pod + SuperMini USB-C Pass-Through & Overmold Boot)"
    ))
    plot(out_dir, shapes3, SectionSpec(
        "vanity_standing_x", (ev.BOARD_X_VANITY, 0.0, 0.0), (1, 0, 0), (1, 2),
        f"Model 3 YZ section at X={ev.BOARD_X_VANITY:.1f} mm (Vanity Pod -Y Standing Foot, 18650 Low-CG Bay & SuperMini)"
    ))

    print(f"16 sections written to {out_dir}")


if __name__ == "__main__":
    main()
