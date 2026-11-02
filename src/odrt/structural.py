"""WP4 first-pass analytical sizing (R-08). Hand-calculation level only.

Load path: cable tension at the drum -> drum shaft (bending + torsion) -> two
bearings -> side plates -> base plate -> anchor bolts. Belt wheels at each end
put their own pull on the shaft. All formulas are textbook beam/shaft relations;
none of this replaces FEA or review.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from odrt.config import ConfigError, check_keys, integer, load_yaml, number, string
from odrt.units import n_to_lbf


@dataclass(frozen=True)
class Material:
    name: str
    yield_mpa: float
    density_kg_m3: float


@dataclass(frozen=True)
class Structure:
    design: str
    stall_is_design_case: bool
    yield_sf: float
    cable_design_factor: float
    shaft: Material
    plate: Material
    pinion_teeth: int
    wheel_teeth: int
    belt_pitch_mm: float
    flange_extra_mm: float
    flange_thickness_mm: float
    span_extra_mm: float
    wheel_overhang_mm: float
    side_plate_mm: float
    base_plate_mm: float
    motor_offset_mm: float
    clearance_mm: float
    anchor_bolts: int
    bolt_spacing_mm: tuple


def _material(raw, where):
    check_keys(raw, where, ["name", "yield_mpa", "density_kg_m3"])
    return Material(string(raw["name"], f"{where}.name"),
                    number(raw["yield_mpa"], f"{where}.yield_mpa", minimum=0, exclusive_minimum=True),
                    number(raw["density_kg_m3"], f"{where}.density_kg_m3", minimum=0, exclusive_minimum=True))


def load_structure(path: Path, options: dict) -> Structure:
    d = load_yaml(path)
    w = str(path)
    check_keys(d, w, ["design", "loads", "materials", "layout"])
    if d["design"] not in options:
        raise ConfigError(f"{w}.design: unknown option {d['design']!r}")
    opt = options[d["design"]]
    lo, ma, la = d["loads"], d["materials"], d["layout"]
    check_keys(lo, f"{w}.loads", ["stall_is_design_case", "yield_safety_factor", "cable_design_factor"])
    check_keys(ma, f"{w}.materials", ["shaft", "plate"])
    check_keys(la, f"{w}.layout", ["belt_reduction", "drum_flange_extra_mm", "drum_flange_thickness_mm",
                                   "bearing_span_extra_mm", "wheel_overhang_mm", "side_plate_thickness_mm",
                                   "base_plate_thickness_mm", "motor_offset_mm", "clearance_mm", "anchor_bolts",
                                   "anchor_bolt_spacing_mm"])
    br = la["belt_reduction"]
    check_keys(br, f"{w}.layout.belt_reduction", ["pinion_teeth", "wheel_teeth", "pitch_mm"])
    pinion = integer(br["pinion_teeth"], f"{w}.layout.belt_reduction.pinion_teeth", minimum=8)
    wheel = integer(br["wheel_teeth"], f"{w}.layout.belt_reduction.wheel_teeth", minimum=pinion)
    if not math.isclose(wheel / pinion, opt.external_ratio, rel_tol=1e-9):
        raise ConfigError(f"{w}.layout.belt_reduction: {wheel}/{pinion} != design ratio {opt.external_ratio:g}")
    if not isinstance(lo["stall_is_design_case"], bool):
        raise ConfigError(f"{w}.loads.stall_is_design_case: expected true/false")
    spacing = la["anchor_bolt_spacing_mm"]
    if not (isinstance(spacing, list) and len(spacing) == 2):
        raise ConfigError(f"{w}.layout.anchor_bolt_spacing_mm: expected [x, y]")
    pos = dict(minimum=0, exclusive_minimum=True)
    return Structure(
        design=d["design"], stall_is_design_case=lo["stall_is_design_case"],
        yield_sf=number(lo["yield_safety_factor"], f"{w}.loads.yield_safety_factor", minimum=1),
        cable_design_factor=number(lo["cable_design_factor"], f"{w}.loads.cable_design_factor", minimum=1),
        shaft=_material(ma["shaft"], f"{w}.materials.shaft"), plate=_material(ma["plate"], f"{w}.materials.plate"),
        pinion_teeth=pinion, wheel_teeth=wheel,
        belt_pitch_mm=number(br["pitch_mm"], f"{w}.layout.belt_reduction.pitch_mm", **pos),
        flange_extra_mm=number(la["drum_flange_extra_mm"], f"{w}.layout.drum_flange_extra_mm", **pos),
        flange_thickness_mm=number(la["drum_flange_thickness_mm"], f"{w}.layout.drum_flange_thickness_mm", **pos),
        span_extra_mm=number(la["bearing_span_extra_mm"], f"{w}.layout.bearing_span_extra_mm", **pos),
        wheel_overhang_mm=number(la["wheel_overhang_mm"], f"{w}.layout.wheel_overhang_mm", **pos),
        side_plate_mm=number(la["side_plate_thickness_mm"], f"{w}.layout.side_plate_thickness_mm", **pos),
        base_plate_mm=number(la["base_plate_thickness_mm"], f"{w}.layout.base_plate_thickness_mm", **pos),
        motor_offset_mm=number(la["motor_offset_mm"], f"{w}.layout.motor_offset_mm", minimum=0),
        clearance_mm=number(la["clearance_mm"], f"{w}.layout.clearance_mm", minimum=0),
        anchor_bolts=integer(la["anchor_bolts"], f"{w}.layout.anchor_bolts", minimum=2),
        bolt_spacing_mm=tuple(number(v, f"{w}.layout.anchor_bolt_spacing_mm", **pos) for v in spacing),
    )


def pitch_diameter_mm(teeth: int, pitch_mm: float) -> float:
    return teeth * pitch_mm / math.pi


def sizing(st: Structure, opt, common, peak_tension_lbf: float) -> dict:
    """First-pass loads and minimum sizes. Units: N, m, N*m, MPa, mm in outputs where noted."""
    from odrt.drivetrain import Drum
    arch = opt.architecture
    drum = Drum(arch, common)
    r_cable = float(drum.radii[-1])
    comp = opt.component
    # Largest static cable tension the motors can produce (stall at peak torque).
    stall_drum_torque = opt.count * comp.peak_torque_nm * opt.external_ratio * opt.efficiency
    stall_tension = stall_drum_torque / float(drum.radii[0])
    nominal_tension = peak_tension_lbf * 4.4482216152605
    design_tension = stall_tension if st.stall_is_design_case else nominal_tension
    design_torque = design_tension * r_cable

    width = drum.width_m
    span = width + 2 * st.flange_thickness_mm / 1e3 + st.span_extra_mm / 1e3
    overhang = st.wheel_overhang_mm / 1e3
    wheel_r = pitch_diameter_mm(st.wheel_teeth, st.belt_pitch_mm) / 2e3
    # Each wheel carries half the drum torque. Belt pull ~ torque / radius, doubled for slack-side
    # pre-tension (rule of thumb, A-018), acting in the cable's direction (worst case: same direction).
    belt_pull_each = 2 * (design_torque / 2) / wheel_r
    # Simply supported shaft, cable load at mid-span, belt loads on overhangs at both ends.
    m_mid = design_tension * span / 4
    m_bearing = belt_pull_each * overhang
    m_max = max(m_mid, m_bearing)
    t_max = design_torque / 2  # torque in the shaft between a wheel and the drum
    allow = st.shaft.yield_mpa * 1e6 / st.yield_sf
    # von Mises for a solid round shaft: sigma = 32/(pi d^3) * sqrt(M^2 + 0.75 T^2)
    d_shaft = (32 * math.sqrt(m_max**2 + 0.75 * t_max**2) / (math.pi * allow)) ** (1 / 3)
    bearing_load = design_tension / 2 + belt_pull_each * (1 + overhang / span)
    total_reaction = design_tension + 2 * belt_pull_each  # into the frame, worst-case same direction
    sx, sy = (v / 1e3 for v in st.bolt_spacing_mm)
    # Cable pulls horizontally at drum height h above the base: tension + overturning moment on the bolts.
    h = 0.12
    bolt_tension = design_tension / st.anchor_bolts + design_tension * h / (sx * st.anchor_bolts / 2)
    return {
        "nominal_tension_lbf": n_to_lbf(nominal_tension),
        "stall_tension_lbf": n_to_lbf(stall_tension),
        "design_tension_lbf": n_to_lbf(design_tension),
        "design_drum_torque_nm": design_torque,
        "required_rope_breaking_kn": st.cable_design_factor * design_tension / 1e3,
        "drum_width_mm": width * 1e3,
        "bearing_span_mm": span * 1e3,
        "wheel_pitch_diameter_mm": wheel_r * 2e3,
        "pinion_pitch_diameter_mm": pitch_diameter_mm(st.pinion_teeth, st.belt_pitch_mm),
        "belt_pull_each_n": belt_pull_each,
        "shaft_moment_nm": m_max,
        "shaft_torque_nm": t_max,
        "min_shaft_diameter_mm": d_shaft * 1e3,
        "bearing_radial_load_n": bearing_load,
        "frame_reaction_n": total_reaction,
        "anchor_bolt_tension_n": bolt_tension,
        "observed_fault_peak_lbf": None,  # filled by the caller from the dynamics results
    }
