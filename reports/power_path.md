# R4 power-path sizing

Fingerprint: `b8dde555f3240ae164377463ce220a9c4ea21f6c5c4e560c2159ef6f6678033f` (R4 `2ab987c41238`)

**Functional sizing only.** Ratings are derived from the [R4 simulated envelope](r4_candidate.md) and cited data already in the repository. No part is selected; every `assumed` value in `data/power_path.yaml` is a verification item.

## Simulated envelope

| Quantity | Value | Worst case |
|---|---:|---|
| Bank RMS current A | 14.24 | r2_aged/single_fast_full |
| Bank peak current A | 34.70 | r2_fresh/left_torque_inverted |
| Bank maximum V | 53.68 | r2_fresh/single_stroke_full |
| Supply peak current A | 9.62 | r2_fresh/single_hold_full |
| Dump current, cycle-averaged maximum A | 19.76 | r2_aged/single_fast_full |
| Bus maximum V (incl. faults) | 55.92 | r2_aged/paired_dump_failure_coordinated |
| Bus minimum V (untripped cases) | 33.27 | r2_aged/single_fast_full |

## Regen Clamp in R4 (reverse block + dump)

R4 keeps the ODrive Regen Clamp but moves the bank to its output (drive) side. Its ideal diode then blocks back-feed into the supply, and its clamp remains the dump chopper.

| Check | Simulated / required | Clamp rating | Outcome |
|---|---:|---:|---|
| Bus maximum (incl. faults) | 55.92 V | 58 V | pass |
| Clamp maximum minus the 56 V trip | 2.0 V | at least 2 V | pass |
| Clamp maximum minus the simulated bus maximum | 2.08 V | — | pass |
| Forward (supply) current | 9.6 A | 20 A free air | pass |
| Brake current, cycle-averaged maximum (r2_aged/single_fast_full) | 19.8 A | 40 A heatspreader | pass |
| Brake current, switched (bus V / dump resistance) | 54.5 A | 80 A for 3 s | pass |

The chopper switches the full bus voltage across the 1 Ω dump, so its instantaneous current is bus V / 1 Ω, inside the 80 A / 3 s peak. The cycle-averaged current is compared with the 40 A heatspreader rating. Whether that rating is an average or an instantaneous limit, and the chopper ripple, are verification items.

## Reverse blocking (source block)

Provided by the clamp's ideal diode, or, if the 58 V rating is rejected, a discrete 80 V-class MOSFET OR-ing stage. It blocks up to 3.9 V in the simulated envelope and 4.0 V at the trip, carries 9.6 A forward and dissipates about 0.46 W at 0.005 Ω (assumed). Source branch DC fuse at least 12.0 A. Blocks during every regenerative event, not only at faults: the bus sits at the 54.4 V dump level in normal use.

## Bank fuse and disconnect

Bank RMS 14.2 A and peak 34.7 A. Fuse at least 17.8 A (1.25 × RMS); the peak is 1.9 × that rating, so a time-delay DC fuse is needed. Back-to-back MOSFET disconnect, 80 V class, about 0.81 W at 0.004 Ω (assumed).

| Bank | Prospective bank fault current A | Multiple of fuse rating |
|---|---:|---:|
| r2_fresh | 233 | 13.1 |
| r2_aged | 122 | 6.8 |

Bank short-circuit current is set by cell ESR, so the aged bank gives the lowest clearing multiple. Fuse time-current behaviour at that multiple must be checked against the cell and wiring I²t.

## Pre-charge and service discharge (one pulse resistor)

6.8 Ω holds start-up supply current at 7.7 A against the 9.6 A rating, peak 400 W. Bypass closes at 5 V difference. The resistor limits supply current itself, so start-up does not depend on the supply overload mode. The same resistor discharges the bank for service. Pulse-energy rating, not continuous power, sizes it.

| Bank | C F | τ s | To drive enable s | To bypass s | Pre-charge energy J | Bypass inrush A | Service discharge to 5 V s | Discharge energy J | Bleed-only τ h |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| r2_fresh | 5.00 | 34 | 68 | 79 | 6698 | 20.8 | 80 | 7203 | 13.9 |
| r2_aged | 3.15 | 21 | 43 | 50 | 4219 | 10.9 | 51 | 4538 | 8.8 |

Without an active discharge the 10 kΩ bleed alone leaves the bank charged for hours; service discharge is required.

## Cell balancing

Passive balancing: 260 Ω per cell (10 mA = 100 × an assumed 0.1 mA leakage spread), 0.52 W for the bank, self-discharge τ 7.2 h. Cells balanced at the setpoint; dynamic excursions above it divide by capacitance, so the lowest-capacitance cell rises fastest. Leakage-driven drift is held by the passive resistors while the supply holds the setpoint.

| Check | Worst cell V | Limit V | Outcome |
|---|---:|---:|---|
| Simulated maximum bank voltage | 2.693 | 2.95 cell monitor trip | pass |
| At the bus trip | 2.822 | 3 rated | pass |

Capacitance spread 10% below the string mean (the documented initial minimum). This replaces the earlier 1.05 worst-cell factor.

## Dump-path monitoring

Peak dump current 54.5 A; a 1 mΩ shunt gives 54 mV and 3.0 W peak. In the fresh-bank dump-failure case the bus reached 55.6 V without a trip. Rule: Expected dump current is commanded duty × bus V / 1 Ω. Flag a dump-path fault when measured current stays below half of expected for 0.1 s while expected exceeds 2 A, or when the bus exceeds 54.5 V (full duty) for 0.1 s; stop the unit and latch, independent of the overvoltage trip.

## Bank duty limit

If aged-cell fast reversal repeated continuously, the cells would reach about 70 °C (case maximum 65 °C). Bank temperature sensing (balancing node) feeds the existing torque derate from 55 °C to the case maximum; this is the duty limit for back-to-back fast work.

## Sources not read

- EPP-500-54 overload protection type (constant current vs hiccup) and start-up into capacitive load: Fetched 2026-11-03 but text not extractable; not used. The pre-charge below does not rely on it. (https://www.meanwell.com/Upload/PDF/EPP-500/EPP-500-SPEC.PDF)
- Eaton TV1860-3R0107-R leakage current and capacitance upper tolerance: Fetch timed out 2026-11-03; leakage is assumed below. (https://www.eaton.com/content/dam/eaton/products/electronic-components/resources/data-sheet/eaton-tv-supercapacitors-cylindrical-cells-data-sheet.pdf)
- Ideal-diode controller ratings (candidate class, e.g. 80 V-rated controllers): No controller is named; only required ratings are derived. (none read)

Reproduce: `make power-path` (after `make r4-candidate`).
