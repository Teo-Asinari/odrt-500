"""R-14 floor platform layout and first-pass checks (hand calculations, A-021).

Geometry: mechanism at the back of the platform, cable leaving the drum toward
the front, a turning sheave under the deck port, cable vertical through the port.
Load path: the cable pulls the port up while the user's feet push the deck down,
so pull loads close inside the platform and the floor carries only weights.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from odrt.config import ConfigError, check_keys, load_yaml, number
from odrt.structural import Material, _material
from odrt.units import n_to_lbf

G = 9.80665


@dataclass(frozen=True)
class PlatformCfg:
    max_fleet_deg: float
    sheave_r_mm: float
    deck: Material
    deck_t_mm: float
    deck_h_mm: float
    stance_half_mm: float
    foot_room_mm: float
    side_margin_mm: float
    back_margin_mm: float
    user_mass_kg: float
    frame_mass_kg: float
    deflection_limit_mm: float
    stringer: Material
    stringer_section_mm: tuple


def load_platform(path: Path) -> PlatformCfg:
    d = load_yaml(path)
    w = str(path)
    check_keys(d, w, ["max_fleet_angle_deg", "sheave_radius_mm", "deck", "stringer", "design_user_mass_kg",
                      "frame_mass_estimate_kg", "deflection_limit_mm"])
    dk = d["deck"]
    check_keys(dk, f"{w}.deck", ["material", "thickness_mm", "height_mm", "stance_half_width_mm", "foot_room_mm",
                                 "side_margin_mm", "back_margin_mm"])
    pos = dict(minimum=0, exclusive_minimum=True)
    sg = d["stringer"]
    check_keys(sg, f"{w}.stringer", ["material", "section_mm"])
    sec = sg["section_mm"]
    if not (isinstance(sec, list) and len(sec) == 3 and 2 * sec[2] < min(sec[0], sec[1])):
        raise ConfigError(f"{w}.stringer.section_mm: expected [width, height, wall] with wall < half the size")
    return PlatformCfg(
        stringer=_material(sg["material"], f"{w}.stringer.material"),
        stringer_section_mm=tuple(number(v, f"{w}.stringer.section_mm", **pos) for v in sec),
        max_fleet_deg=number(d["max_fleet_angle_deg"], f"{w}.max_fleet_angle_deg", minimum=0.5, maximum=15),
        sheave_r_mm=number(d["sheave_radius_mm"], f"{w}.sheave_radius_mm", **pos),
        deck=_material(dk["material"], f"{w}.deck.material"),
        deck_t_mm=number(dk["thickness_mm"], f"{w}.deck.thickness_mm", **pos),
        deck_h_mm=number(dk["height_mm"], f"{w}.deck.height_mm", **pos),
        stance_half_mm=number(dk["stance_half_width_mm"], f"{w}.deck.stance_half_width_mm", **pos),
        foot_room_mm=number(dk["foot_room_mm"], f"{w}.deck.foot_room_mm", **pos),
        side_margin_mm=number(dk["side_margin_mm"], f"{w}.deck.side_margin_mm", minimum=0),
        back_margin_mm=number(dk["back_margin_mm"], f"{w}.deck.back_margin_mm", minimum=0),
        user_mass_kg=number(d["design_user_mass_kg"], f"{w}.design_user_mass_kg", **pos),
        frame_mass_kg=number(d["frame_mass_estimate_kg"], f"{w}.frame_mass_estimate_kg", **pos),
        deflection_limit_mm=number(d["deflection_limit_mm"], f"{w}.deflection_limit_mm", **pos),
    )


def evaluate(cfg: PlatformCfg, lay: dict, mech_env_mm: tuple, drum_width_mm: float, design_tension_n: float,
             snap_tension_n: float, mech_mass_kg: float, mech_back_mm: float = None) -> dict:
    """Layout dimensions and pass/fail checks.

    mech_env_mm: (x, y, z) mechanism envelope; mech_back_mm: distance from the drum axis to the mechanism's
    rearmost point (defaults to half the envelope depth).
    """
    half_wrap = drum_width_mm / 2
    drum_to_sheave = half_wrap / math.tan(math.radians(cfg.max_fleet_deg))
    mech_x, mech_y, mech_z = mech_env_mm
    # rear end frame (one stringer-height deep), then back_margin, then the mechanism's rearmost point
    rear = mech_y / 2 if mech_back_mm is None else mech_back_mm
    back_to_drum = cfg.stringer_section_mm[1] + cfg.back_margin_mm + rear
    port_y = back_to_drum + drum_to_sheave
    length = port_y + cfg.foot_room_mm
    width = max(mech_x, 2 * (cfg.stance_half_mm + 70)) + 2 * cfg.side_margin_mm  # 70 mm ~ half a foot width
    height_needed = mech_z + cfg.deck_t_mm + 10
    # Each foot (user weight + snap tension, shared) stands over a stringer simply supported at the platform
    # ends; the foot sits at the port's position along the length.
    foot = (cfg.user_mass_kg * G + snap_tension_n) / 2
    span = length / 1000
    a_ = port_y / 1000
    b_ = span - a_
    bw, bh, wall = (v / 1000 for v in cfg.stringer_section_mm)
    i = (bw * bh**3 - (bw - 2 * wall) * (bh - 2 * wall) ** 3) / 12
    m = foot * a_ * b_ / span
    stress = m * (bh / 2) / i
    e = cfg.stringer.youngs_gpa * 1e9
    # max deflection of a simply supported beam under an off-centre point load
    short = min(a_, b_)
    defl = foot * short * (span**2 - short**2) ** 1.5 / (9 * math.sqrt(3) * span * e * i)
    allow = cfg.stringer.yield_mpa * 1e6 / 2.0
    sheave_load = math.sqrt(2) * snap_tension_n  # 90-degree wrap
    empty_lift_off_n = (cfg.frame_mass_kg + mech_mass_kg) * G
    return {
        "fleet_angle_deg": math.degrees(math.atan(half_wrap / drum_to_sheave)),
        "drum_to_sheave_mm": drum_to_sheave,
        "platform_length_mm": length, "platform_width_mm": width, "deck_height_mm": cfg.deck_h_mm,
        "deck_height_needed_mm": height_needed, "deck_height_ok": cfg.deck_h_mm >= height_needed,
        "port_from_back_mm": port_y,
        "foot_load_n": foot,
        "stringer_stress_mpa": stress / 1e6, "stringer_allow_mpa": allow / 1e6, "stringer_stress_ok": stress <= allow,
        "stringer_deflection_mm": defl * 1e3, "stringer_deflection_ok": defl * 1e3 <= cfg.deflection_limit_mm,
        "sheave_load_n": sheave_load, "design_tension_lbf": n_to_lbf(design_tension_n),
        "snap_tension_lbf": n_to_lbf(snap_tension_n),
        "empty_platform_lift_off_lbf": n_to_lbf(empty_lift_off_n),
        "platform_mass_kg": cfg.frame_mass_kg + mech_mass_kg,
    }
