"""Custom motor sizing study (pre-design): scaling laws fitted to a cited motor family.

No electromagnetic design happens here. Standard sizing relations for radial-flux
surface-PM machines are fitted to published Tecnotion QTR/QTL data
(data/motor_family.csv) and used to estimate what a custom motor would need
(diameter, stack length, mass, inertia) to reach a target motor constant (A-023).

  Km^2 = c * r^a * L^2 / (L + e*r)   copper loss with end turns that scale with radius
  Tp   = s * r^b * L                 peak torque ~ air-gap area * shear
  Rth  = q / (r^g * H)               coil-to-mount resistance ~ 1 / cooled area
  tau  = t0 * r^h                    winding thermal time constant
  mass = rho * pi (Ro^2 - Ri^2) * H,  H = L + k_h * r,  J = j * mass * r^2

r = mean air-gap radius estimate (m), L = lamination stack (m), H = stator height (m).
"""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from odrt.config import ConfigError


@dataclass(frozen=True)
class FamilyPoint:
    model: str
    od_m: float
    id_m: float
    stack_m: float
    height_m: float
    km2: float
    peak_nm: float
    rth: float
    tau_s: float
    mass_kg: float
    inertia: float

    @property
    def r(self) -> float:  # mean of rotor ID and stator OD radii, rough gap-radius proxy
        return (self.od_m + self.id_m) / 4


def load_family(path: Path) -> list:
    with Path(path).open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise ConfigError(f"{path}: empty")
    pts = []
    for i, r in enumerate(rows, start=2):
        if not r["source_url"].startswith("https://"):
            raise ConfigError(f"{path}: line {i}: source_url must be https")
        try:
            pts.append(FamilyPoint(r["model"], float(r["stator_od_mm"]) / 1e3, float(r["rotor_id_mm"]) / 1e3,
                                   float(r["stack_mm"]) / 1e3, float(r["stator_height_mm"]) / 1e3,
                                   float(r["km2_nm2_per_w"]), float(r["peak_torque_nm"]), float(r["rth_k_per_w"]),
                                   float(r["tau_th_s"]), float(r["mass_kg"]), float(r["rotor_inertia_kg_m2"])))
        except ValueError as exc:
            raise ConfigError(f"{path}: line {i}: {exc}") from None
    return pts


@dataclass(frozen=True)
class Fit:
    c: float
    a: float
    e: float
    s: float
    b: float
    q: float
    g: float
    t0: float
    h: float
    rho: float
    k_h: float
    j: float
    id_ratio: float
    errors: dict      # quantity -> max relative error over the family


def _loglin(x_cols, y):
    """Least squares of log y on [1, log x...]; returns coefficients."""
    A = np.column_stack([np.ones(len(y))] + [np.log(x) for x in x_cols])
    coef, *_ = np.linalg.lstsq(A, np.log(y), rcond=None)
    return coef


def fit(pts) -> Fit:
    r = np.array([p.r for p in pts])
    L = np.array([p.stack_m for p in pts])
    H = np.array([p.height_m for p in pts])
    km2 = np.array([p.km2 for p in pts])
    best = None
    for a in np.linspace(1.0, 6.0, 101):
        for e in np.linspace(0.0, 2.0, 81):
            shape = r**a * L**2 / (L + e * r)
            c = math.exp(np.mean(np.log(km2 / shape)))
            err = np.max(np.abs(c * shape / km2 - 1))
            if best is None or err < best[0]:
                best = (err, c, a, e)
    _, c, a, e = best
    s_log, b = _loglin([r], np.array([p.peak_nm for p in pts]) / L)
    q_log, mg = _loglin([r], np.array([p.rth for p in pts]) * H)
    t_log, h = _loglin([r], np.array([p.tau_s for p in pts]))
    area = np.array([math.pi * ((p.od_m / 2) ** 2 - (p.id_m / 2) ** 2) for p in pts])
    rho = float(np.mean(np.array([p.mass_kg for p in pts]) / (area * H)))
    k_h = float(np.mean((H - L) / r))
    j = float(np.mean(np.array([p.inertia for p in pts]) / (np.array([p.mass_kg for p in pts]) * r**2)))
    id_ratio = float(np.mean([p.id_m / p.od_m for p in pts]))
    f = Fit(c, a, e, math.exp(s_log), b, math.exp(q_log), -mg, math.exp(t_log), h, rho, k_h, j, id_ratio, {})
    pred = {"km2": km2_law(f, r, L), "peak": peak_law(f, r, L), "rth": f.q / (r**f.g * H), "tau": f.t0 * r**f.h}
    meas = {"km2": km2, "peak": np.array([p.peak_nm for p in pts]), "rth": np.array([p.rth for p in pts]),
            "tau": np.array([p.tau_s for p in pts])}
    errors = {k: float(np.max(np.abs(pred[k] / meas[k] - 1))) for k in pred}
    return Fit(**{**f.__dict__, "errors": errors})


