# Motor study review

2026-11-04. **Decision: PROPOSE a motor specification, not a part. R4 keeps the RO100 until the owner decides.**
Evidence: [motor study](../../reports/motor_study.md) (`make motor-study`) and the full R4 suite with the
Kollmorgen TBM2G-11526D at 6:1 ([r4m candidate](../../reports/r4m_candidate.md), `make r4m-candidate`).
Candidate data and conversions: `data/motor_candidates.yaml`.

## Question

With the RO100 at a 52 V bus, no belt ratio passes heavy (needs at least 5:1 at 50 A) and fast motion (needs
about 4:1) together, and endurance is Km-limited ([fast-motion review](fast-motion-review.md), [R4 review](r4-review.md)).
Does a different motor remove both problems, and what does it have to be?

## Result

| Motor (best ratio) | Km | Pole pairs | Fails (of 12) | Endurance winding °C | Fast reversal fresh / aged | Fast electrical Hz | Price |
|---|---:|---:|---:|---:|---|---:|---|
| RO100 KV55, 5:1 (R4) | 0.53 | 21 | 6 | 129 | 8.0% / 12.1% | 800 | not sourced |
| **TBM2G-11526D, 6:1** | **0.80** | **10** | **3** | **74** | **1.9% / 6.3%** | **480** | CHF 1,094 |
| RO100 rewound to KV80 (hypothetical), 6:1 | 0.53 | 21 | 6 | 127 | 3.7% / trip | 1,017 | — |
| T-Motor U13 II KV65, 6:1 | 0.54 | 21 | 6 | 128 | 5.1% / trip | 1,031 | $380 |
| T-Motor U15 II KV80, 6.5:1 (does not fit) | 0.92 | 21 | 4 | 58 | 46% / trip | 1,133 | $690 |

Full R4 suite with the TBM2G at 6:1: **5 of 54 cases fail (R4: 8)**, numerical verification passes, the support
screen passes 16 of 16 rows (R4: 8), and the low-Km and warm-room sensitivities no longer derate.

1. **Km about 0.8 is needed.** Higher Kv alone (the rewound RO100) allows 6:1 but leaves endurance in derate.
2. **Pole count matters.** Every 21-pole-pair motor runs fast reversal past the 700 Hz screen at 6:1.
3. **Rotor inertia matters.** The U15's estimated inertia (about 12× the TBM2G's, reflected) makes fast reversal fail.
4. **The bank becomes the limit.** Aged fast reversal bottoms 0.9 V above the 30 V trip with the TBM2G at 6:1 and
   trips without the planned feedforward (which hardware cannot implement). Bank ripple rises from 14.2 to 16.7 A RMS
   (rating 11.7 A); continuous repetition would take aged cells to about 87 °C (case limit 65 °C).
5. **Still failing with the TBM2G:** aged fast-reversal tracking (6.3%), full-stroke overshoot (16.6%, the same at
   every ratio, so probably the C1 end zone), and the inverted-torque fault's voltage-controllability check.

**Km sweep** (TBM2G at 6:1, resistance scaled; Kt, speed, inertia and poles unchanged):

| Km | Endurance winding °C | Aged fast reversal |
|---:|---:|---|
| 0.80 | 74 | 6.3%, no trip |
| 0.75 | 82 | 14.0%, undervoltage trip |
| 0.70 | 91 | 30.2%, trip |
| 0.65 | 103 | 43.0%, trip |
| 0.60 | 119 (derate at 120) | 48.3%, trip |

Endurance tracking passes down to 0.6 with no margin; the weak heat path adds about 30 °C, so 0.7 is the thermal minimum.
With the current bank, aged fast reversal needs 0.8: lower Km means more copper loss drawn from the aged bank.

## Proposed motor specification

Km at least 0.8 N·m/√W (0.7 acceptable only if the bank margin is fixed separately); 12 pole pairs or fewer; Kv about 70–75 rpm/V; at least 9 N·m
peak at 80 A phase peak; rotor inertia at most 5 × 10⁻⁴ kg·m²; OD at most 115 mm and axial length at most 45 mm;
stator bonded into an aluminium carrier. The TBM2G meets it at about CHF 1,094 per motor, which puts two motors
alone above the $500 retail hypothesis (DESIGN.md Gate C). Draft requests for a cheaper part:
[CubeMars](../rfq/cubemars-custom-winding-request.md), [SEA MOTION](../rfq/sea-motion-custom-motor-request.md),
[Exmek](../rfq/exmek-custom-motor-request.md). None is sent.

## Limitations

- The TBM2G and drone motors keep the RO100's unmeasured heat path (0.28 K/W winding to housing); weak-path
  variants (0.7 K/W) bound it for the TBM2G (endurance 105 °C) and the U13 (131 °C).
- Model Kt does not fall with winding temperature (the TBM2G's hot Kt is about 11% lower). Drive current limits
  are converted assuming the ODrive limit is a phase amplitude (80 A = 69.3 A DC-equivalent).
- Drone-motor values are first-order conversions of Kv, internal resistance (line-line assumed) and propeller
  test torque, with estimated inertia; they are open-frame motors rated with propeller cooling.
- Ratio variants keep the R2 drum inertia; 6:1 pulleys, the housed TBM2G (about 128 × 44 mm, 1.43 kg) and its
  mass are not checked against the CAD or the ADR-003 envelope. That check comes next.
- The 100 A variant at 5:1 tracks paired heavy worse than 69.3 A (8.8% vs 1.9%, 37% overshoot); not explained.

## Next

1. Owner decision on the motor route: TBM2G-class at its price, or a quoted custom part to the specification.
2. CAD fit check with the TBM2G and 6:1 pulleys; rerun the inertia, belt, bearing and support screens.
3. Bank margin in aged fast reversal: a power-aware current limit study before any bank change.
4. Send the supplier requests once the minimum Km is filled in. See the [bench-prototype path](bench-prototype-path.md).
