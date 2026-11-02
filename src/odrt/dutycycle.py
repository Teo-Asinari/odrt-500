"""Duty-cycle metrics for a trajectory: the quantities later electrical and
thermal models (R-06, R-07) will need. Pure kinematics x setpoint; no actuator."""
from __future__ import annotations

import numpy as np

from odrt.scenarios import Defaults, Trajectory
from odrt.units import lbf_to_n, n_to_lbf


def _integrate(y: np.ndarray, dt: float) -> float:
    """Trapezoidal integral on a uniform grid."""
    if len(y) < 2:
        return 0.0
    return float(dt * (np.sum(y) - 0.5 * (y[0] + y[-1])))


def _longest_run_s(mask: np.ndarray, dt: float) -> float:
    if not mask.any():
        return 0.0
    padded = np.concatenate(([0], mask.astype(np.int8), [0]))
    edges = np.flatnonzero(np.diff(padded))
    return float(np.max(edges[1::2] - edges[0::2]) * dt)


def metrics(traj: Trajectory, defaults: Defaults) -> dict:
    dt = traj.dt
    p = traj.power_w
    f = traj.tension_n
    duration = float(traj.t[-1] - traj.t[0])
    under_tension = f > lbf_to_n(defaults.tut_threshold_lbf)
    peak_f = float(np.max(f))
    near_peak = f >= 0.95 * peak_f if peak_f > 0 else np.zeros_like(f, dtype=bool)
    absorbed = _integrate(np.clip(p, 0, None), dt)
    returned = _integrate(np.clip(-p, 0, None), dt)
    rms_f = float(np.sqrt(_integrate(f**2, dt) / duration))
    return {
        "duration_s": duration,
        "max_extension_m": float(np.max(traj.x)),
        "peak_tension_n": peak_f,
        "peak_tension_lbf": float(n_to_lbf(peak_f)),
        "rms_tension_n": rms_f,
        "rms_tension_lbf": float(n_to_lbf(rms_f)),
        "peak_extension_speed_m_s": float(max(np.max(traj.v), 0.0)),
        "peak_retraction_speed_m_s": float(max(-np.min(traj.v), 0.0)),
        "peak_abs_accel_m_s2": float(np.max(np.abs(traj.a))),
        "peak_power_absorbed_w": float(max(np.max(p), 0.0)),
        "peak_power_returned_w": float(max(-np.min(p), 0.0)),
        "energy_absorbed_j": absorbed,
        "energy_returned_j": returned,
        "net_energy_absorbed_j": absorbed - returned,
        "mean_abs_power_w": (absorbed + returned) / duration,
        "time_under_tension_s": float(np.count_nonzero(under_tension) * dt),
        "tut_fraction": float(np.count_nonzero(under_tension) / len(f)),
        "longest_continuous_tut_s": _longest_run_s(under_tension, dt),
        "longest_near_peak_tension_s": _longest_run_s(near_peak, dt),
    }
