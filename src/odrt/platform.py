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
    sheave: dict
    bolts: dict


def load_platform(path: Path) -> PlatformCfg:
    d = load_yaml(path)
    w = str(path)
    check_keys(d, w, ["max_fleet_angle_deg", "sheave_radius_mm", "deck", "stringer", "sheave", "mechanism_bolts",
                      "design_user_mass_kg",
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
    sh, bo = d["sheave"], d["mechanism_bolts"]
    check_keys(sh, f"{w}.sheave", ["cheek_gap_mm", "cheek_thickness_mm", "edge_distance_mm", "bearing_static_factor"])
    check_keys(bo, f"{w}.mechanism_bolts", ["count", "tensile_area_mm2", "shear_allow_mpa"])
    return PlatformCfg(
        sheave={k: number(v, f"{w}.sheave.{k}", **pos) for k, v in sh.items()},
        bolts={k: number(v, f"{w}.mechanism_bolts.{k}", **pos) for k, v in bo.items()},
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
    # Sheave axle: pin between two cheeks, central load -> M = P L / 4; solid round, yield / 2.
    sh = cfg.sheave
    allow_steel = cfg.stringer.yield_mpa * 1e6 / 2.0
    m_axle = sheave_load * (sh["cheek_gap_mm"] / 1000) / 4
    d_axle = (32 * m_axle / (math.pi * allow_steel)) ** (1 / 3) * 1000
    d_axle_std = next(v for v in (8, 10, 12, 15, 17, 20, 25) if v >= d_axle)
    bearing_c0_n = sh["bearing_static_factor"] * sheave_load / 2
    cheek_bearing_mpa = sheave_load / 2 / (d_axle_std * sh["cheek_thickness_mm"])
    cheek_tearout_mpa = sheave_load / 2 / (2 * sh["edge_distance_mm"] * sh["cheek_thickness_mm"])
    # Cheeks reach forward from a cross-beam behind the sheave: cantilever arm ~ r + beam/2 + 5 mm,
    # section = cheek thickness x (beam depth + sheave radius), conservative.
    arm = (cfg.sheave_r_mm + cfg.stringer_section_mm[0] / 2 + 5) / 1000
    h_cheek = (cfg.stringer_section_mm[1] + cfg.sheave_r_mm) / 1000
    cheek_bending = (sheave_load / 2 * arm) / (sh["cheek_thickness_mm"] / 1000 * h_cheek**2 / 6)
    # Cross-beam between the stringers carrying the sheave: central point load over the stringer spacing.
    span_cb = 2 * cfg.stance_half_mm / 1000
    m_cb = sheave_load * span_cb / 4
    cb_stress = m_cb * (bh / 2) / i
    cb_defl = sheave_load * span_cb**3 / (48 * e * i)
    # Mechanism base bolts in shear: the drum pulls the mechanism toward the sheave with the snap tension.
    bo = cfg.bolts
    bolt_shear_mpa = snap_tension_n / bo["count"] / bo["tensile_area_mm2"]
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
        "sheave_d_over_rope": 2 * cfg.sheave_r_mm / 4.0,
        "axle_min_mm": d_axle, "axle_mm": d_axle_std, "sheave_bearing_c0_n": bearing_c0_n,
        "cheek_bearing_mpa": cheek_bearing_mpa, "cheek_tearout_mpa": cheek_tearout_mpa,
        "cheek_bending_mpa": cheek_bending / 1e6, "cheek_bending_ok": cheek_bending <= cfg.deck.yield_mpa * 1e6 / 2.0,
        "cross_beam_stress_mpa": cb_stress / 1e6, "cross_beam_stress_ok": cb_stress <= allow,
        "cross_beam_deflection_mm": cb_defl * 1e3, "bolt_shear_mpa": bolt_shear_mpa,
        "bolt_shear_ok": bolt_shear_mpa <= bo["shear_allow_mpa"],
        "snap_tension_lbf": n_to_lbf(snap_tension_n),
        "empty_platform_lift_off_lbf": n_to_lbf(empty_lift_off_n),
        "platform_mass_kg": cfg.frame_mass_kg + mech_mass_kg,
    }
