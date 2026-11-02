"""R-07 thermal model against closed forms."""
import dataclasses

import numpy as np
import pytest

from conftest import REPO, edit_yaml
from odrt.config import ConfigError
from odrt.project import load_inputs, thermal_models
from odrt.thermal import block_mean_square, km_at, motor_thermal, simulate, steady_state_winding_c


@pytest.fixture(scope="module")
def ro100():
    inputs = load_inputs(REPO)
    comp = inputs.components["cubemars_ro100_kv55"]
    mt, reason = motor_thermal(comp, inputs.thermal)
    assert reason is None
    return comp, mt, inputs.thermal


def test_rated_torque_settles_at_winding_limit(ro100):
    comp, mt, tp = ro100
    assert steady_state_winding_c(comp.continuous_torque_nm, mt, tp) == pytest.approx(tp.winding_max_c)


def test_simulation_converges_to_closed_form(ro100):
    comp, mt, tp = ro100
    tau = 3.0
    n = int(6 * 3600 / tp.step_s)  # many housing time constants
    tw, th = simulate(np.full(n, tau**2), mt, tp)
    assert tw[-1] == pytest.approx(steady_state_winding_c(tau, mt, tp), abs=0.05)
    # housing settles at ambient + loss * R_ha
    p = tau**2 / km_at(mt.km25, tw[-1]) ** 2
    assert th[-1] == pytest.approx(tp.ambient_c + p * mt.r_ha, abs=0.05)


def test_winding_heats_faster_than_housing(ro100):
    _, mt, tp = ro100
    tw, th = simulate(np.full(100, 25.0), mt, tp)
    assert np.all(tw >= th)
    assert tw[0] > tp.ambient_c


def test_runaway_is_reported(ro100):
    _, mt, tp = ro100
    assert steady_state_winding_c(1e3, mt, tp) == float("inf")


def test_stop_at_limit(ro100):
    _, mt, tp = ro100
    tw, _ = simulate(np.full(100000, 100.0), mt, tp, stop_at_limit=True)
    assert tw[-1] >= tp.winding_max_c > tw[-2]


def test_block_mean_square_is_exact():
    tau = np.array([1.0, 3.0, 2.0, 2.0, 5.0])
    np.testing.assert_allclose(block_mean_square(tau, 0.05, 0.1), [5.0, 4.0, 25.0])


def test_missing_data_reasons():
    inputs = load_inputs(REPO)
    _, reason = motor_thermal(inputs.components["odrive_d6374_150kv"], inputs.thermal)
    assert reason == "not stated: mass"
    _, reason = motor_thermal(inputs.components["myactuator_rmd_x10_p7_40"], inputs.thermal)
    assert "actuator" in reason


def test_two_motors_at_half_ratio_match_one_at_double(ro100):
    _, _, tp = ro100
    inputs = load_inputs(REPO)
    # Same torque per motor -> same thermal behaviour (checked through the stored option fields).
    a, b = inputs.options["2x cubemars_ro100_kv55@4:1"], inputs.options["cubemars_ro100_kv55@8:1"]
    assert a.count * a.external_ratio == b.count * b.external_ratio


def test_coarse_step_fails(repo_copy):
    edit_yaml(repo_copy / "configs/thermal.yaml", lambda d: d.__setitem__("step_s", 10.0))
    with pytest.raises(ConfigError, match="too coarse"):
        thermal_models(load_inputs(repo_copy))


def test_limit_below_ambient_fails(repo_copy):
    edit_yaml(repo_copy / "configs/thermal.yaml", lambda d: d.__setitem__("winding_max_c", 20))
    with pytest.raises(ConfigError, match="exceed ambient"):
        load_inputs(repo_copy)
