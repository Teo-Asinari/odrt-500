# R4 candidate review — 2026-11-03

> **Update:** the overvoltage trip is now 56 V, not 57 V ([power-path review](power-path-review.md)). The rerun changes only the aged dump-failure cases, which trip 58 ms earlier at 55.92 V. Every other result below is unchanged. The worst cell at the trip is now 2.82 V (capacitance-spread analysis).

**Decision: REVISE, but R4 should replace R3 + C1 as the lead candidate.** Moving the bank onto the drive bus improves or leaves unchanged every case in the full suite, with no new failed comparison. Fast reversal and full stroke still fail, because they are voltage-limited by the RO100 at 5:1 (see the [fast-motion review](fast-motion-review.md)). Endurance is still limited by the motor's Km. Both need the owner's motor/bus decision. The bank exceeds its continuous RMS current rating only in back-to-back fast reversal, and the power-path hardware is not designed.

R4 = R3 + C1, with the 20-cell TV bank moved from upstream of the one-way Regen Clamp onto the drive bus ([data/r4_power.yaml](../../data/r4_power.yaml)). The supply stays one-way, and the 54.35–54.5 V dump and 57 V trip are unchanged.

Evidence: [R4 candidate](../../reports/r4_candidate.md) (`make r4-candidate`). It covers all 54 normal and fault scenarios on fresh and aged banks, four 3-resolution refinements (all pass), seven uncertainties, eight controller-variant runs and the support screen at simulated loads (8/16 corners pass, as in R3). There were no solver failures.

## R3 + C1 → R4

| Case (fresh / aged) | R3 + C1 | R4 |
|---|---|---|
| Fast reversal | 11.4% / 62%, undervoltage trip | **8.0% / 12.1%, no trip** |
| Full stroke | 14.1% / 14.5% | 10.7% / 11.5% |
| Heavy, paired heavy, asymmetric, slow, row, press, curl | 0.07–0.13% | unchanged |
| Endurance | 21.4%, 128.6 °C | 21.1%, 128.5 °C (Km-limited, unchanged) |
| Aged heavy, minimum bus | 40.1 V | 42.1 V |
| Aged buffered power loss, minimum bus | 32.1 V | 33.7 V |
| Fresh dump failure | overvoltage trip at 56.9 V | **no trip**, bank absorbs, 55.6 V |
| Aged dump failure | overvoltage trip | overvoltage trip (unchanged) |
| Inverted torque | fails voltage controllability | unchanged |
| 1% imbalanced release | 46.5° bar | unchanged |

The normal maximum bus voltage is now the 54.4 V dump level, not about 53 V, because regeneration charges the bank up to it.

**Dump-failure note.** With the fresh bank, a failed dump no longer trips on overvoltage: the bank absorbs one set. That is gentler behaviour, but it hides the fault. The supervisor needs independent dump-path detection, such as a commanded-versus-measured dump current check, rather than relying on the overvoltage trip.

## Realisable feedforward

C1 uses inertia feedforward on the scenario's planned acceleration, which a real machine cannot know. With it removed (`inertia_feedforward: 0`) on R4:

| Case (fresh / aged) | R4 (C1) | R4, no planned feedforward |
|---|---|---|
| Fast reversal | 8.0% / 12.1% | 9.7% / 13.6% |
| Full stroke | 10.7% / 11.5% | 11.2% / 11.9% |
| Paired heavy / asymmetric | 0.11% / 0.10% | 0.22% / 0.22% |

The honest cost is about 1.5 points on fast reversal and nothing material elsewhere. Any hardware-intended controller should use the right-hand column as its baseline.

## Bank-on-bus hardware checks

| Check | Result |
|---|---|
| Worst cell voltage (max bank 53.7 V, ×1.05 assumed imbalance) | 2.82 V vs 3.0 V rated: pass |
| Worst cell at the 57 V trip | 2.99 V: pass with almost no margin; a balancing design is needed before relying on it |
| Bank RMS current over one set | 14.2 A (aged fast reversal) vs 11.7 A continuous rating. The 18 s set only warms the cells to 29 °C. |
| Fast reversal repeated back to back | 47 °C fresh / **70 °C aged** vs 65 °C case maximum. This needs a bank duty limit or cooling for continuous fast work. |
| Supply peak current | 9.6 A, at the constant-current limit |
| Reverse blocking | about 0.5 W at 5 mΩ (assumed; no part selected) |
| Pre-charge at the supply limit | 27 s fresh / 17 s aged; 6.8 kJ bank energy; a fallback resistor needs at least 5.4 Ω and full-energy pulse rating |

## What remains

- **Owner decisions** (unchanged): motor/bus class for fast motion, and the endurance envelope.
- **Power-path design:** verify the EPP-500-54 overload mode into a capacitive load; select the ideal-diode and pre-charge parts; design cell balancing, fusing, a service disconnect and bank wiring. Add these to the electrical definition and cost allowances. The 57 V trip leaves almost no worst-cell margin.
- **Supervisor:** add dump-path fault detection independent of overvoltage, and a bank thermal or duty limit.
- **Unchanged from R3:** inverted-torque voltage controllability, 1% release-imbalance bar rotation, electrical frequency over 700 Hz in fast cases, low Km and warm-room failures, and the physical items in the [R2 review](r2-review.md).
