# ODRT-500 — Open Digital Resistance Trainer

Simulation-first research project for an open, wall-powered, digitally controlled cable resistance trainer. Targets: 250 lbf (1,112 N) per modular unit, 500 lbf combined from two units, and a long-run $500 retail price per unit (ADR-002). Both are **hypotheses to test, not demonstrated capabilities**.

**Status:** Concept. Simulation-only. No hardware build or human-load testing is authorized; see the safety gates in the design brief. Progress: [`reports/STATUS.md`](reports/STATUS.md). Current integration: [`reports/modular.md`](reports/modular.md).

- Design brief: [`docs/DESIGN.md`](docs/DESIGN.md)
- Coding agents: start with §11 of the brief, then `reports/STATUS.md`.

## Quick start

Requires Python ≥ 3.9 and make. Everything runs headlessly.

```sh
make venv     # create .venv with pinned dependencies (constraints.txt)
make check    # validate requirements, assumptions and scenarios
make test     # unit and negative tests
make report   # simulate all scenarios, regenerate reports/
make cad      # modular unit + paired-board CAD: build/cad/*.step and *.glb
make fea      # side-plate FEA convergence study, reports/fea.md
make visual   # current unit/full/cutaway/exploded + paired-board GLBs in build/visual (metres, Y-up)
make ci       # all of the above; fails if committed reports are stale
```

There is no hosted CI. Run `make ci` before committing.

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