def km2_law(f: Fit, r, L):
    return f.c * r**f.a * L**2 / (L + f.e * r)


def peak_law(f: Fit, r, L):
    return f.s * r**f.b * L


def r_from_od(f: Fit, od_m: float) -> float:
    return od_m * (1 + f.id_ratio) / 4


def stack_for_km(f: Fit, od_m: float, km: float) -> float:
    """Solve c r^a L^2 - Km^2 L - Km^2 e r = 0 for the stack length L (m)."""
    r = r_from_od(f, od_m)
    A = f.c * r**f.a
    k2 = km**2
    return (k2 + math.sqrt(k2**2 + 4 * A * k2 * f.e * r)) / (2 * A)


@dataclass(frozen=True)
class Candidate:
    label: str
    od_m: float
    stack_m: float
    height_m: float
    km: float
    peak_nm: float
    rth: float
    tau_s: float
    mass_kg: float
    inertia: float


def size(f: Fit, label: str, od_m: float, km: float) -> Candidate:
    r = r_from_od(f, od_m)
    L = stack_for_km(f, od_m, km)
    H = L + f.k_h * r
    mass = f.rho * math.pi * ((od_m / 2) ** 2 - (f.id_ratio * od_m / 2) ** 2) * H
    return Candidate(label, od_m, L, H, km, float(peak_law(f, r, L)), f.q / (r**f.g * H), f.t0 * r**f.h, mass,
                     f.j * mass * r**2)


SCENARIOS = ("heavy_tempo_limit", "peak_tension_hold_limit", "slow_heavy_pull_reference", "endurance_session_limit")


def evaluate(inputs, cand: Candidate, ratio: float, efficiency: float, limit_c: float,
             mount_r_k_per_w: float = 1.0, mount_c_j_per_k: float = 2000.0) -> dict:
    """Run a candidate through the WP2 drivetrain and a one-node winding model on the heavy scenarios.

    Thermal: winding -> mount through the fitted Rth (vendor value, measured with the mount held at 20 C),
    then mount -> air through mount_r_k_per_w with heat capacity mount_c_j_per_k (frame, placeholders A-023).
    """
    import dataclasses

    from odrt.drivetrain import Architecture, solve
    from odrt.scenarios import generate
    from odrt.thermal import MotorThermal, block_mean_square, simulate
    from odrt.units import lbf_to_n

    drum = inputs.architectures[inputs.study.drum_from_architecture]
    arch = Architecture(name=cand.label, description="custom motor", gear_ratio=ratio, gear_efficiency=efficiency,
                        drum_core_radius_m=drum.drum_core_radius_m, turns_per_layer=drum.turns_per_layer,
                        max_layers=drum.max_layers, drum_inertia_kg_m2=drum.drum_inertia_kg_m2,
                        motor_rotor_inertia_kg_m2=cand.inertia, motor_km_nm_per_sqrt_w=cand.km)
    common = dataclasses.replace(inputs.common, winding_temp_c=25.0)  # thermal model applies the tempco itself
    mt = MotorThermal(km25=cand.km, r_wh=cand.rth, r_ha=mount_r_k_per_w, c_w=cand.tau_s / cand.rth,
                      c_h=mount_c_j_per_k + 460 * cand.mass_kg)
    tp = dataclasses.replace(inputs.thermal, winding_max_c=limit_c)
    r_drum = drum.drum_core_radius_m + inputs.common.cable_diameter_m / 2
    tau_peak = lbf_to_n(inputs.envelope.peak_tension_lbf) * r_drum / (ratio * efficiency)
    out = {"torque_peak_nm": tau_peak, "copper_peak_w": (tau_peak / cand.km) ** 2,
           "peak_ok": cand.peak_nm >= tau_peak, "felt_inertia_kg": arch.inertia_at_drum() / r_drum**2, "temps": {}}
    n = int(3600 / tp.step_s)
    tw, _ = simulate(np.full(n, tau_peak**2), mt, tp, stop_at_limit=True)
    out["hold_peak_s"] = len(tw) * tp.step_s if tw[-1] >= limit_c else None
    worst_need = 0.0
    for scen in SCENARIOS:
        traj = generate(inputs.scenarios[scen], inputs.defaults)
        sig = solve(traj, arch, common, inputs.envelope.max_usable_stroke_m)
        worst_need = max(worst_need, float(np.max(np.abs(sig.motor_torque_nm))))
        w, _ = simulate(block_mean_square(sig.motor_torque_nm, traj.dt, tp.step_s), mt, tp)
        out["temps"][scen] = float(np.max(w))
    out["peak_need_nm"] = worst_need
    out["peak_ok"] = cand.peak_nm >= worst_need
    out["thermal_ok"] = all(v < limit_c for v in out["temps"].values())
    return out
