# Fast-motion study (R3 + C1)

Fingerprint: `8537637be565ab66212148efd63a481bbe39cf180d361a328c1f80c90d961bf8`

**Study only. The reference controller and the R3/C1 candidate are unchanged.** The controller study attributed the remaining fast-reversal error to force-loop bandwidth. Trace analysis contradicts that: sensor and torque-loop lags contribute a few newtons, while the commanded current sits on the back-EMF/bus voltage bound for about half of the set. This study attributes the error and tests the voltage, energy and feedforward levers separately.

## Tracking, r2_fresh bank

| Variant | single_fast_full | single_stroke_full | single_heavy_full | paired_heavy_full | single_slow_full | single_endurance_full |
|---|---:|---:|---:|---:|---:|---:|
| r3c | 11.4% ✗ | 14.1% ✗ | 0.1% | 0.1% | 0.1% | 21.4% ✗ |
| measured_accel | 10.5% ✗ | 14.5% ✗ | 0.1% | 1.2% | 0.1% | 21.4% ✗ |
| no_feedforward | 13.5% ✗ | 14.6% ✗ | 0.2% | 0.2% | 0.1% | 21.3% ✗ |
| esr_0.1 | 8.8% ✗ | 13.7% ✗ | 0.1% | 0.1% | 0.1% | 21.3% ✗ |
| ratio_4.5 | 16.6% trip ✗ | 1.1% ✗ | 4.5% ✗ | 4.5% ✗ | 1.4% ✗ | 28.9% ✗ |
| bidirectional | 8.0% ✗ | 10.7% ✗ | 0.1% | 0.1% | 0.1% | 21.1% ✗ |
| bidirectional_ratio_4.5 | 6.9% ✗ | 1.0% ✗ | 4.5% ✗ | 4.5% ✗ | 1.4% ✗ | 28.7% ✗ |
| bidirectional_ratio_4 | 6.8% ✗ | 1.0% ✗ | 13.9% ✗ | 13.7% ✗ | 10.9% ✗ | 36.1% ✗ |
| bidirectional_ratio_4.5_60a | 6.9% ✗ | 1.0% ✗ | 3.0% ✗ | 3.1% ✗ | 0.2% | 28.3% ✗ |

Cells: settled tracking RMS fraction of the worst unit; `trip` marks a latched protective trip; ✗ marks any failed comparison (details in `fast_motion_study.json`).

## Tracking, r2_aged bank

| Variant | single_fast_full | single_stroke_full | single_heavy_full | paired_heavy_full | single_slow_full | single_endurance_full |
|---|---:|---:|---:|---:|---:|---:|
| r3c | 62.0% trip ✗ | 14.5% ✗ | 0.1% | 0.1% | 0.1% | 21.4% ✗ |
| measured_accel | 61.9% trip ✗ | 14.8% ✗ | 0.1% | 1.3% | 0.1% | 21.4% ✗ |
| no_feedforward | 62.3% trip ✗ | 15.0% ✗ | 0.2% | 0.2% | 0.1% | 21.4% ✗ |
| esr_0.1 | 11.7% ✗ | 13.9% ✗ | 0.1% | 0.1% | 0.1% | 21.3% ✗ |
| ratio_4.5 | 75.9% trip ✗ | 1.8% ✗ | 50.0% trip ✗ | 47.1% trip ✗ | 1.4% ✗ | 98.0% trip ✗ |
| bidirectional | 12.1% ✗ | 11.5% ✗ | 0.1% | 0.1% | 0.1% | 21.2% ✗ |
| bidirectional_ratio_4.5 | 49.9% trip ✗ | 1.1% ✗ | 26.7% trip ✗ | 4.6% trip ✗ | 1.4% ✗ | 97.9% trip ✗ |
| bidirectional_ratio_4 | 74.2% trip ✗ | 1.0% ✗ | 49.9% trip ✗ | 48.4% trip ✗ | 10.9% ✗ | 98.0% trip ✗ |
| bidirectional_ratio_4.5_60a | 49.9% trip ✗ | 1.1% ✗ | 28.8% trip ✗ | 26.1% trip ✗ | 0.2% | 97.9% trip ✗ |

Cells: settled tracking RMS fraction of the worst unit; `trip` marks a latched protective trip; ✗ marks any failed comparison (details in `fast_motion_study.json`).

## Voltage saturation and energy, unit 0

