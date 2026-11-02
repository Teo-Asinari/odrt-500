"""Trajectory kinematics and duty-cycle energy accounting against closed forms."""
import dataclasses

import numpy as np
import pytest

from conftest import REPO
from odrt.config import ConfigError
from odrt.dutycycle import metrics
from odrt.project import load_inputs
from odrt.scenarios import (PHASE_EXTEND, PHASE_RETRACT, Defaults, Scenario, generate, min_jerk,
                            scenario_duration_s, settle_s)
from odrt.units import lbf_to_n

DEFAULTS = Defaults(sample_rate_hz=2000, tension_ramp_s=0.2, rest_tension_lbf=5, tut_threshold_lbf=6)
BASE = Scenario(name="t", description="test", kind="limit", requirements=("R-01",),
                assumptions=("A-001",), start_offset_m=0.3, stroke_m=0.6, extend_s=1.2,
                top_hold_s=0.5, retract_s=2.0, bottom_hold_s=0.5, reps=4, sets=2, rest_s=10,
                extension_tension_lbf=100, retraction_tension_lbf=100)


def test_min_jerk_boundaries_and_peaks():
    tau = np.linspace(0, 1, 100001)
    pos, vel, acc = min_jerk(tau)
    assert pos[0] == 0 and pos[-1] == pytest.approx(1)
    assert vel[0] == 0 and vel[-1] == pytest.approx(0, abs=1e-12)
    assert vel.max() == pytest.approx(1.875, rel=1e-6)
    assert np.abs(acc).max() == pytest.approx(10 / np.sqrt(3), rel=1e-6)
    # velocity is the derivative of position
    np.testing.assert_allclose(np.gradient(pos, tau), vel, atol=1e-6)


def test_trajectory_kinematics():
    traj = generate(BASE, DEFAULTS)
    lo, hi = BASE.start_offset_m, BASE.start_offset_m + BASE.stroke_m
    assert traj.t[-1] == pytest.approx(scenario_duration_s(BASE, DEFAULTS))
    assert traj.x.min() == pytest.approx(lo) and traj.x.max() == pytest.approx(hi)
    assert traj.x[0] == pytest.approx(lo) and traj.x[-1] == pytest.approx(lo)
    assert traj.v.max() == pytest.approx(1.875 * BASE.stroke_m / BASE.extend_s, rel=1e-4)
    assert -traj.v.min() == pytest.approx(1.875 * BASE.stroke_m / BASE.retract_s, rel=1e-4)
    # position is continuous and consistent with velocity
    np.testing.assert_allclose(np.gradient(traj.x, traj.dt), traj.v, atol=2e-3)
    assert np.all(traj.v[traj.phase == PHASE_EXTEND] >= 0)
    assert np.all(traj.v[traj.phase == PHASE_RETRACT] <= 0)


def test_tension_never_negative_and_ramped():
    traj = generate(BASE, DEFAULTS)
    assert traj.tension_n.min() >= 0
    max_step = np.max(np.abs(np.diff(traj.tension_n)))
    full_step = lbf_to_n(BASE.extension_tension_lbf - DEFAULTS.rest_tension_lbf)
    expected_step = full_step / (DEFAULTS.tension_ramp_s * DEFAULTS.sample_rate_hz)
    assert max_step == pytest.approx(expected_step, rel=1e-6)


def test_constant_tension_energy_matches_closed_form():
    traj = generate(BASE, DEFAULTS)
    m = metrics(traj, DEFAULTS)
    total_reps = BASE.reps * BASE.sets
    # Ramps finish inside holds, so tension is constant whenever the cable moves.
    expected = lbf_to_n(100) * BASE.stroke_m * total_reps
    assert m["energy_absorbed_j"] == pytest.approx(expected, rel=1e-4)
    assert m["energy_returned_j"] == pytest.approx(expected, rel=1e-4)
    assert m["net_energy_absorbed_j"] == pytest.approx(0, abs=expected * 1e-4)
    assert m["peak_power_absorbed_w"] == pytest.approx(lbf_to_n(100) * traj.v.max(), rel=1e-6)


def test_eccentric_overload_returns_more_energy():
    s = dataclasses.replace(BASE, retraction_tension_lbf=150)
    m = metrics(generate(s, DEFAULTS), DEFAULTS)
    n = s.reps * s.sets
    assert m["energy_absorbed_j"] == pytest.approx(lbf_to_n(100) * s.stroke_m * n, rel=1e-4)
    assert m["energy_returned_j"] == pytest.approx(lbf_to_n(150) * s.stroke_m * n, rel=1e-4)
    assert m["net_energy_absorbed_j"] < 0


def test_tension_constant_while_cable_moves():
    s = dataclasses.replace(BASE, retraction_tension_lbf=150)
    traj = generate(s, DEFAULTS)
    ext, ret = traj.phase == PHASE_EXTEND, traj.phase == PHASE_RETRACT
    np.testing.assert_allclose(traj.tension_n[ext], lbf_to_n(100), rtol=1e-12)
    np.testing.assert_allclose(traj.tension_n[ret], lbf_to_n(150), rtol=1e-12)


def test_time_under_tension():
    m = metrics(generate(BASE, DEFAULTS), DEFAULTS)
    ramp = DEFAULTS.tension_ramp_s
    # Each set: pre-load ramp up, the reps, then the ramp down at the start of the rest.
    per_set = BASE.reps * BASE.cycle_s() + 2 * ramp
    assert m["time_under_tension_s"] == pytest.approx(BASE.sets * per_set, abs=0.01 * BASE.sets)
    assert m["longest_continuous_tut_s"] == pytest.approx(per_set, abs=0.01)


def test_zero_length_holds_are_dropped():
    s = dataclasses.replace(BASE, top_hold_s=0, bottom_hold_s=0, sets=1)
    traj = generate(s, DEFAULTS)
    assert traj.t[-1] == pytest.approx(
        2 * settle_s(DEFAULTS) + DEFAULTS.tension_ramp_s + s.reps * (s.extend_s + s.retract_s))
    assert np.all(np.isfinite(traj.x)) and np.all(np.isfinite(traj.a))


@pytest.mark.parametrize("changes, message", [
    (dict(retraction_tension_lbf=150, top_hold_s=0), "top_hold lasts 0 s"),
    (dict(retraction_tension_lbf=150, top_hold_s=0.1), "needs tension_ramp_s"),
    (dict(retraction_tension_lbf=150, bottom_hold_s=0.05), "needs tension_ramp_s"),
    (dict(rest_s=0.1), "needs tension_ramp_s"),
])
def test_tension_change_without_room_to_ramp_fails(changes, message):
    with pytest.raises(ConfigError, match=message):
        generate(dataclasses.replace(BASE, **changes), DEFAULTS)


def test_rms_tension_constant_load():
    s = dataclasses.replace(BASE, sets=1, reps=50)
    m = metrics(generate(s, DEFAULTS), DEFAULTS)
    # Long session at constant tension: RMS approaches the setpoint from below.
    assert 0.95 * 100 < m["rms_tension_lbf"] <= 100


def test_all_shipped_scenarios_stay_in_envelope():
    inputs = load_inputs(REPO)
    for s in inputs.scenarios.values():
        m = metrics(generate(s, inputs.defaults), inputs.defaults)
        assert m["peak_tension_lbf"] <= inputs.envelope.peak_tension_lbf + 1e-9, s.name
        assert m["max_extension_m"] <= inputs.envelope.max_usable_stroke_m + 1e-9, s.name
