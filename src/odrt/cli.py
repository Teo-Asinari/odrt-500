"""Headless CLI: `odrt check | simulate | report`. Exit code != 0 on any failure."""
from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path

import numpy as np

import odrt
from odrt.components import none_if_nan
from odrt.config import ConfigError
from odrt.drivetrain import drive_metrics, solve
from odrt.dutycycle import metrics
from odrt.project import load_inputs, thermal_models
from odrt import thermal as th
from odrt.units import lbf_to_n
from odrt.scenarios import generate

METRICS_FILE = "metrics.json"


def cmd_check(args) -> int:
    inputs = load_inputs(args.root)
    thermal_models(inputs)  # validates the thermal step against every motor
    kinds = {}
    for s in inputs.scenarios.values():
        kinds[s.kind] = kinds.get(s.kind, 0) + 1
    print(f"OK: {len(inputs.requirements)} requirements, {len(inputs.assumptions)} assumptions, "
          f"{len(inputs.scenarios)} scenarios {kinds}, {len(inputs.architectures)} architectures, "
          f"{len(inputs.components)} components ({len(inputs.options)} options)")
    print(f"input hash {inputs.input_hash[:12]}")
    return 0


def cmd_simulate(args) -> int:
    inputs = load_inputs(args.root)
    names = args.only or list(inputs.scenarios)
    unknown = sorted(set(names) - set(inputs.scenarios))
    if unknown:
        raise ConfigError(f"unknown scenarios {unknown}")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    results, drive = {}, {a: {} for a in inputs.architectures}
    comp = {o: {} for o in inputs.options}
    thermals = thermal_models(inputs)
    therm = {}
    for opt_name, (mt, reason) in thermals.items():
        opt = inputs.options[opt_name]
        entry = {"reason": reason, "scenarios": {}}
        if mt is not None:
            r = max(opt.architecture.drum_core_radius_m + inputs.common.cable_diameter_m / 2, 1e-9)
            tau = lbf_to_n(inputs.envelope.peak_tension_lbf) * r / (opt.external_ratio * opt.efficiency) / opt.count
            steady = th.steady_state_winding_c(tau, mt, inputs.thermal)
            n_steps = int(inputs.thermal.peak_hold_cap_s / inputs.thermal.step_s)
            tw, _ = th.simulate(np.full(n_steps, tau**2), mt, inputs.thermal, stop_at_limit=True)
            reached = tw[-1] >= inputs.thermal.winding_max_c
            entry.update({"r_total_k_per_w": mt.r_total, "winding_tau_s": mt.winding_tau_s,
                          "peak_tension_torque_per_motor_nm": tau,
                          "peak_tension_steady_winding_c": None if steady == float("inf") else steady,
                          "peak_tension_hold_s": len(tw) * inputs.thermal.step_s if reached else None})
        therm[opt_name] = entry
    for name in names:
        traj = generate(inputs.scenarios[name], inputs.defaults)
        np.savez_compressed(out / f"{name}.npz", t=traj.t, x=traj.x, v=traj.v, a=traj.a,
                            tension_n=traj.tension_n, phase=traj.phase)
        results[name] = metrics(traj, inputs.defaults)
        for arch_name, arch in inputs.architectures.items():
            sig = solve(traj, arch, inputs.common, inputs.envelope.max_usable_stroke_m)
            drive[arch_name][name] = drive_metrics(traj, sig, arch, inputs.common)
        for opt_name, opt in inputs.options.items():
            sig = solve(traj, opt.architecture, inputs.common, inputs.envelope.max_usable_stroke_m)
            m = drive_metrics(traj, sig, opt.architecture, inputs.common)
            mt = thermals[opt_name][0]
            if mt is not None:
                per_motor = sig.motor_torque_nm / opt.count
                tw, _ = th.simulate(th.block_mean_square(per_motor, traj.dt, inputs.thermal.step_s), mt,
                                    inputs.thermal)
                therm[opt_name]["scenarios"][name] = float(np.max(tw))
            comp[opt_name][name] = {k: none_if_nan(m[k]) for k in (
                "peak_motor_torque_nm", "worst_window_rms_motor_torque_nm", "peak_motor_speed_rpm",
                "worst_window_copper_w", "effective_cable_mass_kg", "radius_max_m")}
        m = results[name]
        print(f"{name:28s} {m['duration_s']:7.1f} s  peak {m['peak_tension_lbf']:5.0f} lbf  "
              f"peak P {m['peak_power_absorbed_w']:6.0f} W  TUT {m['time_under_tension_s']:6.1f} s")
    dyn = run_dynamics(inputs, out)
    payload = {
        "provenance": {
            "odrt_version": odrt.__version__,
            "input_hash": inputs.input_hash,
            "python": platform.python_version(),
            "numpy": np.__version__,
        },
        "scenarios": results,
        "drivetrain": drive,
        "components": comp,
        "thermal": therm,
        "dynamics": dyn,
    }
    (out / METRICS_FILE).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"wrote {len(results)} scenarios to {out}")
    return 0


