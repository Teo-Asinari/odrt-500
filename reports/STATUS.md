# Status

Last updated: 2026-11-02. Hand-written by the coding agent; everything else in `reports/` is generated.

## Done

- **WP0 (bootstrap and traceability):** `odrt` package and CLI (`check`, `simulate`, `report`), a Makefile, pinned dependencies (`constraints.txt`) and a pytest suite. Requirements R-01 to R-13 are in `requirements/requirements.yaml`; assumptions A-001 to A-006 are in `requirements/assumptions.yaml`. Every scenario cites both, and `reports/traceability.md` maps them. Reports record a hash of all inputs, and `odrt report` refuses stale or partial simulation results. `make ci` fails if the committed reports are out of date.
- **WP1 (reference use cases and duty cycles):** 11 named scenarios in `configs/scenarios.yaml`: 4 illustrative reference movements (curl, row, press, slow heavy pull) and 7 limit cases (500 lbf hold, 500 lbf at 1 m/s, full 2 m stroke, fast reversals, eccentric overload, a long endurance session, 8 lbf low force). Each one produces a 1 kHz trajectory (position, speed, acceleration, tension setpoint) and duty-cycle metrics: peak and RMS tension, peak absorbed and returned power, energy in each direction, time under tension, and longest time near peak. See `reports/duty_cycles.md`.

## Tests

49 tests pass. Among them, the unit conversions are checked against the brief's numbers (2224 N, 44.5 N·m, the 222/556/1112/2224 W table), and the minimum-jerk kinematics and energy accounting are checked against closed-form results. Negative tests confirm that invalid inputs exit with an error.

One bug was found and fixed during development: the first tension-ramp design let ramps run into cable motion, which undercounted energy by about 0.02%. Tension now changes only while the cable is stationary, and an input that leaves no room for a ramp is rejected.

## What the numbers already say (inputs, not feasibility)

- `power_corner_limit` asks for **2.2 kW absorbed and 2.1 kW returned** at peak, so the device must handle regenerated energy at that scale (R-06).
- `fast_reversal_limit` reaches **14 m/s²** and swings ±1.7 kW within 0.4 s (R-04, R-06).
- `peak_tension_hold_limit` holds near 500 lbf for **39 s continuously**, which sizes stall torque and stall heating (R-07).
- `eccentric_overload_limit` returns more energy than it absorbs (12.0 vs 8.0 kJ), so it needs a net power source, not only a brake.

## Main assumptions to challenge

- A-002: minimum-jerk motion is smoother than real pulls. Real peak acceleration and power will be higher.
- A-005: the reference strokes, speeds and loads are guesses. Measured cable data would replace them.
- A-006: RMS tension stands in for heating until the WP2 motor model exists.

## Open questions

- At what cable speed must 500 lbf be available, and for how long? This sets whether `power_corner_limit` is a requirement or an out-of-scope stress case.
- Is a 0.2 s tension ramp acceptable? It is a placeholder and sets the minimum hold time when tensions change.

## Next smallest verifiable milestone

WP2 analytical baseline: map each duty cycle to drum torque and speed (with winding-layer radius), then to motor torque, speed and copper loss for three clearly illustrative architectures (A direct drive, B quasi-direct, C high reduction), with unit tests against hand calculations.
