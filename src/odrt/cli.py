"""Headless CLI: `odrt check | simulate | report`. Exit code != 0 on any failure."""
from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path

import numpy as np

import odrt
from odrt.config import ConfigError
from odrt.drivetrain import drive_metrics, solve
from odrt.dutycycle import metrics
from odrt.project import load_inputs
from odrt.scenarios import generate

METRICS_FILE = "metrics.json"


def cmd_check(args) -> int:
    inputs = load_inputs(args.root)
    kinds = {}
    for s in inputs.scenarios.values():
        kinds[s.kind] = kinds.get(s.kind, 0) + 1
    print(f"OK: {len(inputs.requirements)} requirements, {len(inputs.assumptions)} assumptions, "
          f"{len(inputs.scenarios)} scenarios {kinds}, {len(inputs.architectures)} architectures")
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
    for name in names:
        traj = generate(inputs.scenarios[name], inputs.defaults)
        np.savez_compressed(out / f"{name}.npz", t=traj.t, x=traj.x, v=traj.v, a=traj.a,
                            tension_n=traj.tension_n, phase=traj.phase)
        results[name] = metrics(traj, inputs.defaults)
        for arch_name, arch in inputs.architectures.items():
            sig = solve(traj, arch, inputs.common, inputs.envelope.max_usable_stroke_m)
            drive[arch_name][name] = drive_metrics(traj, sig, arch, inputs.common)
        m = results[name]
        print(f"{name:28s} {m['duration_s']:7.1f} s  peak {m['peak_tension_lbf']:5.0f} lbf  "
              f"peak P {m['peak_power_absorbed_w']:6.0f} W  TUT {m['time_under_tension_s']:6.1f} s")
    payload = {
        "provenance": {
            "odrt_version": odrt.__version__,
            "input_hash": inputs.input_hash,
            "python": platform.python_version(),
            "numpy": np.__version__,
        },
        "scenarios": results,
        "drivetrain": drive,
    }
    (out / METRICS_FILE).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"wrote {len(results)} scenarios to {out}")
    return 0


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
