"""
Renders exact 2D cross-sections of the presence sensor enclosure with all dummy parts
(18650 cell, contact plates, SuperMini nRF52840 board + through-hole pins, HLK-LD2410S
20x20 mm radar + J2 5-pin header shroud/pins/solder-tails) to out/sections/*.png.

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

COLORS: dict[str, str] = {
    "base": "#9a9a9a",
    "lid": "#5b7fc7",
    "cell": "#dd4433",
    "plate_neg": "#3355dd",
    "plate_pos": "#3355dd",
    "board": "#2ca02c",
    "board_parts": "#66c266",
    "radar": "#e67e22",
    "radar_parts": "#f39c12",
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


def main() -> None:
    out_dir = Path(__file__).parent / "out" / "sections"
    out_dir.mkdir(parents=True, exist_ok=True)
    base, lid, dm = e.make_base(), e.make_lid(), e.make_dummies()
    shapes: dict[str, cq.Workplane] = {"base": base, "lid": lid, **dm}

    z_board = e.FLOOR + e.BOARD_RAIL_H + e.BOARD_T / 2
    z_radar = e.FLOOR + e.RADAR_RAIL_H + e.RADAR_T / 2
    z_radome = e.H + e.RADOME_DEPTH / 2
    z_flange = e.H - 0.5

    specs: list[SectionSpec] = [
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

    for spec in specs:
        plot(out_dir, shapes, spec)

    print(f"12 sections written to {out_dir}")


if __name__ == "__main__":
    main()
