"""R-07 first-order thermal model: two nodes per motor (winding, housing).

  C_w dT_w/dt = P_cu(T_w) - (T_w - T_h) / R_wh
  C_h dT_h/dt = (T_w - T_h) / R_wh - (T_h - T_a) / R_ha
  P_cu(T_w)   = tau^2 / Km(T_w)^2,  Km(T) = Km_25 / sqrt(1 + alpha (T - 25))

R_wh + R_ha is backed out so the motor's rated continuous torque settles exactly
at winding_max_c (A-015). Copper loss rises with temperature, so runaway is
possible and is reported rather than hidden.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

from odrt.config import ConfigError, check_keys, load_yaml, number
from odrt.drivetrain import COPPER_TEMPCO_PER_K


@dataclass(frozen=True)
class ThermalParams:
    ambient_c: float
    winding_max_c: float
    specific_heat_j_per_kg_k: float
    winding_capacity_fraction: float
    winding_resistance_fraction: float
    step_s: float
    peak_hold_cap_s: float


@dataclass(frozen=True)
class MotorThermal:
    km25: float
    r_wh: float   # K/W
    r_ha: float   # K/W
    c_w: float    # J/K
    c_h: float    # J/K

    @property
    def r_total(self) -> float:
        return self.r_wh + self.r_ha

    @property
    def winding_tau_s(self) -> float:
        return self.r_wh * self.c_w


def load_thermal(path: Path) -> ThermalParams:
    data = load_yaml(path)
    w = str(path)
    keys = ["ambient_c", "winding_max_c", "specific_heat_j_per_kg_k", "winding_capacity_fraction",
            "winding_resistance_fraction", "step_s", "peak_hold_cap_s"]
    check_keys(data, w, keys)
    p = ThermalParams(
        ambient_c=number(data["ambient_c"], f"{w}.ambient_c", minimum=-20, maximum=60),
        winding_max_c=number(data["winding_max_c"], f"{w}.winding_max_c", maximum=250),
        specific_heat_j_per_kg_k=number(data["specific_heat_j_per_kg_k"], f"{w}.specific_heat_j_per_kg_k",
                                        minimum=0, exclusive_minimum=True),
        winding_capacity_fraction=number(data["winding_capacity_fraction"], f"{w}.winding_capacity_fraction",
                                         minimum=0, exclusive_minimum=True, maximum=0.99),
        winding_resistance_fraction=number(data["winding_resistance_fraction"],
                                           f"{w}.winding_resistance_fraction", minimum=0,
                                           exclusive_minimum=True, maximum=0.99),
        step_s=number(data["step_s"], f"{w}.step_s", minimum=0, exclusive_minimum=True),
        peak_hold_cap_s=number(data["peak_hold_cap_s"], f"{w}.peak_hold_cap_s", minimum=0, exclusive_minimum=True),
    )
    if p.winding_max_c <= p.ambient_c:
        raise ConfigError(f"{w}: winding_max_c must exceed ambient_c")
    return p


def km_at(km25: float, temp_c):
    return km25 / np.sqrt(1 + COPPER_TEMPCO_PER_K * (np.asarray(temp_c) - 25))


def motor_thermal(component, params: ThermalParams):
    """(MotorThermal, None) or (None, reason) when the cited data is insufficient."""
    missing = [label for label, value in (("Km", component.km()), ("continuous torque",
               component.continuous_torque_nm), ("mass", component.mass_kg)) if value is None]
    if component.kind != "motor":
        return None, "actuator: no winding data"
    if missing:
        return None, "not stated: " + ", ".join(missing)
    km25 = component.km()
    p_rated = (component.continuous_torque_nm / km_at(km25, params.winding_max_c)) ** 2
    r_total = (params.winding_max_c - params.ambient_c) / float(p_rated)
    c_total = component.mass_kg * params.specific_heat_j_per_kg_k
    mt = MotorThermal(km25=km25,
                      r_wh=r_total * params.winding_resistance_fraction,
                      r_ha=r_total * (1 - params.winding_resistance_fraction),
                      c_w=c_total * params.winding_capacity_fraction,
                      c_h=c_total * (1 - params.winding_capacity_fraction))
    if params.step_s > 0.1 * mt.winding_tau_s:
        raise ConfigError(f"thermal step_s {params.step_s} s too coarse for {component.id} "
                          f"(winding time constant {mt.winding_tau_s:.1f} s)")
    return mt, None


def block_mean_square(torque_nm: np.ndarray, dt: float, step_s: float) -> np.ndarray:
    """Mean of torque^2 over consecutive blocks of step_s (copper loss is exact per block)."""
    n = max(1, int(round(step_s / dt)))
    usable = len(torque_nm) // n * n
    sq = torque_nm[:usable] ** 2
    blocks = sq.reshape(-1, n).mean(axis=1)
    if usable < len(torque_nm):
        blocks = np.append(blocks, np.mean(torque_nm[usable:] ** 2))
    return blocks


def simulate(tau2_blocks: np.ndarray, mt: MotorThermal, params: ThermalParams,
             t_w0: Optional[float] = None, t_h0: Optional[float] = None, stop_at_limit: bool = False):
    """Explicit Euler over blocks. Returns (winding temps, housing temps) per block end."""
    dt = params.step_s
    tw = params.ambient_c if t_w0 is None else t_w0
    th = params.ambient_c if t_h0 is None else t_h0
    out_w, out_h = np.empty(len(tau2_blocks)), np.empty(len(tau2_blocks))
    alpha = COPPER_TEMPCO_PER_K
    inv_km2 = 1.0 / mt.km25**2
    for i, tau2 in enumerate(tau2_blocks):
        p = tau2 * inv_km2 * (1 + alpha * (tw - 25))
        q_wh = (tw - th) / mt.r_wh
        q_ha = (th - params.ambient_c) / mt.r_ha
        tw += (p - q_wh) / mt.c_w * dt
        th += (q_wh - q_ha) / mt.c_h * dt
        out_w[i], out_h[i] = tw, th
        if stop_at_limit and tw >= params.winding_max_c:
            return out_w[:i + 1], out_h[:i + 1]
    return out_w, out_h


def steady_state_winding_c(tau: float, mt: MotorThermal, params: ThermalParams) -> float:
    """Closed form steady state; +inf if copper loss outruns cooling (thermal runaway)."""
    # T - Ta = R tau^2/Km25^2 (1 + alpha (T - 25))  ->  linear in T
    k = mt.r_total * tau**2 / mt.km25**2
    denom = 1 - k * COPPER_TEMPCO_PER_K
    if denom <= 0:
        return math.inf
    return (params.ambient_c + k * (1 - COPPER_TEMPCO_PER_K * 25)) / denom