| Variant | Bank | Case | Voltage-limited time | Voltage-limited error share | Min bus V | Mean dump W | Max winding °C | Max electrical Hz |
|---|---|---|---:|---:|---:|---:|---:|---:|
| r3c | r2_fresh | single_fast_full | 52% | 85% | 34.8 | 317 | 63.1 | 774 |
| r3c | r2_fresh | single_stroke_full | 32% | 78% | 49.3 | 143 | 36.9 | 743 |
| r3c | r2_aged | single_fast_full | 30% | 2% | 30.2 | 170 | 49.8 | 774 |
| r3c | r2_aged | single_stroke_full | 32% | 78% | 47.7 | 143 | 36.9 | 743 |
| measured_accel | r2_fresh | single_fast_full | 52% | 86% | 35.6 | 306 | 62.9 | 774 |
| measured_accel | r2_fresh | single_stroke_full | 32% | 73% | 49.3 | 143 | 37.8 | 743 |
| measured_accel | r2_aged | single_fast_full | 30% | 2% | 30.2 | 165 | 49.8 | 774 |
| measured_accel | r2_aged | single_stroke_full | 32% | 74% | 47.7 | 143 | 37.8 | 744 |
| no_feedforward | r2_fresh | single_fast_full | 57% | 85% | 34.3 | 337 | 63.1 | 776 |
| no_feedforward | r2_fresh | single_stroke_full | 32% | 75% | 49.2 | 144 | 36.9 | 743 |
| no_feedforward | r2_aged | single_fast_full | 32% | 3% | 30.1 | 181 | 49.7 | 776 |
| no_feedforward | r2_aged | single_stroke_full | 33% | 76% | 47.6 | 144 | 36.9 | 744 |
| esr_0.1 | r2_fresh | single_fast_full | 46% | 87% | 41.5 | 320 | 63.1 | 773 |
| esr_0.1 | r2_fresh | single_stroke_full | 31% | 78% | 50.1 | 143 | 36.9 | 743 |
| esr_0.1 | r2_aged | single_fast_full | 53% | 89% | 34.2 | 317 | 62.9 | 773 |
| esr_0.1 | r2_aged | single_stroke_full | 32% | 78% | 49.6 | 143 | 36.9 | 744 |
| ratio_4.5 | r2_fresh | single_fast_full | 42% | 31% | 30.4 | 294 | 71.7 | 766 |
| ratio_4.5 | r2_fresh | single_stroke_full | 12% | 46% | 49.2 | 121 | 39.2 | 735 |
| ratio_4.5 | r2_aged | single_fast_full | 15% | 1% | 30.5 | 118 | 46.7 | 771 |
| ratio_4.5 | r2_aged | single_stroke_full | 18% | 72% | 46.9 | 121 | 39.2 | 735 |
| bidirectional | r2_fresh | single_fast_full | 40% | 79% | 44.3 | 49 | 63.2 | 800 |
| bidirectional | r2_fresh | single_stroke_full | 30% | 79% | 50.1 | 51 | 36.8 | 757 |
| bidirectional | r2_aged | single_fast_full | 51% | 78% | 33.3 | 71 | 63.2 | 805 |
| bidirectional | r2_aged | single_stroke_full | 31% | 79% | 48.6 | 84 | 36.8 | 758 |
| bidirectional_ratio_4.5 | r2_fresh | single_fast_full | 29% | 75% | 42.3 | 26 | 72.4 | 769 |
| bidirectional_ratio_4.5 | r2_fresh | single_stroke_full | 2% | 3% | 50.3 | 33 | 39.2 | 752 |
| bidirectional_ratio_4.5 | r2_aged | single_fast_full | 27% | 3% | 30.1 | 44 | 61.8 | 796 |
| bidirectional_ratio_4.5 | r2_aged | single_stroke_full | 8% | 17% | 48.3 | 64 | 39.2 | 752 |
| bidirectional_ratio_4 | r2_fresh | single_fast_full | 28% | 75% | 38.4 | 15 | 85.9 | 684 |
| bidirectional_ratio_4 | r2_fresh | single_stroke_full | 0% | 0% | 50.2 | 30 | 42.8 | 679 |
| bidirectional_ratio_4 | r2_aged | single_fast_full | 14% | 1% | 30.1 | 29 | 54.5 | 696 |
| bidirectional_ratio_4 | r2_aged | single_stroke_full | 0% | 0% | 48.1 | 60 | 42.8 | 679 |
| bidirectional_ratio_4.5_60a | r2_fresh | single_fast_full | 29% | 75% | 42.3 | 26 | 72.4 | 769 |
| bidirectional_ratio_4.5_60a | r2_fresh | single_stroke_full | 2% | 3% | 50.3 | 33 | 39.2 | 752 |
| bidirectional_ratio_4.5_60a | r2_aged | single_fast_full | 27% | 3% | 30.1 | 44 | 61.8 | 796 |
| bidirectional_ratio_4.5_60a | r2_aged | single_stroke_full | 8% | 17% | 48.3 | 64 | 39.2 | 752 |

## Variants

- **r3c**: R3 + C1
- **measured_accel**: control: {'acceleration_blend': 1.0}
- **no_feedforward**: control: {'inertia_feedforward': 0}
- **esr_0.1**: sensitivity: {'esr_scale': 0.1}
- **ratio_4.5**: reference: {'ratio': 4.5}
- **bidirectional**: topology: bidirectional
- **bidirectional_ratio_4.5**: topology: bidirectional; reference: {'ratio': 4.5}
- **bidirectional_ratio_4**: topology: bidirectional; reference: {'ratio': 4.0}
- **bidirectional_ratio_4.5_60a**: topology: bidirectional; reference: {'ratio': 4.5}; control: {'current_limit_a': 60}

## Notes

- Ratio variants keep the R2 CAD drum inertia and do not rerun the belt, bearing or support screens; the motor's reflected inertia scales with the ratio squared.
- The bidirectional topology puts the 20-cell bank directly on the drive bus through its ESR, keeps the one-way supply and the 54.35–54.5 V dump. Pre-charge, inrush, bank ripple current, supply reverse blocking and cell balancing are not modelled.
- The 60 A variant uses the motor's whole peak-torque current. Motor and drive heating at that current are modelled; drive current rating with the proposed airflow is not verified.
- Cells with a trip report little voltage-limited share because a tripped drive is disabled, not saturated.
- voltage-limited share is the fraction of squared tracking error that occurs while the requested current exceeds a back-EMF/bus bound tighter than the current limit. It is a diagnostic, not a pass/fail criterion.

Reproduce: `make fast-study`.
