"""Electronics: heat and power budget, buffer ESR, conductor sizing (first pass, A-024)."""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from odrt.config import ConfigError

COLUMNS = ("id", "item", "role", "qty", "length_mm", "width_mm", "height_mm", "mass_kg", "dims_basis",
           "source_url", "accessed", "notes")


@dataclass(frozen=True)
class Part:
    id: str
    item: str
    role: str
    qty: int
    dims_mm: tuple
    dims_basis: str
    source_url: str
    notes: str


def load_electronics(path: Path) -> dict:
    with Path(path).open(newline="") as fh:
        reader = csv.DictReader(fh)
        if tuple(reader.fieldnames or ()) != COLUMNS:
            raise ConfigError(f"{path}: columns must be exactly {list(COLUMNS)}")
        out = {}
        for i, r in enumerate(reader, start=2):
            try:
                dims = tuple(float(r[k]) for k in ("length_mm", "width_mm", "height_mm"))
                qty = int(r["qty"])
            except ValueError as exc:
                raise ConfigError(f"{path}: line {i}: {exc}") from None
            if r["dims_basis"].startswith("cited") and not r["source_url"].startswith("https://"):
                raise ConfigError(f"{path}: line {i}: cited dimensions need an https source_url")
            out[r["id"]] = Part(r["id"], r["item"], r["role"], qty, dims, r["dims_basis"], r["source_url"], r["notes"])
    return out


def awg_for_area(area_mm2: float) -> int:
    """Largest AWG number (thinnest wire) with at least the given copper area."""
    for awg in range(30, -1, -1):
        d = 0.127 * 92 ** ((36 - awg) / 39)
        if math.pi * d**2 / 4 >= area_mm2:
            return awg
    return 0


def budget(inputs, cfg: dict) -> dict:
    """Heat and current budget for the lead design, from the drivetrain model."""
    from odrt.drivetrain import drive_metrics, solve
    from odrt.scenarios import generate
    opt = inputs.options[inputs.structure.design]
    comp = opt.component
    out = {}
    for key, scen in (("set", "heavy_tempo_limit"), ("session", "endurance_session_limit")):
        traj = generate(inputs.scenarios[scen], inputs.defaults)
        sig = solve(traj, opt.architecture, inputs.common, inputs.envelope.max_usable_stroke_m)
        m = drive_metrics(traj, sig, opt.architecture, inputs.common)
        out[f"{key}_mean_bus_w"] = m["mean_bus_w"]
        out[f"{key}_mean_copper_w"] = m["mean_copper_w"]
        out[f"{key}_window_copper_w"] = m["worst_window_copper_w"]
        if key == "set":
            per_motor = np.abs(sig.motor_torque_nm) / opt.count
            current = per_motor / comp.kt_nm_per_a
            out["motor_peak_current_a"] = float(current.max())
            win = max(1, min(int(round(60 / traj.dt)), len(current) - 1))  # 60 s or the whole set
            c2 = np.concatenate(([0.0], np.cumsum(current**2)))
            out["motor_window_rms_current_a"] = float(np.sqrt(np.max((c2[win:] - c2[:-win]) / win)))
            swing = (sig.bus_w - m["mean_bus_w"]) / inputs.dynamics.bus_v
            out["buffer_rms_current_a"] = float(np.sqrt(np.mean(swing**2)))
            out["bus_peak_current_a"] = float(np.max(np.abs(sig.bus_w)) / inputs.dynamics.bus_v)
    n = cfg["cells_in_series"]
    for label, esr in (("small", cfg["small_cell_esr_ohm"]), ("large", cfg["large_cell_esr_ohm"])):
        out[f"buffer_esr_{label}_ohm"] = n * esr
        out[f"buffer_loss_{label}_w"] = out["buffer_rms_current_a"] ** 2 * n * esr
        out[f"buffer_drop_{label}_v"] = out["bus_peak_current_a"] * n * esr
    out["buffer_small_bank_f"] = cfg["small_cell_f"] / n
    psu = lambda p: max(p, 0.0) * (1 / cfg["psu_efficiency"] - 1)  # noqa: E731
    drive = lambda p: cfg["drive_idle_w"] + cfg["drive_loss_fraction"] * abs(p)  # noqa: E731
    out["set_heat_w"] = (out["set_window_copper_w"] + psu(out["set_mean_bus_w"]) + drive(out["set_mean_bus_w"])
                         + out["buffer_loss_large_w"])
    out["session_heat_w"] = (out["session_mean_copper_w"] + psu(out["session_mean_bus_w"])
                             + drive(out["session_mean_bus_w"]) + cfg["standby_w"])
    ua = cfg["skin_area_m2"] * cfg["skin_h_w_m2k"]
    out["air_natural_c"] = cfg["room_c"] + out["session_heat_w"] / ua
    out["air_fan_c"] = cfg["room_c"] + out["session_heat_w"] / (ua + 1.2 * 1005 * cfg["fan_flow_m3_s"])
    out["fan_needed"] = out["air_natural_c"] > min(cfg["limits_c"].values()) - 10
    out["drive_over_continuous"] = out["motor_window_rms_current_a"] > cfg["drive_continuous_a"]
    out["phase_awg"] = awg_for_area(out["motor_window_rms_current_a"] / cfg["current_density_a_mm2"])
    out["bus_awg"] = awg_for_area(out["bus_peak_current_a"] / cfg["current_density_a_mm2"])
    return out
