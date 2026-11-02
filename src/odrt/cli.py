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
    written = write_reports(inputs, payload, sim, Path(args.out), structural_summary(inputs, payload))
    for path in written:
        print(f"wrote {path}")
    return 0


def structural_summary(inputs, payload) -> dict:
    from odrt.structural import sizing
    st = inputs.structure
    sizes = sizing(st, inputs.options[st.design], inputs.common, inputs.envelope.peak_tension_lbf)
    dyn = payload.get("dynamics", {}).get(st.design)
    if dyn:
        on = [c.name for c in inputs.dynamics.cases if c.safety]
        sizes["observed_fault_peak_lbf"] = max(dyn[c]["peak_tension_lbf"] for c in on)
        sizes["observed_unprotected_peak_lbf"] = max(m["peak_tension_lbf"] for m in dyn.values())
    return sizes


def platform_summary(inputs, sizes, mech_env_mm, mech_mass_kg, mech_back_mm=None) -> dict:
    from odrt import cad, platform
    from odrt.drivetrain import Drum
    st = inputs.structure
    opt = inputs.options[st.design]
    return platform.evaluate(inputs.platform, cad.layout(st, opt, inputs.common, sizes), mech_env_mm,
                             Drum(opt.architecture, inputs.common).width_m * 1e3,
                             sizes["design_tension_lbf"] * 4.4482216152605,
                             sizes["observed_fault_peak_lbf"] * 4.4482216152605, mech_mass_kg, mech_back_mm)


def cmd_cad(args) -> int:
    from odrt import cad
    inputs = load_inputs(args.root)
    st = inputs.structure
    opt = inputs.options[st.design]
    sim_metrics = Path("build/sim/metrics.json")
    sizes = structural_summary(inputs, json.loads(sim_metrics.read_text()) if sim_metrics.exists() else {})
    if sizes.get("observed_fault_peak_lbf") is None:
        print("error: run `odrt simulate` first (platform checks need the dynamic snap load)", file=sys.stderr)
        return 2
    try:
        parts, geo = cad.build(st, opt, inputs.common, sizes)
    except cad.CadUnavailable as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3
    import cadquery as cq
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    assy = cad.assemble(parts)
    step = out / "odrt500_concept.step"
    assy.save(str(step))
    glb = out / "odrt500_concept.glb"  # for viewers without STEP import (e.g. Golemics)
    assy.save(str(glb), exportType="GLTF")
    cad.gltf_to_metres_y_up(glb)
    clashes = cad.interferences(parts)
    masses = cad.mass_kg(parts, st, opt.component.mass_kg or 0.0)
    env = cad.envelope_mm(parts)
    figs = Path(args.reports) / "figures"
    figs.mkdir(parents=True, exist_ok=True)
    compound = assy.toCompound().mirror("XY")  # the SVG exporter draws +Z downward
    views = {"iso": (1, 1.2, -0.8), "plan": (0, 0, -1)}
    for view, direction in views.items():
        cq.exporters.export(cq.Workplane().add(compound), str(figs / f"cad_{view}.svg"), exportType="SVG",
                            opt={"projectionDir": direction, "showAxes": False, "width": 520, "height": 400,
                                 "marginLeft": 10, "marginTop": 10, "strokeWidth": 0.4, "showHidden": False})
    from odrt.reporting import write_cad_report, write_platform_report
    report = write_cad_report(inputs, sizes, geo, env, masses, clashes, step, Path(args.reports))
    back = -min(p.shape.val().BoundingBox().ymin for p in parts)
    plat = platform_summary(inputs, sizes, env, sum(masses.values()), back)
    pparts, pgeo = cad.build_platform(st, opt, inputs.common, sizes, inputs.platform, plat)
    pclash = cad.interferences(pparts)
    passy = cad.assemble(pparts)
    passy.save(str(out / "odrt500_platform.step"))
    pglb = out / "odrt500_platform.glb"
    passy.save(str(pglb), exportType="GLTF")
    cad.gltf_to_metres_y_up(pglb)
    cq.exporters.export(cq.Workplane().add(passy.toCompound().mirror("XY")), str(figs / "cad_platform_iso.svg"),
                        exportType="SVG", opt={"projectionDir": (1.2, 1.0, -0.9), "showAxes": False, "width": 560,
                                               "height": 420, "marginLeft": 10, "marginTop": 10, "strokeWidth": 0.4,
                                               "showHidden": False})
    plat["interferences"] = len(pclash)
    plat["envelope_mm"] = cad.envelope_mm(pparts)
    write_platform_report(inputs, plat, Path(args.reports))
    clashes = clashes + pclash
    print(f"wrote {step}, {glb}, {report} and {len(views)} views; {len(clashes)} interferences")
    return 1 if clashes else 0


