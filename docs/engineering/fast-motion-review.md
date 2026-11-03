# Fast-motion review — 2026-11-03

**Decision: correct the controller-study diagnosis. Fast reversal and full stroke are limited by voltage and stored energy, not by force-loop bandwidth. Propose a bidirectional bank (bank on the drive bus) as the R4 power topology at 5:1. No ratio fits the heavy and fast cases together with the RO100 at a 52 V bus. That is a motor/bus decision for the owner, alongside the endurance Km decision.**

Evidence: [fast-motion study](../../reports/fast_motion_study.md) (9 variants × 6 cases × fresh/aged banks on R3 + C1),
and a new report-only diagnostic in `coupled.py`: `voltage_limited_fraction` and `voltage_limited_error_share`.
Nothing is adopted. The reference controller, R3 and R3 + C1 are unchanged.

## What the controller study got wrong

The [controller study](controller-study.md) concluded that fast reversal was "not current- or voltage-limited" and that the residual error pointed to force-loop bandwidth. Both statements came from the `voltage_uncontrollable` flag. That flag is only set when *no* current is feasible. It is not set when the requested current is clamped to the back-EMF/bus bound, which is the normal way a drive saturates.

On the R3 + C1 fast-reversal trace (fresh bank):

- The tension error is low-frequency: its spectrum sits at the 1.25 Hz rep rate and its 2.5 Hz harmonic. It is biased by direction: about +66 N mean while paying out and −68 N while retracting. The integrator winds up to about 250 N chasing it.
- Force-sensor lag contributes about 3 N RMS and torque-loop lag about 5 N RMS. Bandwidth is not the limit.
- The requested current sits on the voltage bound for **52%** of the set, and those samples carry **85%** of the squared tracking error. Back-EMF reaches about 46 V at 1.7 m/s. The drive has about 27 V of phase voltage available (0.78 modulation × a bus that sags to 34.8 V).
- Retracting fast, the drive cannot push enough current against back-EMF, so tension is low. Paying out fast, the voltage bound forces a minimum braking current, so tension is high.
- The planned-acceleration inertia feedforward is mistimed against the real handle motion (the user model lags the plan). It also uses information a real controller would not have: the user's planned trajectory. Removing it costs 2 points (11.4% → 13.5%), because feedback is starved by the same voltage limit. Measured-acceleration feedforward is about neutral on fast reversal and worsens paired heavy (0.1% → 1.2%).

Full stroke is the same mechanism without the energy problem: 32% of the stroke is on the voltage bound, carrying 78% of the error.

## Energy: the one-way clamp throws regeneration away

Since R2, the bank sits upstream of the ODrive Regen Clamp's ideal diode. Regeneration cannot return to storage (`upstream_buffer.py`). In R3 + C1 fast reversal, payout regenerates about 417 W mean, and the dump burns **317 W** of it. Retraction is then fed by a bank that only the 500 W supply refills: the bank falls from 52 V to 40 V over 17 s with the fresh cells, and the aged bank reaches the 30 V trip.

With the bank on the drive bus through its ESR (bidirectional), the same set dumps 49 W and holds the bank at 48.7–52.5 V:

| Case (fresh / aged) | R3 + C1 | Bidirectional, 5:1 |
|---|---|---|
| Fast reversal | 11.4% / 62% with trip | **8.0% / 12.1%, no trip** |
| Full stroke | 14.1% / 14.5% | 10.7% / 11.5% |
| Heavy, paired heavy, slow | 0.1% | 0.1% |
| Endurance | 21.4% (Km-limited) | 21.1% (unchanged; Km-limited) |
| Fast reversal mean dump | 317 W | 49 W |

A stiffer bank (ESR × 0.1) helps the fresh case less (8.8%) and is not a part that exists. Bidirectional storage is the larger and more realistic lever.

## The ratio is boxed in

| Ratio, bidirectional | Fast reversal | Full stroke | Heavy | Notes |
|---|---|---|---|---|
| 5:1 | 8.0% | 10.7% | 0.1% | 800 Hz electrical in fast cases |
| 4.5:1 | 6.9% | 1.0% | 4.5% (current limit, 49.9 A) | aged bank trips in fast and heavy |
| 4.5:1, 60 A | 6.9% | 1.0% | 3.0% | aged bank still trips |
| 4:1 | 6.8% | 1.0% | 13.9% | under 700 Hz; aged trips |

Heavy sets need at least 5:1 at the 50 A limit. Fast motion and full stroke need about 4:1 or less, for back-EMF and the 700 Hz screen. Even the 60 A motor peak does not close the gap. With the RO100 on a 52 V bus, no single ratio passes both. The fixes are outside control tuning:

1. **Higher bus voltage.** The ODrive Pro's 58 V maximum leaves little headroom above the 54.5 V dump, so this needs a different drive class.
2. **A motor with a higher torque constant per volt** (more torque per amp at the same back-EMF), which is the same direction as the endurance Km problem. The [custom-motor study](../../reports/custom_motor.md) and the RO100 data request already point here.
3. **Field weakening.** This is not modelled, and is of limited use on a surface-PM outrunner.
4. **An owner-accepted fast envelope**, for example a lower force ceiling above a stated cable speed.

## Proposals

- **R4 power topology: bidirectional bank at 5:1.** It needs, and does not yet have: a pre-charge/inrush circuit, bank ripple-current and cell-balancing checks, supply reverse blocking, a dump threshold that clears the bank's maximum (20 × 3.0 V = 60 V rating against the 54.5 V dump), and a rerun of the full fault suite (dump failure, power loss, paired asymmetry), none of which this study covers.
- **Retire the planned-acceleration feedforward** from any hardware-intended controller. It is not realisable. Model C1 with `inertia_feedforward: 0` as the honest baseline, or with measured acceleration after a noise model exists.
- **Owner decisions** (with the endurance Km decision from the [R3 review](r3-review.md)): motor/bus class, or an accepted reduced fast envelope.

## Limitations

- Ratio variants keep the R2 CAD drum inertia and do not rerun belt, bearing or support screens.
- The bidirectional model keeps the one-way supply and the same dump; inrush, switching ripple and supply behaviour below 52 V are not modelled.
- Electrical frequency is still over 700 Hz at 5:1 in every fast variant, which needs a sourced drive limit.
- Voltage saturation share is a diagnostic. No pass/fail criterion is attached to it.
