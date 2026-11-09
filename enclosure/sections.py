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
    "ld2410c_base": "#8e949e",
    "ld2410c_lid": "#4a78c2",
    "ld2410s_usb_base": "#8e949e",
    "ld2410s_usb_lid": "#4a78c2",
    "v_stand": "#555b66",
    "aura_s_base": "#7f8790",
    "aura_s_lid": "#3b6db3",
    "aura_s_stand": "#484e58",
    "aura_c_base": "#7f8790",
    "aura_c_lid": "#3b6db3",
    "aura_c_stand": "#484e58",
    "aura_s_v2_base": "#7f8790",
    "aura_s_v2_lid": "#3b6db3",
    "aura_s_v2_stand": "#484e58",
    "aura_c_v2_base": "#7f8790",
    "aura_c_v2_lid": "#3b6db3",
    "aura_c_v2_stand": "#484e58",
    "usbc_socket_fit_test": "#7f8c8d",
    "fit_test_labels": "#2c3e50",
    "cell": "#dd4433",
    "plate_neg": "#3355dd",
    "plate_pos": "#3355dd",
    "board": "#2ca02c",
    "board_parts": "#66c266",
    "radar": "#e67e22",
    "radar_parts": "#f39c12",
    "dupont_5p": "#d35400",
    "direct_wires": "#d35400",
    "usb_c_socket": "#16a085",
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

    # Model 4 (Sleek Desktop Battery-Free HLK-LD2410C 22x16 mm Enclosure + Detachable V-Stand) sections
    lc_base, lc_lid, dm4 = ev.make_ld2410c_base(), ev.make_ld2410c_lid(), ev.make_ld2410c_dummies()
    v_stand_c = ev.make_v_stand(outer_w=ev.OUTER_W_C)
    shapes4: dict[str, cq.Workplane] = {"ld2410c_base": lc_base, "ld2410c_lid": lc_lid, "v_stand": v_stand_c, **dm4}
    z_radar_c = e.FLOOR + ev.RADAR_C_RAIL_H + ev.RADAR_C_T / 2
    plot(out_dir, shapes4, SectionSpec(
        "ld2410c_z_radar", (0.0, 0.0, z_radar_c), (0, 0, 1), (0, 1),
        f"Model 4 XY section at Z={z_radar_c:.1f} mm (Sleek 28.8 mm wide HLK-LD2410C Pod + Detachable Inverted-V Stand)"
    ))
    plot(out_dir, shapes4, SectionSpec(
        "ld2410c_usbc_y", (0.0, ev.Y_C, 0.0), (0, 1, 0), (0, 2),
        f"Model 4 XZ section at Y={ev.Y_C:.1f} mm (22x16 mm HLK-LD2410C + SuperMini + Panel-Mount USB-C Socket, No Screw Tabs)"
    ))
    plot(out_dir, shapes4, SectionSpec(
        "ld2410c_radar_x", (ev.RADAR_C_X, 0.0, 0.0), (1, 0, 0), (1, 2),
        f"Model 4 YZ section at X={ev.RADAR_C_X:.1f} mm (Sleek Battery-Free 22x16 mm HLK-LD2410C Cradle & 1.2 mm Radome)"
    ))

    # Model 5 (Sleek Desktop Battery-Free HLK-LD2410S 20x20 mm Enclosure + Detachable V-Stand) sections
    ls_base, ls_lid, dm5 = ev.make_ld2410s_usb_base(), ev.make_ld2410s_usb_lid(), ev.make_ld2410s_usb_dummies()
    v_stand_s = ev.make_v_stand(outer_w=ev.OUTER_W_S)
    shapes5: dict[str, cq.Workplane] = {"ld2410s_usb_base": ls_base, "ld2410s_usb_lid": ls_lid, "v_stand": v_stand_s, **dm5}
    z_radar_s_usb = e.FLOOR + e.RADAR_RAIL_H + e.RADAR_T / 2
    z_v_stand = ev.V_MORTISE_Z0 + ev.V_MORTISE_L_Z / 2
    plot(out_dir, shapes5, SectionSpec(
        "ld2410s_usb_z_radar", (0.0, 0.0, z_v_stand), (0, 0, 1), (0, 1),
        f"Model 5 XY section at Z={z_v_stand:.1f} mm (Sleek Desktop HLK-LD2410S Pod + Slotted-In Inverted-V Stand)"
    ))
    plot(out_dir, shapes5, SectionSpec(
        "ld2410s_usb_usbc_y", (0.0, ev.Y_C, 0.0), (0, 1, 0), (0, 2),
        f"Model 5 XZ section at Y={ev.Y_C:.1f} mm (20x20 mm HLK-LD2410S + SuperMini + Panel-Mount USB-C Socket, No Screw Tabs)"
    ))
    plot(out_dir, shapes5, SectionSpec(
        "ld2410s_usb_radar_x", (-ev.V_MORTISE_X_OFF, 0.0, 0.0), (1, 0, 0), (1, 2),
        f"Model 5 YZ section at X={-ev.V_MORTISE_X_OFF:.1f} mm (Slotted-In Inverted-V Stand Tenon & Mortise + SuperMini)"
    ))

    # Model 6 ("Aura-S" — Award-Edition Horizon Stadium Monolith for 20x20 mm HLK-LD2410S) sections
    as_base, as_lid, as_stand, dm6 = (
        ev.make_aura_s_base(),
        ev.make_aura_s_lid(),
        ev.make_aura_s_stand(),
        ev.make_aura_s_dummies(),
    )
    shapes6: dict[str, cq.Workplane] = {"aura_s_base": as_base, "aura_s_lid": as_lid, "aura_s_stand": as_stand, **dm6}
    plot(out_dir, shapes6, SectionSpec(
        "aura_s_front_xy", (0.0, 0.0, z_v_stand), (0, 0, 1), (0, 1),
        f"Aura-S XY section at Z={z_v_stand:.1f} mm (20x20 mm HLK-LD2410S Stadium Monolith + Rear 13.4 mm USB-C + V-Pedestal)"
    ))
    plot(out_dir, shapes6, SectionSpec(
        "aura_s_center_xz", (0.0, ev.Y_C, 0.0), (0, 1, 0), (0, 2),
        "Aura-S XZ section at Y=0.0 mm (20x20 mm HLK-LD2410S + SuperMini + Hidden Rear Z=0 13.4 mm USB-C Socket)"
    ))
    plot(out_dir, shapes6, SectionSpec(
        "aura_s_stand_yz", (-ev.V_MORTISE_X_OFF, 0.0, 0.0), (1, 0, 0), (1, 2),
        f"Aura-S YZ section at X={-ev.V_MORTISE_X_OFF:.1f} mm (34.0 mm Stadium Bevel, Horizon Groove & Slotted V-Pedestal)"
    ))

    # Model 7 ("Aura-C" — Award-Edition Horizon Stadium Monolith for 22x16 mm HLK-LD2410C) sections
    ac_base, ac_lid, ac_stand, dm7 = (
        ev.make_aura_c_base(),
        ev.make_aura_c_lid(),
        ev.make_aura_c_stand(),
        ev.make_aura_c_dummies(),
    )
    shapes7: dict[str, cq.Workplane] = {"aura_c_base": ac_base, "aura_c_lid": ac_lid, "aura_c_stand": ac_stand, **dm7}
    plot(out_dir, shapes7, SectionSpec(
        "aura_c_front_xy", (0.0, 0.0, z_v_stand), (0, 0, 1), (0, 1),
        f"Aura-C XY section at Z={z_v_stand:.1f} mm (22x16 mm HLK-LD2410C Stadium Monolith + Rear 13.4 mm USB-C + V-Pedestal)"
    ))
    plot(out_dir, shapes7, SectionSpec(
        "aura_c_center_xz", (0.0, ev.Y_C, 0.0), (0, 1, 0), (0, 2),
        "Aura-C XZ section at Y=0.0 mm (22x16 mm HLK-LD2410C + SuperMini + Hidden Rear Z=0 13.4 mm USB-C Socket)"
    ))
    plot(out_dir, shapes7, SectionSpec(
        "aura_c_stand_yz", (-ev.V_MORTISE_X_OFF, 0.0, 0.0), (1, 0, 0), (1, 2),
        f"Aura-C YZ section at X={-ev.V_MORTISE_X_OFF:.1f} mm (32.0 mm Stadium Bevel, Horizon Groove & Slotted V-Pedestal)"
    ))

    # Model 8 ("Aura-S v2" / "aura_v2") & Model 9 ("Aura-C v2") Compact Stacked Direct-Solder Monoliths
    as2_base, as2_lid, as2_stand, dm8 = (
        ev.make_aura_s_v2_base(),
        ev.make_aura_s_v2_lid(),
        ev.make_aura_s_v2_stand(),
        ev.make_aura_s_v2_dummies(),
    )
    shapes8: dict[str, cq.Workplane] = {
        "aura_s_v2_base": as2_base, "aura_s_v2_lid": as2_lid, "aura_s_v2_stand": as2_stand, **dm8
    }
    z_v2_stand = ev.V_MORTISE_V2_Z0 + ev.V_MORTISE_V2_L_Z / 2
    plot(out_dir, shapes8, SectionSpec(
        "aura_v2_front_xy", (0.0, 0.0, z_v2_stand), (0, 0, 1), (0, 1),
        f"Aura-S v2 XY section at Z={z_v2_stand:.1f} mm (64x34 mm Compact Stacked Stadium + Rear USB-C + V-Pedestal)"
    ))
    plot(out_dir, shapes8, SectionSpec(
        "aura_v2_center_xz", (0.0, ev.Y_C, 0.0), (0, 1, 0), (0, 2),
        "Aura-S v2 XZ section at Y=0.0 mm (20x20 mm HLK-LD2410S Stacked Over SuperMini + Rear Z=0 USB-C)"
    ))
    plot(out_dir, shapes8, SectionSpec(
        "aura_v2_stack_yz", (ev.RADAR_AURA_V2_X, 0.0, 0.0), (1, 0, 0), (1, 2),
        f"Aura-S v2 YZ section at X={ev.RADAR_AURA_V2_X:.1f} mm (Stepped Amphitheater Stack: SuperMini Z=5.4 + LD2410S Z=15.9)"
    ))

    ac2_base, ac2_lid, ac2_stand, dm9 = (
        ev.make_aura_c_v2_base(),
        ev.make_aura_c_v2_lid(),
        ev.make_aura_c_v2_stand(),
        ev.make_aura_c_v2_dummies(),
    )
    shapes9: dict[str, cq.Workplane] = {
        "aura_c_v2_base": ac2_base, "aura_c_v2_lid": ac2_lid, "aura_c_v2_stand": ac2_stand, **dm9
    }
    plot(out_dir, shapes9, SectionSpec(
        "aura_c_v2_center_xz", (0.0, ev.Y_C, 0.0), (0, 1, 0), (0, 2),
        "Aura-C v2 XZ section at Y=0.0 mm (22x16 mm HLK-LD2410C Stacked Over SuperMini + Rear Z=0 USB-C)"
    ))
    plot(out_dir, shapes9, SectionSpec(
        "aura_c_v2_stack_yz", (ev.RADAR_AURA_V2_X, 0.0, 0.0), (1, 0, 0), (1, 2),
        f"Aura-C v2 YZ section at X={ev.RADAR_AURA_V2_X:.1f} mm (Corbelled Stack: SuperMini Z=5.4 + LD2410C Z=15.9)"
    ))

    # USB-C Socket 4-Way Fit-Test Gauge section (combines Z=12.5 mm slot plane + Z=2.7 mm embossed text plane)
    usbc_test = ev.make_usbc_socket_fit_test()
    usbc_test_labels = usbc_test.translate((0.0, 0.0, ev.USBC_SOCK_Z - (e.FLOOR + 0.3)))
    plot(out_dir, {"usbc_socket_fit_test": usbc_test, "fit_test_labels": usbc_test_labels}, SectionSpec(
        "usbc_socket_fit_test_z", (0.0, 0.0, ev.USBC_SOCK_Z), (0, 0, 1), (0, 1),
        f"Fit-Test XY section at Z={ev.USBC_SOCK_Z:.1f} mm (+0.5, +1.0, +1.5, +2.0 mm Wider USB-C Slots + Front Apron Text)"
    ))

    print(f"34 sections written to {out_dir}")


if __name__ == "__main__":
    main()