def run_dynamics(inputs, out: Path) -> dict:
    from odrt.dynamics import Plant, run
    trajs = {c.scenario: generate(inputs.scenarios[c.scenario], inputs.defaults) for c in inputs.dynamics.cases}
    result = {}
    for design in inputs.dynamics.designs:
        plant = Plant.from_option(inputs.options[design], inputs.common)
        result[design] = {}
        for case in inputs.dynamics.cases:
            res = run(case, trajs[case.scenario], plant, inputs.dynamics)
            result[design][case.name] = res["metrics"]
            np.savez_compressed(out / f"dyn__{_slug(design)}__{case.name}.npz", **res["signals"])
        print(f"dynamics {design}: {len(inputs.dynamics.cases)} cases")
    return result


def _slug(text: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in text)


def cmd_report(args) -> int:
    from odrt.reporting import write_reports  # matplotlib import is slow; only load when needed

    inputs = load_inputs(args.root)
    sim = Path(args.sim)
    try:
        payload = json.loads((sim / METRICS_FILE).read_text())
    except FileNotFoundError:
        raise ConfigError(f"{sim / METRICS_FILE} not found: run `odrt simulate` first") from None
    if payload["provenance"]["input_hash"] != inputs.input_hash:
        raise ConfigError("simulation results are stale (input hash differs): rerun `odrt simulate`")
    missing = sorted(set(inputs.scenarios) - set(payload["scenarios"]))
    missing += sorted(f"{a}/{s}" for a in inputs.architectures for s in inputs.scenarios
                      if s not in payload.get("drivetrain", {}).get(a, {}))
    missing += sorted(f"{d}/{c.name}" for d in inputs.dynamics.designs for c in inputs.dynamics.cases
                      if c.name not in payload.get("dynamics", {}).get(d, {}))
    missing += sorted(f"{o}/{s}" for o in inputs.options for s in inputs.scenarios
                      if s not in payload.get("components", {}).get(o, {}))
    if missing:
        raise ConfigError(f"simulation results missing {missing}: rerun `odrt simulate`")
    written = write_reports(inputs, payload, sim, Path(args.out))
    for path in written:
        print(f"wrote {path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="odrt", description=__doc__)
    parser.add_argument("--root", default=".", help="repository root (default: .)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check", help="validate requirements, assumptions and scenarios")
    p = sub.add_parser("simulate", help="generate scenario trajectories and duty-cycle metrics")
    p.add_argument("--out", default="build/sim")
    p.add_argument("--only", nargs="+", metavar="SCENARIO")
    p = sub.add_parser("report", help="render reports from simulation results")
    p.add_argument("--sim", default="build/sim")
    p.add_argument("--out", default="reports")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    handler = {"check": cmd_check, "simulate": cmd_simulate, "report": cmd_report}[args.command]
    try:
        return handler(args)
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
