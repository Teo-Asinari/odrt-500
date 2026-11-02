"""WP2 drivetrain baseline against hand calculations and energy conservation."""
import dataclasses

import numpy as np
import pytest

from conftest import REPO, edit_yaml
from odrt.config import ConfigError
from odrt.drivetrain import (Architecture, Common, Drum, buffer_energy_j, drive_metrics, km_hot,
                             solve, worst_window_mean)
from odrt.project import load_inputs
from odrt.scenarios import Defaults, Scenario, Trajectory, generate
from odrt.units import lbf_to_n

COMMON = Common(cable_diameter_m=0.004, dead_turns=3, winding_temp_c=25, thermal_window_s=60)
ARCH = Architecture(name="t", description="test", gear_ratio=5, gear_efficiency=0.9,
                    drum_core_radius_m=0.02, turns_per_layer=20, max_layers=1, drum_inertia_kg_m2=0.0,
                    motor_rotor_inertia_kg_m2=0.0, motor_km_nm_per_sqrt_w=0.5)
STROKE = 2.0


def _const(n=1001, v=0.0, a=0.0, f=1000.0, x=0.5):
    t = np.arange(n) / 1000.0
    full = np.full(n, 1.0)
    return Trajectory(t=t, x=x * full, v=v * full, a=a * full, tension_n=f * full,
                      phase=np.zeros(n, dtype=np.int8))


R0 = 0.02 + 0.002  # core + half the cable diameter


def test_extension_motor_torque_is_reduced_by_gear_loss():
    sig = solve(_const(v=0.5), ARCH, COMMON, STROKE)
    np.testing.assert_allclose(sig.motor_torque_nm, 1000 * R0 * 0.9 / 5)
    np.testing.assert_allclose(sig.motor_speed_rad_s, 5 * 0.5 / R0)


def test_retraction_motor_torque_is_increased_by_gear_loss():
    sig = solve(_const(v=-0.5), ARCH, COMMON, STROKE)
    np.testing.assert_allclose(sig.motor_torque_nm, 1000 * R0 / (5 * 0.9))


def test_holding_copper_loss_hand_calc():
    sig = solve(_const(v=0.0), ARCH, COMMON, STROKE)
    tau = 1000 * R0 / (5 * 0.9)
    np.testing.assert_allclose(sig.copper_w, (tau / 0.5) ** 2)
    np.testing.assert_allclose(sig.bus_w, sig.copper_w)  # no motion: all bus power is copper loss


def test_brief_drum_torque_example():
    # DESIGN.md section 5: 500 lbf at r_eff = 0.020 m -> ~44.5 N*m at the drum.
    arch = dataclasses.replace(ARCH, drum_core_radius_m=0.018)  # centreline radius 0.020 m
    sig = solve(_const(f=lbf_to_n(500)), arch, COMMON, STROKE)
    assert sig.drum_torque_nm[0] == pytest.approx(44.5, abs=0.05)


def test_km_derates_with_temperature():
    hot = dataclasses.replace(COMMON, winding_temp_c=125)
    assert km_hot(ARCH, hot) == pytest.approx(0.5 / np.sqrt(1 + 0.00393 * 100))
    assert km_hot(ARCH, COMMON) == pytest.approx(0.5)


def test_inertia_reduces_motor_torque_when_cable_accelerates_out():
    arch = dataclasses.replace(ARCH, motor_rotor_inertia_kg_m2=1e-4, gear_efficiency=1.0)
    j = arch.inertia_at_drum()
    assert j == pytest.approx(25 * 1e-4)
    sig = solve(_const(v=0.0, a=2.0), arch, COMMON, STROKE)
    np.testing.assert_allclose(sig.motor_torque_nm, (1000 * R0 - j * 2.0 / R0) / 5)


def test_energy_is_conserved_over_a_scenario():
    defaults = Defaults(sample_rate_hz=2000, tension_ramp_s=0.2, rest_tension_lbf=5, tut_threshold_lbf=6)
    s = Scenario(name="e", description="d", kind="limit", requirements=("R-01",), assumptions=("A-001",),
                 start_offset_m=0.2, stroke_m=0.8, extend_s=1.0, top_hold_s=0.5, retract_s=1.5,
                 bottom_hold_s=0.5, reps=3, sets=1, rest_s=0, extension_tension_lbf=300,
                 retraction_tension_lbf=200)
    traj = generate(s, defaults)
    arch = dataclasses.replace(ARCH, motor_rotor_inertia_kg_m2=1e-4, drum_inertia_kg_m2=1e-3)
    sig = solve(traj, arch, COMMON, STROKE)
    m = drive_metrics(traj, sig, arch, COMMON)
    dt = traj.dt
    cable_in = np.sum(traj.tension_n * traj.v) * dt
    # Gear losses are never negative, in either power-flow direction.
    assert sig.gear_loss_w.min() >= -1e-9
    # Bus = copper - (cable work - gear loss - change in kinetic energy); KE starts and ends at 0.
    expected_bus = (np.sum(sig.copper_w) * dt - cable_in + np.sum(sig.gear_loss_w) * dt)
    assert m["net_bus_energy_kj"] * 1e3 == pytest.approx(expected_bus, rel=1e-3, abs=1.0)
    assert m["net_bus_energy_kj"] > 0  # losses mean the supply always nets positive here


def test_multilayer_radius_steps_down_as_cable_pays_out():
    arch = dataclasses.replace(ARCH, drum_core_radius_m=0.015, turns_per_layer=10, max_layers=3)
    drum = Drum(arch, COMMON)
    np.testing.assert_allclose(drum.radii, [0.017, 0.021, 0.025])
    r = drum.radius(np.array([0.0, STROKE]), STROKE)
    assert r[0] > r[1]
    assert r[1] == pytest.approx(0.017)
    assert np.all(np.diff(drum.radius(np.linspace(0, STROKE, 500), STROKE)) <= 0)


def test_single_layer_drum_has_constant_radius():
    r = Drum(ARCH, COMMON).radius(np.linspace(0, STROKE, 100), STROKE)
    np.testing.assert_allclose(r, R0)


def test_worst_window_and_buffer():
    y = np.concatenate([np.zeros(1000), np.full(500, 10.0), np.zeros(1000)])
    assert worst_window_mean(y, 0.001, 0.5) == pytest.approx(10.0)
    assert worst_window_mean(y, 0.001, 1.0) == pytest.approx(5.0)
    # +1 kW for 1 s then -1 kW for 1 s: mean 0, buffer must hold 1 kJ.
    bus = np.concatenate([np.full(1000, 1000.0), np.full(1000, -1000.0)])
    assert buffer_energy_j(bus, 0.001) == pytest.approx(1000.0, rel=1e-3)


def test_shipped_architectures_load():
    inputs = load_inputs(REPO)
    assert set(inputs.architectures) == {"A_direct_drive", "B_quasi_direct", "C_high_reduction"}


@pytest.mark.parametrize("mutate, message", [
    (lambda a: a.__setitem__("gear_efficiency", 1.2), "<= 1"),
    (lambda a: a.__setitem__("gear_ratio", 0), "> 0"),
    (lambda a: a.__setitem__("turns_per_layer", 5), "drum holds"),
    (lambda a: a.__setitem__("motor_km", 1), "unknown keys"),
])
def test_invalid_architectures_fail(repo_copy, mutate, message):
    edit_yaml(repo_copy / "configs/architectures.yaml",
              lambda d: mutate(d["architectures"]["A_direct_drive"]))
    with pytest.raises(ConfigError, match=message):
        load_inputs(repo_copy)
