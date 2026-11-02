"""WP2 analytical baseline: map a cable duty cycle to drum and motor demands.

Rigid, lumped model (A-009). Sign conventions:
- Cable payout (extension) is the positive direction for x, v, drum angle.
- tau_m is the motor torque resisting payout (>= 0 while holding tension).
- Shaft power into the motor is tau_m * omega_m: > 0 means the motor is generating.
- Bus power P_bus = P_copper - tau_m * omega_m: > 0 draws from the supply,
  < 0 is regenerated energy the electronics must store, return or dump (R-06).
Drive, PSU and iron losses are neglected (A-010).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from odrt.config import ConfigError, check_keys, integer, load_yaml, number, string
from odrt.scenarios import Trajectory

COPPER_TEMPCO_PER_K = 0.00393  # resistance temperature coefficient of copper
RPM_PER_RAD_S = 60 / (2 * np.pi)


@dataclass(frozen=True)
class Common:
    cable_diameter_m: float
    dead_turns: int
    winding_temp_c: float
    thermal_window_s: float


@dataclass(frozen=True)
class Architecture:
    name: str
    description: str
    gear_ratio: float
    gear_efficiency: float
    drum_core_radius_m: float
    turns_per_layer: int
    max_layers: int
    drum_inertia_kg_m2: float
    motor_rotor_inertia_kg_m2: float
    motor_km_nm_per_sqrt_w: float

    def inertia_at_drum(self) -> float:
        return self.drum_inertia_kg_m2 + self.gear_ratio**2 * self.motor_rotor_inertia_kg_m2


_ARCH_KEYS = ["description", "gear_ratio", "gear_efficiency", "drum_core_radius_m", "turns_per_layer",
              "max_layers", "drum_inertia_kg_m2", "motor_rotor_inertia_kg_m2", "motor_km_nm_per_sqrt_w"]


def load_architectures(path: Path, max_stroke_m: float):
    """Returns (Common, {name: Architecture}); checks each drum can hold the full stroke."""
    data = load_yaml(path)
    check_keys(data, str(path), ["common", "architectures"])
    c = data["common"]
    where = f"{path}: common"
    check_keys(c, where, ["cable_diameter_m", "dead_turns", "winding_temp_c", "thermal_window_s"])
    common = Common(
        number(c["cable_diameter_m"], f"{where}.cable_diameter_m", minimum=0, exclusive_minimum=True),
        integer(c["dead_turns"], f"{where}.dead_turns", minimum=0),
        number(c["winding_temp_c"], f"{where}.winding_temp_c", minimum=-40, maximum=200),
        number(c["thermal_window_s"], f"{where}.thermal_window_s", minimum=0, exclusive_minimum=True),
    )
    if not isinstance(data["architectures"], dict) or not data["architectures"]:
        raise ConfigError(f"{path}: 'architectures' must be a non-empty mapping")
    archs = {}
    for name, raw in data["architectures"].items():
        w = f"{path}: architectures.{name}"
        check_keys(raw, w, _ARCH_KEYS)

        def pos(key):
            return number(raw[key], f"{w}.{key}", minimum=0, exclusive_minimum=True)

        arch = Architecture(
            name=str(name), description=string(raw["description"], f"{w}.description"),
            gear_ratio=pos("gear_ratio"),
            gear_efficiency=number(raw["gear_efficiency"], f"{w}.gear_efficiency", minimum=0,
                                   exclusive_minimum=True, maximum=1),
            drum_core_radius_m=pos("drum_core_radius_m"),
            turns_per_layer=integer(raw["turns_per_layer"], f"{w}.turns_per_layer", minimum=1),
            max_layers=integer(raw["max_layers"], f"{w}.max_layers", minimum=1),
            drum_inertia_kg_m2=number(raw["drum_inertia_kg_m2"], f"{w}.drum_inertia_kg_m2", minimum=0),
            motor_rotor_inertia_kg_m2=number(raw["motor_rotor_inertia_kg_m2"],
                                             f"{w}.motor_rotor_inertia_kg_m2", minimum=0),
            motor_km_nm_per_sqrt_w=pos("motor_km_nm_per_sqrt_w"),
        )
        Drum(arch, common).check_capacity(max_stroke_m, w)
        archs[arch.name] = arch
    return common, archs


class Drum:
    """Layered winding: layer k centreline radius r_k = r_core + d/2 + k*d (A-011).

    The cable leaves from the outermost occupied layer, so the effective radius
    falls in steps as cable pays out.
    """

    def __init__(self, arch: Architecture, common: Common):
        d = common.cable_diameter_m
        self.radii = arch.drum_core_radius_m + d / 2 + d * np.arange(arch.max_layers)
        self.capacity = np.cumsum(arch.turns_per_layer * 2 * np.pi * self.radii)
        self.dead_length_m = common.dead_turns * 2 * np.pi * self.radii[0]
        self.width_m = arch.turns_per_layer * d

    def check_capacity(self, max_stroke_m: float, where: str) -> None:
        need = max_stroke_m + self.dead_length_m
        if need > self.capacity[-1] + 1e-12:
            raise ConfigError(f"{where}: drum holds {self.capacity[-1]:.3f} m but needs {need:.3f} m "
                              f"(max stroke + dead turns)")

    def radius(self, cable_out_m, max_stroke_m: float):
        """Effective radius for cable paid out x (0 = fully wound to max stroke)."""
        wound = max_stroke_m + self.dead_length_m - np.asarray(cable_out_m)
        layer = np.searchsorted(self.capacity, wound - 1e-12, side="left")
        return self.radii[np.clip(layer, 0, len(self.radii) - 1)]


@dataclass(frozen=True)
class DriveSignals:
    radius_m: np.ndarray
    drum_torque_nm: np.ndarray     # net torque the drivetrain must react at the drum
    motor_torque_nm: np.ndarray
    motor_speed_rad_s: np.ndarray
    copper_w: np.ndarray
    bus_w: np.ndarray
    gear_loss_w: np.ndarray


def km_hot(arch: Architecture, common: Common) -> float:
    """Motor constant at winding temperature: R rises with T, Km falls as 1/sqrt(R)."""
    return arch.motor_km_nm_per_sqrt_w / np.sqrt(1 + COPPER_TEMPCO_PER_K * (common.winding_temp_c - 25))


def solve(traj: Trajectory, arch: Architecture, common: Common, max_stroke_m: float) -> DriveSignals:
    r = Drum(arch, common).radius(traj.x, max_stroke_m)
    g, eta = arch.gear_ratio, arch.gear_efficiency
    omega_d = traj.v / r
    alpha_d = traj.a / r  # dr/dt term neglected (A-009)
    # Rigid drum: J_eq * alpha = F r - (torque from drivetrain). The drivetrain
    # supplies whatever torque makes the cable carry the commanded tension.
    tau_d = traj.tension_n * r - arch.inertia_at_drum() * alpha_d
    p_drum = tau_d * omega_d  # power flowing from drum into the gearbox
    tau_m = np.where(p_drum > 0, tau_d * eta / g, tau_d / (g * eta))
    omega_m = g * omega_d
    copper = (tau_m / km_hot(arch, common)) ** 2
    shaft_in = tau_m * omega_m
    return DriveSignals(radius_m=r, drum_torque_nm=tau_d, motor_torque_nm=tau_m, motor_speed_rad_s=omega_m,
                        copper_w=copper, bus_w=copper - shaft_in, gear_loss_w=p_drum - shaft_in)


def _integrate(y, dt):
    return float(dt * (np.sum(y) - 0.5 * (y[0] + y[-1]))) if len(y) > 1 else 0.0


def worst_window_mean(y: np.ndarray, dt: float, window_s: float) -> float:
    """Largest moving-window mean of y; whole-record mean if the record is shorter."""
    n = max(1, int(round(window_s / dt)))
    if n >= len(y):
        return float(np.mean(y))
    c = np.concatenate(([0.0], np.cumsum(y, dtype=np.float64)))
    return float(np.max((c[n:] - c[:-n]) / n))


def buffer_energy_j(bus_w: np.ndarray, dt: float) -> float:
    """Energy storage needed if the supply delivers only the session-mean bus power.

    The buffer absorbs regeneration and supplies peaks: its required size is the
    max-minus-min of the cumulative deviation from the mean (lossless, A-010).
    """
    deviation = np.cumsum(bus_w - np.mean(bus_w)) * dt
    return float(np.max(deviation) - np.min(deviation))


def drive_metrics(traj: Trajectory, sig: DriveSignals, arch: Architecture, common: Common) -> dict:
    dt = traj.dt
    duration = float(traj.t[-1] - traj.t[0])
    tau2 = sig.motor_torque_nm**2
    regen = np.clip(-sig.bus_w, 0, None)
    return {
        "radius_min_m": float(sig.radius_m.min()),
        "radius_max_m": float(sig.radius_m.max()),
        "effective_cable_mass_kg": float(arch.inertia_at_drum() / sig.radius_m.min() ** 2),
        "peak_drum_torque_nm": float(np.max(np.abs(sig.drum_torque_nm))),
        "peak_motor_torque_nm": float(np.max(np.abs(sig.motor_torque_nm))),
        "rms_motor_torque_nm": float(np.sqrt(_integrate(tau2, dt) / duration)),
        "worst_window_rms_motor_torque_nm": float(np.sqrt(worst_window_mean(tau2, dt, common.thermal_window_s))),
        "peak_motor_speed_rpm": float(np.max(np.abs(sig.motor_speed_rad_s)) * RPM_PER_RAD_S),
        "peak_copper_w": float(np.max(sig.copper_w)),
        "mean_copper_w": _integrate(sig.copper_w, dt) / duration,
        "worst_window_copper_w": worst_window_mean(sig.copper_w, dt, common.thermal_window_s),
        "copper_energy_kj": _integrate(sig.copper_w, dt) / 1e3,
        "gear_loss_energy_kj": _integrate(sig.gear_loss_w, dt) / 1e3,
        "peak_bus_draw_w": float(max(np.max(sig.bus_w), 0.0)),
        "peak_regen_w": float(np.max(regen)),
        "regen_energy_kj": _integrate(regen, dt) / 1e3,
        "net_bus_energy_kj": _integrate(sig.bus_w, dt) / 1e3,
        "mean_bus_w": _integrate(sig.bus_w, dt) / duration,
        "buffer_at_mean_draw_kj": buffer_energy_j(sig.bus_w, dt) / 1e3,
    }
