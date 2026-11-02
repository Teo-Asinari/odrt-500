# Status

Last updated: 2026-11-02. Hand-written by the coding agent; everything else in `reports/` is generated.

## Done

- **WP0 (bootstrap and traceability):** `odrt` package and CLI (`check`, `simulate`, `report`), a Makefile, pinned dependencies and a pytest suite. Requirements R-01 to R-13 and assumptions A-001 to A-012 are machine-readable, and every scenario cites them (`reports/traceability.md`). Reports record a hash of all inputs. `odrt report` refuses stale or partial results, and `make ci` fails if the committed reports are out of date.
- **WP1 (duty cycles):** 11 named scenarios, 4 reference movements and 7 limit cases (`reports/duty_cycles.md`).
- **WP2 analytical baseline:** each duty cycle is mapped to drum torque (with winding-layer radius) and then to motor torque, speed, copper loss and bus power, for three illustrative architectures (`reports/drivetrain_baseline.md`).
- **R-01 scoped:** per the user, 500 lbf is a human maximum at normal heavy-lift tempos (A-007). That speed is now cited: at 1RM, squats average 0.29 m/s but peak at 0.89 m/s (Conceição et al., URL in A-007). `heavy_tempo_limit` therefore peaks at 0.94 m/s and 2.1 kW mechanical.

## Tests

64 tests pass. They cover:
- unit conversions against the brief's numbers;
- minimum-jerk kinematics and duty-cycle energy against closed forms;
- motor torque in each power-flow direction, copper loss and Km temperature derating against hand calculations;
- energy conservation over a full scenario with inertia and gear losses;
- multi-layer drum radius steps;
- negative tests for invalid inputs.

## What WP2 suggests (illustrative parameters, A-008: directions, not results)

- **Wall power may not be the limit; energy buffering is.** A and B draw up to ~1.45 kW at 500 lbf heavy tempo and ~2.1 kW in fast reversals, and regenerate up to ~1.7 kW on every pull. Session-mean bus power is only 50–380 W. A lossless buffer of about 2 kJ per heavy set (about 6 kJ for the endurance session) would let the supply run near the mean, so this is worth testing early (R-06). Drive and PSU losses are not yet included (A-010).
- **Heat at 500 lbf is the binding constraint for R-01/R-02.** With the illustrative motors, holding 500 lbf costs ~360–400 W of copper loss continuously. How long 500 lbf can be held is a thermal question, not a torque question.
- **High reduction (C) looks poor:** 260 kg effective cable mass, 10,000–25,000 motor rpm, and a 5.1 kW peak bus draw in fast reversals just to move its own inertia. A and B land within ~10% of each other on power and heat. B needs a 5× smaller motor torque (10.6 vs 50 N·m) at the cost of a gearbox.

## Main assumptions to challenge

- A-008: every architecture number is a placeholder. Nothing above is a feasibility claim.
- A-002 / A-007: minimum-jerk motion doesn't reproduce measured 1RM speed profiles (peak about 3× mean). The scenario matches peak speed, so it overstates average speed, power and heat.
- A-010: no drive, PSU or iron losses yet.
- A-012: a 60 s worst-window RMS stands in for a thermal model.

## Open questions

- How long must 500 lbf be held? This now decides motor size and cooling.
- Is an internal energy buffer (capacitors) acceptable within "no battery operation"? It isn't a battery, but it adds stored energy, which is a hazard (R-09).
- The upper-body 1RM velocity is not yet sourced (A-007 cites lower-body lifts only).

## Next smallest verifiable milestone

WP3 component reality: replace A and B's placeholder motor and gearbox values with 2–3 real, cited candidates each (Km, continuous and peak torque, max speed, inertia, price with source URL and date). Then turn the requirement columns in `drivetrain_baseline.md` into pass/fail margins. After that, a first-order thermal network (R-07) to replace A-012.
