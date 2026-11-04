# ODRT-500 — Open Digital Resistance Trainer

Simulation-first research project for an open, wall-powered, digitally controlled cable resistance trainer. Targets: 250 lbf (1,112 N) per modular unit, 500 lbf combined from two units, and a long-run $500 retail price per unit (ADR-002). Both are **hypotheses to test, not demonstrated capabilities**.

**Status:** Concept. Simulation-only. No hardware build or human-load testing is authorized; see the safety gates in the design brief. Progress: [`reports/STATUS.md`](reports/STATUS.md). Current integration: [`reports/modular.md`](reports/modular.md). Active engineering goal: [`docs/engineering/goal.md`](docs/engineering/goal.md); owner package target: [`ADR-003`](docs/architecture-decisions/ADR-003-voltra-sized-envelope.md).

- Design brief: [`docs/DESIGN.md`](docs/DESIGN.md)
- Coding agents: start with §11 of the brief, then `reports/STATUS.md`.

## Quick start

Requires Python ≥ 3.9 and make. Everything runs headlessly.

```sh
make venv     # create .venv with pinned dependencies (constraints.txt)
make check    # validate requirements, assumptions and scenarios
make architecture # compact architecture screen, measurable criteria and component-rating review
make coupled  # coupled mechanics, control, power/ESR, thermal and paired-bar faults
make coupled-verify # full coupled suite plus resolution and parameter-uncertainty checks
make buffer-study # separate compact capacitor experiment; retains solver failures
make electrical # functional schematic, semantic netlist and preliminary harness (Graphviz required)
make preliminary-costs # full-function planning allowances; not supplier quotes
make compact-package # compact integration STEP/GLB experiment and explicit geometry/fidelity checks
make compact-candidate # all named scenarios with CAD-derived inertia and compact fresh/aged banks
make compact-structure # candidate study followed by compact shaft/bearing/bridge screens
make compact-plots # candidate study followed by saved-trace tracking and fault plots
make support-revision # roller-bearing / two-ended-shaft screen at comparison loads
make revision-power # ODrive Pro + Regen Clamp upstream-buffer experiment
make r2-package # R2 integrated CAD (5:1, roller bearings, TV bank) with clash/keepout checks
make r2-candidate # R2 full suite, parallel (JOBS=n), plus support screen at simulated loads
make r3-candidate # R2 + conducted motor heat path + 30 V undervoltage trip
make control-study # controller gain variants on the R3 machine; reference controller unchanged
make r3c-candidate # R3 full suite with the proposed controller C1
make r4-candidate # R3 + C1 with the bank on the drive bus (bidirectional), full suite and bank checks
make power-path # R4 power-path sizing: clamp, fuse, pre-charge/discharge, balancing, dump monitor
make precharge # R4 start-up pre-charge and service-discharge sequences, with fault variants
make monitor-study # dump-monitor rules under measurement errors, tolerances and noise
make fast-study # fast-motion attribution: voltage saturation, storage topology, ratio
make test     # unit and negative tests, in parallel
make quick    # tests minus those marked slow (~15 s)
make t T=tests/test_r2.py K=expr # one file / matching tests
make retest   # rerun only last run's failures
make report   # simulate all scenarios, regenerate reports/
make cad      # modular unit + paired-board CAD: build/cad/*.step and *.glb
make fea      # side-plate FEA convergence study, reports/fea.md
make visual   # current unit/full/cutaway/exploded + paired-board GLBs in build/visual (metres, Y-up)
make ci       # all of the above; fails if committed reports are stale
```

There is no hosted CI. Run `make ci` before committing. Slow studies are skipped when their recorded input fingerprint is unchanged (`FORCE=1 make ci` reruns everything); a study refuses to publish if its inputs change while it runs. Clear `PYTHONPATH` when calling `.venv/bin/python` directly (the Makefile does).

Latest decision: [power-path review](docs/engineering/power-path-review.md) (R4 power path sized and sequence-simulated; dump monitor on the gate rule; 56 V trip), [R4 review](docs/engineering/r4-review.md) (REVISE; lead candidate, bank on the drive bus), [fast-motion review](docs/engineering/fast-motion-review.md) (voltage/energy-limited; bidirectional bank proposed), [controller study](docs/engineering/controller-study.md) and [R3 review](docs/engineering/r3-review.md) (REVISE); earlier: [R2 review](docs/engineering/r2-review.md), [R1 review](docs/engineering/compact-candidate-r1-review.md).

The reusable model interface and contributor checks are documented in [`docs/engineering/model-interface.md`](docs/engineering/model-interface.md). The reference model has no physical I/O. Controlled validation/review requirements are in [`validation-plan.md`](docs/engineering/validation-plan.md).

Additional engineering evidence: [compact buffer experiment](reports/compact_buffer.md),
[preliminary electrical definition](reports/electrical_definition.md), and
[complete-function preliminary cost allowances](reports/preliminary_costs.md).
These do not establish a complete compact assembly or a qualified hardware design.
The latest [compact CAD experiment](reports/compact_package.md) and
[engineering checkpoint](docs/engineering/latched-trip-and-layout-review.md) identify the remaining geometry/simulation mismatches.
The [current candidate review](docs/engineering/compact-candidate-r1-review.md) and
[mechanical screen](reports/compact_structure.md) retain the failures and the original goal's remaining work.

## Layout

| Path | Contents |
|---|---|
| `requirements/` | Requirements (R-xx), assumptions (A-xxx) and hazard log (H-xx), machine-readable |
| `configs/` | Envelope, duty-cycle scenarios, drivetrains, component study, thermal, dynamics and structure/layout parameters |
| `data/` | Real components with cited specs (`components.csv`) and the cited BOM (`bom.csv`); blank = not stated or not priced |
| `src/odrt/` | Models, CLI and report generation |
| `reports/` | Generated reports and figures, plus the hand-written `STATUS.md` |
| `tests/` | pytest suite |

## License

MIT — see [`LICENSE`](LICENSE).
