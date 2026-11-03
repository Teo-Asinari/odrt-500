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
make test     # unit and negative tests
make report   # simulate all scenarios, regenerate reports/
make cad      # modular unit + paired-board CAD: build/cad/*.step and *.glb
make fea      # side-plate FEA convergence study, reports/fea.md
make visual   # current unit/full/cutaway/exploded + paired-board GLBs in build/visual (metres, Y-up)
make ci       # all of the above; fails if committed reports are stale
```

There is no hosted CI. Run `make ci` before committing.

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