def cmd_fea(args) -> int:
    try:
        import gmsh  # noqa: F401
        import skfem  # noqa: F401
    except ImportError:
        print("error: FEA needs gmsh and scikit-fem: run `.venv/bin/pip install -c constraints.txt -e '.[fea]'`",
              file=sys.stderr)
        return 3
    from odrt import cad, fea
    from odrt.reporting import write_fea_report
    inputs = load_inputs(args.root)
    st = inputs.structure
    sizes = structural_summary(inputs, {})
    dims = cad.layout(st, inputs.options[st.design], inputs.common, sizes)
    force = sizes["bearing_radial_load_n"]
    runs = [fea.side_plate(dims, force, st.plate.youngs_gpa * 1e9, st.plate.poisson, h) for h in st.fea_mesh_sizes_mm]
    a, b = runs[-2]["max_von_mises_mpa"], runs[-1]["max_von_mises_mpa"]
    change = abs(b - a) / b * 100
    force_err = abs(runs[-1]["applied_force_n"] - force) / force * 100
    ok = change <= st.fea_converged_pct and force_err <= 1.0
    path = write_fea_report(inputs, dims, force, runs, change, force_err, ok, Path(args.reports))
    print(f"wrote {path}: peak von Mises {b:.1f} MPa, change {change:.1f}%, load error {force_err:.2f}%"
          f"{'' if ok else ' -- NOT CONVERGED or load mismatch'}")
    return 0 if ok else 1


def cmd_visual(args) -> int:
    from odrt import animate, cad, visual
    inputs = load_inputs(args.root)
    st = inputs.structure
    opt = inputs.options[st.design]
    try:
        parts, pivots, info = visual.build(st, opt, inputs.common, structural_summary(inputs, {}))
        handle = visual.handle()
    except cad.CadUnavailable as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    scene, _ = animate.build_scene(inputs, parts, pivots, info, handle)
    (out / "odrt500_detailed.glb").write_bytes(scene.to_glb())
    print(f"wrote {out / 'odrt500_detailed.glb'}")
    for ex in animate.EXERCISES:
        if args.only and ex.name not in args.only:
            continue
        scene, rep = animate.build_scene(inputs, parts, pivots, info, handle, ex)
        path = out / f"odrt500_{ex.name}.glb"
        path.write_bytes(scene.to_glb())
        print(f"wrote {path}: {rep['duration_s']:.1f} s, cable stroke {rep['stroke_m']:.2f} m, "
              f"peak cable speed {rep['peak_cable_speed_m_s']:.2f} m/s ({rep['scenario']} timing)")
    return 0


def cmd_motor(args) -> int:
    import yaml as _yaml
    from odrt import motor_sizing as ms
    from odrt.reporting import write_motor_report
    inputs = load_inputs(args.root)
    root = Path(args.root)
    cfg = _yaml.safe_load((root / "configs/custom_motor.yaml").read_text())
    fam = ms.load_family(root / "data/motor_family.csv")
    f = ms.fit(fam)
    rows = []
    for kind in ("geared", "direct_drive"):
        c = cfg[kind]
        for od in c["stator_od_mm"]:
            for km in c["km_targets"]:
                cand = ms.size(f, f"{kind}", od / 1e3, km)
                if cand.stack_m * 1e3 > cfg["max_stack_mm"]:
                    rows.append((kind, cand, None))
                    continue
                rows.append((kind, cand, ms.evaluate(inputs, cand, c["ratio"], c["efficiency"], cfg["winding_limit_c"],
                                                     cfg["mount_to_air_k_per_w"], cfg["mount_heat_capacity_j_per_k"])))
    # RO100 baseline under the same thermal assumptions (cited Km and the analogue's Km)
    from odrt.project import thermal_models
    mt, _ = thermal_models(inputs)["cubemars_ro100_kv55@6:1"]
    ro = inputs.components["cubemars_ro100_kv55"]
    base = []
    for label, km in (("RO100, cited Km", ro.km()), ("RO100 at analogue Km", 0.34)):
        cand = ms.Candidate(label, 0.1135, 0.0, 0.0, km, ro.peak_torque_nm, mt.r_wh, mt.winding_tau_s, ro.mass_kg,
                            ro.rotor_inertia_kg_m2)
        base.append((label, cand, ms.evaluate(inputs, cand, 6, 0.95, cfg["winding_limit_c"],
                                              cfg["mount_to_air_k_per_w"], cfg["mount_heat_capacity_j_per_k"])))
    path = write_motor_report(inputs, f, fam, cfg, rows, base, Path(args.reports))
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
    p = sub.add_parser("cad", help="build the parametric concept CAD (needs the [cad] extra)")
    p.add_argument("--out", default="build/cad")
    p.add_argument("--reports", default="reports")
    p = sub.add_parser("visual", help="detailed model and animated exercise GLBs (needs the [cad] extra)")
    p.add_argument("--out", default="build/visual")
    p.add_argument("--only", nargs="+", metavar="EXERCISE")
    p = sub.add_parser("motor", help="custom motor sizing study from the cited motor family")
    p.add_argument("--reports", default="reports")
    p = sub.add_parser("fea", help="side-plate FEA convergence study (needs the [fea] extra)")
    p.add_argument("--reports", default="reports")
    p = sub.add_parser("report", help="render reports from simulation results")
    p.add_argument("--sim", default="build/sim")
    p.add_argument("--out", default="reports")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    handler = {"check": cmd_check, "simulate": cmd_simulate, "report": cmd_report, "cad": cmd_cad,
               "fea": cmd_fea, "visual": cmd_visual,
               "motor": cmd_motor}[args.command]
    try:
        return handler(args)
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
