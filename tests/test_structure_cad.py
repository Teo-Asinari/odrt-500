"""WP4 structural sizing and (when CadQuery is installed) CAD generation."""
import math

import pytest

from conftest import REPO, edit_yaml
from odrt.config import ConfigError
from odrt.project import load_inputs
from odrt.structural import pitch_diameter_mm, sizing
from odrt.units import lbf_to_n


@pytest.fixture(scope="module")
def inputs():
    return load_inputs(REPO)


def test_stall_tension_hand_calc(inputs):
    st = inputs.structure
    opt = inputs.options[st.design]
    z = sizing(st, opt, inputs.common, 500)
    r0 = opt.architecture.drum_core_radius_m + inputs.common.cable_diameter_m / 2
    stall = opt.count * 12 * 6 * 0.95 / r0
    assert lbf_to_n(z["stall_tension_lbf"]) == pytest.approx(stall)
    assert z["design_tension_lbf"] == pytest.approx(z["stall_tension_lbf"])
    assert z["required_rope_breaking_kn"] == pytest.approx(5 * stall / 1e3)


def test_shaft_formula(inputs):
    st = inputs.structure
    z = sizing(st, inputs.options[st.design], inputs.common, 500)
    allow = st.shaft.yield_mpa * 1e6 / st.yield_sf
    stress = 32 * math.sqrt(z["shaft_moment_nm"] ** 2 + 0.75 * z["shaft_torque_nm"] ** 2) / (
        math.pi * (z["min_shaft_diameter_mm"] / 1e3) ** 3)
    assert stress == pytest.approx(allow, rel=1e-9)


def test_pitch_diameter():
    assert pitch_diameter_mm(90, 5) == pytest.approx(143.24, abs=0.01)


def test_belt_ratio_must_match_design(repo_copy):
    edit_yaml(repo_copy / "configs/structure.yaml",
              lambda d: d["layout"]["belt_reduction"].__setitem__("wheel_teeth", 80))
    with pytest.raises(ConfigError, match="design ratio"):
        load_inputs(repo_copy)


def test_cad_builds_without_interference(inputs):
    pytest.importorskip("cadquery")
    from odrt import cad
    from odrt.cli import structural_summary
    st = inputs.structure
    parts, geo = cad.build(st, inputs.options[st.design], inputs.common, structural_summary(inputs, {}))
    assert cad.interferences(parts) == []
    assert geo["shaft_diameter_mm"] >= structural_summary(inputs, {})["min_shaft_diameter_mm"]


def test_cad_detects_interference(inputs):
    pytest.importorskip("cadquery")
    import dataclasses
    from odrt import cad
    st = dataclasses.replace(inputs.structure, span_extra_mm=2.0,  # side plates pushed into the drum flanges
                             bolt_spacing_mm=(200.0, 200.0))
    opt = inputs.options[st.design]
    parts, _ = cad.build(st, opt, inputs.common, sizing(st, opt, inputs.common, 500))
    assert cad.interferences(parts)


def test_platform_stringer_hand_calc():
    from odrt.platform import PlatformCfg, evaluate  # noqa: F401
    inputs = load_inputs(REPO)
    cfg = inputs.platform
    z = evaluate(cfg, {}, (300.0, 300.0, 160.0), 72.0, 2500.0, 4000.0, 7.0)
    # fleet angle exactly at the limit by construction
    assert z["fleet_angle_deg"] == pytest.approx(cfg.max_fleet_deg)
    foot = (cfg.user_mass_kg * 9.80665 + 4000.0) / 2
    assert z["foot_load_n"] == pytest.approx(foot)
    L, a = z["platform_length_mm"] / 1e3, z["port_from_back_mm"] / 1e3
    bw, bh, t = (v / 1e3 for v in cfg.stringer_section_mm)
    i = (bw * bh**3 - (bw - 2 * t) * (bh - 2 * t) ** 3) / 12
    assert z["stringer_stress_mpa"] == pytest.approx(foot * a * (L - a) / L * (bh / 2) / i / 1e6)
    assert z["empty_platform_lift_off_lbf"] == pytest.approx((cfg.frame_mass_kg + 7.0) * 9.80665 / 4.4482216152605)
