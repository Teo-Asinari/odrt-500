# R3 candidate review — 2026-11-02

**Decision: REVISE. R3 removes the R2 heat and aged-bank regressions in every case except the motor-limited endurance session. What remains is a motor Km question for the owner and a control problem.**

R3 is R2 (same CAD, 5:1, TV bank, upstream clamp, unchanged gains) plus two proposals:

1. **Conducted motor heat path** ([data/r3_thermal.yaml](../../data/r3_thermal.yaml), [frame_thermal.py](../../src/odrt/frame_thermal.py)). The motor housing conducts through the stator carrier into an aluminium base and skin (0.3 K/W), which lose heat to the room (1.4 W/K) and to the internal airflow (1.5 W/K), with 800 J/K of frame capacity. This requires a metallic enclosure, which matches the owner's black metallic finish. The energy ledger is extended, so energy residuals still audit the model.
2. **30 V undervoltage trip** ([data/r3_power.yaml](../../data/r3_power.yaml)) instead of 40 V. The ODrive Pro datasheet gives 15–58 V DC, so 40 V was a reference choice, not a drive limit. The voltage-controllability and modulation screens are unchanged and still judge whether the motor can be driven.

Evidence: [R3 candidate](../../reports/r3_candidate.md) — 54 scenarios, four 3-resolution studies (pass), 10 uncertainty cases, support screen at simulated loads (8/16 corners pass at 850–1000 N preload; peak rope force 1575 N). No solver failures.

## R2 → R3

| Case | R2 | Heat path only | R3 |
|---|---|---|---|
| Slow heavy pull (winding) | 128.5 °C, 3.45% | 104.7 °C, 0.07% | 104.7 °C, 0.07% |
| Row / press / eccentric (winding) | 59–71 °C | 49–59 °C | 49–59 °C |
| Aged paired heavy | 17%, undervoltage trip | 17%, trip | **0.18%, no trip** |
| Aged buffered power loss | undervoltage trip | trip | **no trip** (32 V min) |
| Aged endurance | 98%, trip | 98%, trip | 21%, no trip |
| Fresh fast reversal | 68%, trip | 68%, trip | 29%, no trip |
| Aged fast reversal | 91%, trip | 91%, trip | 71%, trip at 30 V |
| Fresh/aged endurance | 40% / 98% | 21% / 98% | 21% / 21%, 128.6 °C |
| Full stroke | 36%, travel-stop engagement | same | same |

Heat-path bounds on the slow heavy pull: high interface resistance (0.8 K/W) gives 111.7 °C; low room conductance (0.7 W/K) gives 105.9 °C; low room conductance in a room 15 °C warmer gives 125.6 °C, which is in derate but still tracks at 0.07%.

## What remains

- **Endurance is limited by the motor's Km.** The winding reaches about 127 °C within the first 200 s and stays in the 120–140 °C derate band for the whole session. The winding runs about 45 K above its housing, so the bottleneck is the RO100's internal winding-to-housing path at roughly 160 W of mean copper loss. An external heat path cannot fix that. This is the A-022 risk realised. Options: (a) the owner accepts a derated endurance envelope; (b) go back to 6:1, which cuts copper loss by about 31% but makes fast moves worse; (c) a higher-Km or potted motor, as in the custom-motor study.
- **Fast reversal and full stroke are control/voltage problems.** They fail the proposed tracking, overshoot and 700 Hz electrical-frequency screens at every ratio and bank tried; full stroke also hits the virtual travel stop. Gains have not been changed in any revision. The next step is a separately reported controller study.
- **Aged asymmetric paired set and aged fast reversal** still trip, at 30 V.
- **Fault cases:** the inverted-torque fault fails voltage controllability (88.6 A phase-brake current); a 1% imbalanced release still rotates the bar about 48°.
- **Low Km** (−36%) still trips; a room 15 °C warmer still fails the drive's rated ambient temperature.
- Not addressed: wiring between the three cell groups, trays, retention, belt rating and tensioner, frame stiffness/joints, mains isolation, demonstrated airflow, supply behaviour below 52 V (constant current assumed), and auxiliary rails riding through 30 V.
