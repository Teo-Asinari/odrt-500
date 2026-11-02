"""Dynamic model: physical sanity checks and fault behaviour."""
import dataclasses

import numpy as np
import pytest

from conftest import REPO, edit_yaml
from odrt.config import ConfigError
from odrt.dynamics import Case, Plant, run
from odrt.project import load_inputs
from odrt.scenarios import Trajectory
from odrt.units import lbf_to_n


@pytest.fixture(scope="module")
def setup():
    inputs = load_inputs(REPO)
    plant = Plant.from_option(inputs.options[inputs.dynamics.designs[0]], inputs.common)
    return inputs, plant


def _hold(f_n, seconds=2.0, x=0.5):
    t = np.arange(0, seconds + 1e-9, 0.001)
    one = np.ones_like(t)
    return Trajectory(t=t, x=x * one, v=0 * one, a=0 * one, tension_n=f_n * one, phase=np.zeros(len(t), np.int8))


def test_static_hold_converges_to_command(setup):
    inputs, plant = setup
    m = run(Case("hold", "x", 2.0, "none", 0.0, True), _hold(1000.0), plant, inputs.dynamics)["metrics"]
    assert m["tracking_rms_error_n"] < 15  # noise + friction only
    assert m["peak_tension_lbf"] == pytest.approx(1000 / 4.448, rel=0.05)


def test_cable_never_pushes(setup):
    inputs, plant = setup
    sig = run(Case("hold", "x", 1.0, "handle_release", 0.2, False), _hold(1000.0, 1.0), plant,
              inputs.dynamics)["signals"]
    assert sig["f"].min() >= 0.0


def test_open_power_loss_drops_tension(setup):
    inputs, plant = setup
    p = dataclasses.replace(inputs.dynamics, user_k=0.0, user_b=0.0)
    sig = run(Case("pl", "x", 2.0, "power_loss_open", 1.0, False), _hold(1000.0), plant, p)["signals"]
    # With no motor torque, the user's 1000 N only has to accelerate the drum and hand (plus friction).
    m_total = plant.m_eq_kg + p.user_mass_kg + p.handle_mass_kg
    expected_v = (1000 - p.friction_n) / m_total * 0.5
    v_at = sig["v_drum"][np.searchsorted(sig["t"], 1.5)]
    assert v_at == pytest.approx(expected_v, rel=0.1)


def test_shorted_braking_force_scales_with_speed(setup):
    _, plant = setup
    # F = n Km^2 (G/r)^2 v (at the drum, before efficiency)
    c = plant.count * plant.km_hot**2 * (plant.gear_ratio / plant.radius_m) ** 2
    assert c > 1e4  # strong enough to matter at walking speeds: > 10 kN per m/s


def test_bus_rises_without_dump_resistor(setup):
    inputs, plant = setup
    p = dataclasses.replace(inputs.dynamics, bus_c=0.002)  # plain bus capacitors, no buffer
    m_with = run(dataclasses.replace(inputs.dynamics.cases[-1]), _traj_pull(), plant, p)["metrics"]
    m_without = run(Case("nd", "x", 3.0, "no_dump_resistor", 0.0, True), _traj_pull(), plant, p)["metrics"]
    assert m_without["peak_bus_v"] > p.overvoltage_v
    assert m_with["peak_bus_v"] <= p.dump_on_v + 1.0


def test_buffer_absorbs_regeneration(setup):
    inputs, plant = setup
    m = run(Case("nd", "x", 3.0, "no_dump_resistor", 0.0, True), _traj_pull(), plant, inputs.dynamics)["metrics"]
    assert m["peak_bus_v"] < inputs.dynamics.overvoltage_v  # 2 F buffer holds a few reps of regen


def _traj_pull():
    inputs = load_inputs(REPO)
    from odrt.scenarios import generate
    return generate(inputs.scenarios["heavy_tempo_limit"], inputs.defaults)


def test_monitor_limits_stuck_load_cell(setup):
    inputs, plant = setup
    traj = _traj_pull()
    off = run(Case("a", "x", 3.5, "load_cell_zero", 2.6, False), traj, plant, inputs.dynamics)["metrics"]
    on = run(Case("b", "x", 3.5, "load_cell_zero", 2.6, True), traj, plant, inputs.dynamics)["metrics"]
    assert on["fell_back_to_feedforward"] and not off["fell_back_to_feedforward"]
    assert on["peak_tension_after_fault_lbf"] < off["peak_tension_after_fault_lbf"]


def test_speed_limiter_slows_drum_after_release(setup):
    inputs, plant = setup
    traj = _traj_pull()
    off = run(Case("a", "x", 4.0, "handle_release", 2.6, False), traj, plant, inputs.dynamics)["signals"]
    on = run(Case("b", "x", 4.0, "handle_release", 2.6, True), traj, plant, inputs.dynamics)["signals"]
    assert -on["v_drum"].min() < -off["v_drum"].min()


def test_released_handle_bounded_by_stored_cable_energy(setup):
    inputs, plant = setup
    p = inputs.dynamics
    f = lbf_to_n(500)
    k = p.ea_n / (p.routing_length_m + 0.8)
    v_max = np.sqrt(f**2 / k / p.handle_mass_kg)  # all elastic energy into the handle
    m = run(Case("r", "x", 4.0, "handle_release", 2.6, True), _traj_pull(), plant, p)["metrics"]
    assert 0.3 * v_max < m["handle_end_stop_speed_m_s"] < 1.2 * v_max


@pytest.mark.parametrize("mutate, message", [
    (lambda d: d.__setitem__("designs", ["nope"]), "unknown option"),
    (lambda d: d.__setitem__("designs", ["myactuator_rmd_x10_p7_40@7:1 (built-in)"]), "lacks motor data"),
    (lambda d: d["cases"][0].__setitem__("fault", "meteor"), "not in"),
    (lambda d: d["cases"][3].pop("fault_time_s"), "fault_time_s required"),
    (lambda d: d["bus"].__setitem__("dump_on_v", 70), "nominal_v < dump_on_v < overvoltage_v"),
    (lambda d: d["cases"][1].__setitem__("name", d["cases"][0]["name"]), "duplicate"),
])
def test_invalid_dynamics_config_fails(repo_copy, mutate, message):
    edit_yaml(repo_copy / "configs/dynamics.yaml", mutate)
    with pytest.raises(ConfigError, match=message):
        load_inputs(repo_copy)
