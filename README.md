# ODRT-500 — Open Digital Resistance Trainer

Simulation-first research project for an open, wall-powered, digitally controlled cable resistance trainer. Targets: up to 500 lbf (2,224 N) of cable tension and a long-run $500 retail price. Both are **hypotheses to test, not demonstrated capabilities**.

**Status:** Concept. Simulation-only. No hardware build or human-load testing is authorized; see the safety gates in the design brief. Progress: [`reports/STATUS.md`](reports/STATUS.md).

- Design brief: [`docs/DESIGN.md`](docs/DESIGN.md)
- Coding agents: start with §11 of the brief, then `reports/STATUS.md`.

## Quick start

Requires Python ≥ 3.9 and make. Everything runs headlessly.

```sh
make venv     # create .venv with pinned dependencies (constraints.txt)
make check    # validate requirements, assumptions and scenarios
make test     # unit and negative tests
make report   # simulate all scenarios, regenerate reports/
make ci       # all of the above; fails if committed reports are stale
```

There is no hosted CI. Run `make ci` before committing.

## Layout

| Path | Contents |
|---|---|
| `requirements/` | Requirements (R-xx) and assumptions register (A-xxx), machine-readable |
| `configs/` | System envelope (`baseline.yaml`) and named duty-cycle scenarios (`scenarios.yaml`) |
| `src/odrt/` | Models, CLI and report generation |
| `reports/` | Generated reports and figures, plus the hand-written `STATUS.md` |
| `tests/` | pytest suite |

## License

MIT — see [`LICENSE`](LICENSE).
