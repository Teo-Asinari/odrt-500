# Controller study — 2026-11-02

**Decision: propose controller C1 for adoption after review; fast reversal still fails and needs a force-loop design, not more gain.**

Evidence: [gain/feature sweep](../../reports/control_study.md) (16 variants × 8 cases on the R3 machine) and
[R3 + C1 full suite](../../reports/r3c_candidate.md) (54 scenarios, refinements and uncertainties; verification passes).
The reference controller in `configs/coupled.yaml` is unchanged; every other study still uses it.

## Diagnosis

- **Fast reversal** is not current- or voltage-limited in R3. About 13 kg of reflected inertia at the rope, weak force feedback (kp 0.2) and feedforward on the scenario's planned acceleration leave a 240 N RMS error.
- **Full stroke** had two causes. The release-safety speed limiter (1 m/s, 3000 N·s/m) cut tension during normal 1.5 m/s retraction, and the scenario ran exactly onto both travel stops (0 and 2.0 m) at speed.
- **Electrical frequency** (743–796 Hz against the provisional 700 Hz screen) comes from speed × 5:1 × pole pairs. It does not respond to gains and needs a sourced drive limit.

## New optional controller features (`coupled.py`)

Defaults reproduce the reference exactly; a re-run of the reference fast-reversal case is bit-identical.

- `acceleration_blend`: inertia feedforward on measured payout acceleration (derivative of the filtered encoder speed) instead of the planned acceleration. This turned out to add little on top of high feedback gain (11.3% → 10.6%) and makes the asymmetric paired set slightly worse, so C1 does not use it.
- `end_zone_m`, `end_zone_gain_n_s_m`: within the zone, the command gains velocity-proportional braking toward the nearest travel limit. Tracking is judged against the braked command.

## C1: kp 4, release limiter 2.5 m/s, 0.15 m end zone at 600 N·s/m

| Case (fresh / aged) | R3 reference controller | R3 + C1 |
|---|---|---|
| Fast reversal | 29% / 71% with trip | 11.4% / 62% with trip |
| Full stroke | 36% with travel-stop engagement | 14% (no stop engagement) |
| Paired asymmetric | 0.79% / 13% with trip, 92° bar | 0.10% / 0.10%, no trip, 0.6° bar |
| Peak rope force (fast reversal / full stroke) | 1346 / 1515 N | 1064 / 648 N |
| Heavy, release, power-loss and sensor faults | pass | pass (tracking 0.1–0.3%) |
| Dump-failure faults | 0.13% | 1.29% (protective overvoltage trip unchanged) |
| 1% imbalanced release | 48° bar rotation | unchanged |

Release safety is not weakened: release cases peak at 1.4 m/s, below both limiter settings.

## Still failing with C1

- Fast reversal 11% (proposed limit 5%) with 19% overshoot. The residual error is largest at constant speed, not during acceleration, which points to force-loop bandwidth against a very stiff cable (current loop 1 ms, force filter 2 ms). Next: a loop-shaping design with an explicit cable/arm model and a stability-margin analysis instead of time-domain gain search.
- Full stroke 14% and electrical frequency in both fast cases.
- Aged-bank fast reversal still trips at 30 V. Endurance is unchanged (motor Km).
- The inverted-torque fault fails voltage controllability (phase braking at 88.6 A).

## Caveats before adoption

- Sensor noise and quantization are not modelled; kp 4 will look better here than on hardware.
- Stability is shown only by these time-domain cases; there is no frequency-domain margin analysis yet.
- The end zone and 2.5 m/s limiter are behaviour changes a user would feel. They need human-factors review.
