# Motor study (R4)

Fingerprint: `5ed63b752a580e2ee5b300dc11107765082c530686ba8509566a9afee41f5b85`

**Study only. The R4 candidate keeps the RO100.** With the RO100 at a 52 V bus no belt ratio passes heavy (needs at least 5:1 at 50 A) and fast motion (needs about 4:1) together, and endurance is Km-limited. This study puts a candidate motor with a higher Km and a lower back-EMF per unit torque, the Kollmorgen TBM2G-11526D (data/motor_candidates.yaml), into the full R4 plant and sweeps the ratio, the drive current limit and the motor heat path.

## Variants at a glance

| Variant | Motor | Ratio | Current limit A | Motor / drum torque limit N·m | Model no-load drum rpm at 52 V | Reflected motor inertia kg·m² | Winding–housing K/W |
|---|---|---:|---:|---:|---:|---:|---:|
| r4_ro100 | ro100_lite | 5 | 50 | 10.0 / 50 | 387 | 0.0132 | 0.28 |
| tbm_5 | tbm2g_11526d | 5 | 69.3 | 9.2 / 46 | 586 | 0.0089 | 0.28 |
| tbm_5_100a | tbm2g_11526d | 5 | 86.6 | 11.5 / 57 | 586 | 0.0089 | 0.28 |
| tbm_5.5 | tbm2g_11526d | 5.5 | 69.3 | 9.2 / 50 | 532 | 0.0107 | 0.28 |
| tbm_6 | tbm2g_11526d | 6 | 69.3 | 9.2 / 55 | 488 | 0.0128 | 0.28 |
| tbm_5.5_weak_path | tbm2g_11526d | 5.5 | 69.3 | 9.2 / 50 | 532 | 0.0107 | 0.70 |
| tbm_6_weak_path | tbm2g_11526d | 6 | 69.3 | 9.2 / 55 | 488 | 0.0128 | 0.70 |

## Tracking, r2_fresh bank

| Variant | single_fast_full | single_stroke_full | single_heavy_full | paired_heavy_full | single_slow_full | single_endurance_full |
|---|---:|---:|---:|---:|---:|---:|
| r4_ro100 | 8.0% ✗ | 10.7% ✗ | 0.1% | 0.1% | 0.1% | 21.1% ✗ |
| tbm_5 | 0.4% | 1.0% ✗ | 0.1% | 1.9% ✗ | 0.1% | 0.1% |
| tbm_5_100a | 0.4% | 1.0% ✗ | 0.1% | 8.8% ✗ | 0.1% | 0.1% |
| tbm_5.5 | 1.1% | 1.0% ✗ | 0.1% | 0.6% | 0.1% | 0.1% |
| tbm_6 | 1.9% | 1.1% ✗ | 0.1% | 0.1% | 0.1% | 0.1% |
| tbm_5.5_weak_path | 1.1% | 1.0% ✗ | 0.1% | 0.8% | 0.1% | 0.1% |
| tbm_6_weak_path | 1.9% | 1.1% ✗ | 0.1% | 0.1% | 0.1% | 0.1% |

## Tracking, r2_aged bank

| Variant | single_fast_full | single_stroke_full | single_heavy_full | paired_heavy_full | single_slow_full | single_endurance_full |
|---|---:|---:|---:|---:|---:|---:|
| r4_ro100 | 12.1% ✗ | 11.5% ✗ | 0.1% | 0.1% | 0.1% | 21.2% ✗ |
| tbm_5 | 79.6% trip ✗ | 1.0% ✗ | 0.1% | 1.3% ✗ | 0.1% | 0.1% |
| tbm_5_100a | 79.6% trip ✗ | 1.0% ✗ | 0.1% | 8.7% ✗ | 0.1% | 0.1% |
| tbm_5.5 | 61.8% trip ✗ | 1.0% ✗ | 0.1% | 1.0% | 0.1% | 0.1% |
| tbm_6 | 6.3% ✗ | 1.1% ✗ | 0.1% | 0.1% | 0.1% | 0.1% |
| tbm_5.5_weak_path | 61.8% trip ✗ | 1.0% ✗ | 0.1% | 0.8% | 0.1% | 0.1% |
| tbm_6_weak_path | 6.3% ✗ | 1.1% ✗ | 0.1% | 0.1% | 0.1% | 0.1% |

Cells: settled tracking RMS fraction of the worst unit; `trip` marks a latched protective trip; ✗ marks any failed comparison (listed below and in `motor_study.json`).

## Limits reached, unit 0

| Variant | Bank | Case | Voltage-limited time | Max current A | Max winding °C | Max electrical Hz | Min bus V | Failed checks |
|---|---|---|---:|---:|---:|---:|---:|---|
| r4_ro100 | r2_fresh | single_fast_full | 40% | 43.2 | 63.2 | 800 | 44.3 | proposed tracking RMS; recommended electrical frequency |
| r4_ro100 | r2_fresh | single_stroke_full | 30% | 26.9 | 36.8 | 757 | 50.1 | proposed normal overshoot; proposed tracking RMS; recommended electrical frequency |
| r4_ro100 | r2_fresh | single_heavy_full | 0% | 44.6 | 105.6 | 417 | 47.2 | — |
| r4_ro100 | r2_fresh | paired_heavy_full | 0% | 44.6 | 105.6 | 418 | 47.2 | — |
| r4_ro100 | r2_fresh | single_slow_full | 0% | 35.6 | 104.6 | 104 | 50.4 | — |
| r4_ro100 | r2_fresh | single_endurance_full | 0% | 44.7 | 128.5 | 631 | 45.7 | proposed normal overshoot; proposed tracking RMS |
| r4_ro100 | r2_aged | single_fast_full | 51% | 44.3 | 63.2 | 805 | 33.3 | proposed normal overshoot; proposed tracking RMS; recommended electrical frequency |
| r4_ro100 | r2_aged | single_stroke_full | 31% | 26.9 | 36.8 | 758 | 48.6 | proposed normal overshoot; proposed tracking RMS; recommended electrical frequency |
| r4_ro100 | r2_aged | single_heavy_full | 0% | 44.6 | 105.6 | 417 | 42.1 | — |
| r4_ro100 | r2_aged | paired_heavy_full | 0% | 44.6 | 105.6 | 418 | 42.1 | — |
| r4_ro100 | r2_aged | single_slow_full | 0% | 35.6 | 104.6 | 104 | 50.3 | — |
| r4_ro100 | r2_aged | single_endurance_full | 0% | 44.7 | 128.5 | 632 | 37.0 | proposed normal overshoot; proposed tracking RMS |
| tbm_5 | r2_fresh | single_fast_full | 7% | 61.0 | 41.6 | 400 | 41.6 | — |
| tbm_5 | r2_fresh | single_stroke_full | 0% | 28.5 | 30.9 | 404 | 50.5 | proposed normal overshoot |
| tbm_5 | r2_fresh | single_heavy_full | 0% | 67.3 | 57.0 | 199 | 50.2 | — |
| tbm_5 | r2_fresh | paired_heavy_full | 0% | 69.2 | 56.9 | 199 | 50.2 | proposed normal overshoot |
| tbm_5 | r2_fresh | single_slow_full | 0% | 53.8 | 56.3 | 50 | 51.1 | — |
| tbm_5 | r2_fresh | single_endurance_full | 0% | 67.5 | 97.7 | 159 | 49.7 | — |
| tbm_5 | r2_aged | single_fast_full | 7% | 61.8 | 31.9 | 402 | 30.3 | latched protective trip during normal operation; proposed tracking RMS |
| tbm_5 | r2_aged | single_stroke_full | 0% | 28.5 | 30.9 | 404 | 49.3 | proposed normal overshoot |
| tbm_5 | r2_aged | single_heavy_full | 0% | 67.3 | 57.0 | 199 | 49.2 | — |
| tbm_5 | r2_aged | paired_heavy_full | 0% | 69.2 | 56.9 | 199 | 49.0 | proposed normal overshoot |
| tbm_5 | r2_aged | single_slow_full | 0% | 53.8 | 56.3 | 50 | 51.0 | — |
| tbm_5 | r2_aged | single_endurance_full | 0% | 67.5 | 98.4 | 159 | 47.1 | — |
| tbm_5_100a | r2_fresh | single_fast_full | 7% | 61.0 | 41.6 | 400 | 41.6 | — |
| tbm_5_100a | r2_fresh | single_stroke_full | 0% | 28.5 | 30.9 | 404 | 50.5 | proposed normal overshoot |
| tbm_5_100a | r2_fresh | single_heavy_full | 0% | 67.3 | 57.0 | 199 | 50.2 | — |
| tbm_5_100a | r2_fresh | paired_heavy_full | 0% | 85.5 | 57.0 | 199 | 49.2 | proposed normal overshoot; proposed tracking RMS |
| tbm_5_100a | r2_fresh | single_slow_full | 0% | 53.8 | 56.3 | 50 | 51.1 | — |
| tbm_5_100a | r2_fresh | single_endurance_full | 0% | 67.5 | 97.7 | 159 | 49.7 | — |
| tbm_5_100a | r2_aged | single_fast_full | 7% | 61.8 | 31.9 | 402 | 30.3 | latched protective trip during normal operation; proposed tracking RMS |
| tbm_5_100a | r2_aged | single_stroke_full | 0% | 28.5 | 30.9 | 404 | 49.3 | proposed normal overshoot |
| tbm_5_100a | r2_aged | single_heavy_full | 0% | 67.3 | 57.0 | 199 | 49.2 | — |
| tbm_5_100a | r2_aged | paired_heavy_full | 0% | 85.6 | 57.0 | 199 | 47.0 | proposed normal overshoot; proposed tracking RMS |
| tbm_5_100a | r2_aged | single_slow_full | 0% | 53.8 | 56.3 | 50 | 51.0 | — |
| tbm_5_100a | r2_aged | single_endurance_full | 0% | 67.5 | 98.4 | 159 | 47.1 | — |
| tbm_5.5 | r2_fresh | single_fast_full | 12% | 56.6 | 39.0 | 441 | 42.7 | — |
| tbm_5.5 | r2_fresh | single_stroke_full | 0% | 26.6 | 30.1 | 443 | 50.5 | proposed normal overshoot |
| tbm_5.5 | r2_fresh | single_heavy_full | 0% | 61.2 | 51.3 | 219 | 50.4 | — |
| tbm_5.5 | r2_fresh | paired_heavy_full | 0% | 64.4 | 51.3 | 219 | 50.3 | — |
| tbm_5.5 | r2_fresh | single_slow_full | 0% | 48.9 | 50.6 | 55 | 51.1 | — |
| tbm_5.5 | r2_fresh | single_endurance_full | 0% | 61.4 | 84.0 | 175 | 50.1 | — |
| tbm_5.5 | r2_aged | single_fast_full | 14% | 57.6 | 34.2 | 445 | 30.2 | latched protective trip during normal operation; proposed tracking RMS |
| tbm_5.5 | r2_aged | single_stroke_full | 0% | 26.6 | 30.1 | 443 | 49.4 | proposed normal overshoot |
| tbm_5.5 | r2_aged | single_heavy_full | 0% | 61.2 | 51.3 | 219 | 49.7 | — |
| tbm_5.5 | r2_aged | paired_heavy_full | 0% | 65.0 | 51.3 | 219 | 49.4 | — |
| tbm_5.5 | r2_aged | single_slow_full | 0% | 48.9 | 50.6 | 55 | 51.0 | — |
| tbm_5.5 | r2_aged | single_endurance_full | 0% | 61.4 | 84.6 | 175 | 47.8 | — |
| tbm_6 | r2_fresh | single_fast_full | 16% | 53.0 | 37.0 | 482 | 43.6 | — |
| tbm_6 | r2_fresh | single_stroke_full | 0% | 25.1 | 29.5 | 481 | 50.5 | proposed normal overshoot |
| tbm_6 | r2_fresh | single_heavy_full | 0% | 56.2 | 47.0 | 239 | 50.4 | — |
| tbm_6 | r2_fresh | paired_heavy_full | 0% | 56.2 | 47.0 | 239 | 50.4 | — |
| tbm_6 | r2_fresh | single_slow_full | 0% | 44.9 | 46.4 | 60 | 51.2 | — |
| tbm_6 | r2_fresh | single_endurance_full | 0% | 56.3 | 74.2 | 191 | 50.2 | — |
| tbm_6 | r2_aged | single_fast_full | 28% | 54.1 | 37.0 | 490 | 30.9 | proposed tracking RMS |
| tbm_6 | r2_aged | single_stroke_full | 0% | 25.1 | 29.5 | 481 | 49.5 | proposed normal overshoot |
| tbm_6 | r2_aged | single_heavy_full | 0% | 56.2 | 47.0 | 239 | 50.0 | — |
| tbm_6 | r2_aged | paired_heavy_full | 0% | 56.2 | 47.0 | 239 | 50.0 | — |
| tbm_6 | r2_aged | single_slow_full | 0% | 44.9 | 46.4 | 60 | 51.1 | — |
| tbm_6 | r2_aged | single_endurance_full | 0% | 56.3 | 74.8 | 191 | 48.3 | — |
| tbm_5.5_weak_path | r2_fresh | single_fast_full | 12% | 56.6 | 42.0 | 441 | 42.7 | — |
| tbm_5.5_weak_path | r2_fresh | single_stroke_full | 0% | 26.6 | 31.1 | 443 | 50.5 | proposed normal overshoot |
| tbm_5.5_weak_path | r2_fresh | single_heavy_full | 0% | 61.2 | 61.7 | 219 | 50.3 | — |
| tbm_5.5_weak_path | r2_fresh | paired_heavy_full | 0% | 65.9 | 61.7 | 219 | 50.2 | — |
| tbm_5.5_weak_path | r2_fresh | single_slow_full | 0% | 48.9 | 65.8 | 55 | 51.1 | — |
| tbm_5.5_weak_path | r2_fresh | single_endurance_full | 0% | 61.4 | 121.9 | 175 | 49.9 | — |
| tbm_5.5_weak_path | r2_aged | single_fast_full | 14% | 57.6 | 35.5 | 445 | 30.2 | latched protective trip during normal operation; proposed tracking RMS |
| tbm_5.5_weak_path | r2_aged | single_stroke_full | 0% | 26.6 | 31.1 | 443 | 49.4 | proposed normal overshoot |
| tbm_5.5_weak_path | r2_aged | single_heavy_full | 0% | 61.2 | 61.7 | 219 | 49.6 | — |
| tbm_5.5_weak_path | r2_aged | paired_heavy_full | 0% | 66.2 | 61.7 | 219 | 49.2 | — |
| tbm_5.5_weak_path | r2_aged | single_slow_full | 0% | 48.9 | 65.8 | 55 | 51.0 | — |
| tbm_5.5_weak_path | r2_aged | single_endurance_full | 0% | 61.4 | 122.6 | 175 | 47.5 | — |
| tbm_6_weak_path | r2_fresh | single_fast_full | 16% | 53.0 | 39.4 | 482 | 43.6 | — |
| tbm_6_weak_path | r2_fresh | single_stroke_full | 0% | 25.1 | 30.3 | 481 | 50.5 | proposed normal overshoot |
| tbm_6_weak_path | r2_fresh | single_heavy_full | 0% | 56.2 | 55.5 | 239 | 50.4 | — |
| tbm_6_weak_path | r2_fresh | paired_heavy_full | 0% | 56.2 | 55.5 | 239 | 50.4 | — |
| tbm_6_weak_path | r2_fresh | single_slow_full | 0% | 44.9 | 58.8 | 60 | 51.2 | — |
| tbm_6_weak_path | r2_fresh | single_endurance_full | 0% | 56.3 | 104.0 | 191 | 50.1 | — |
| tbm_6_weak_path | r2_aged | single_fast_full | 28% | 54.1 | 39.5 | 490 | 30.8 | proposed tracking RMS |
| tbm_6_weak_path | r2_aged | single_stroke_full | 0% | 25.1 | 30.3 | 481 | 49.5 | proposed normal overshoot |
| tbm_6_weak_path | r2_aged | single_heavy_full | 0% | 56.2 | 55.5 | 239 | 49.9 | — |
| tbm_6_weak_path | r2_aged | paired_heavy_full | 0% | 56.2 | 55.5 | 239 | 49.9 | — |
| tbm_6_weak_path | r2_aged | single_slow_full | 0% | 44.9 | 58.8 | 60 | 51.1 | — |
| tbm_6_weak_path | r2_aged | single_endurance_full | 0% | 56.3 | 104.7 | 191 | 48.1 | — |

## Variants

- **r4_ro100**: R4 candidate (RO100, 5:1, 50 A)
- **tbm_5**: motor: tbm2g_11526d; control: {'current_limit_a': 69.3}
- **tbm_5_100a**: motor: tbm2g_11526d; control: {'current_limit_a': 86.6}
- **tbm_5.5**: motor: tbm2g_11526d; reference: {'ratio': 5.5}; control: {'current_limit_a': 69.3}
- **tbm_6**: motor: tbm2g_11526d; reference: {'ratio': 6.0}; control: {'current_limit_a': 69.3}
- **tbm_5.5_weak_path**: motor: tbm2g_11526d; reference: {'ratio': 5.5}; control: {'current_limit_a': 69.3}; thermal_scale: {'winding_to_housing_k_w': 2.5}
- **tbm_6_weak_path**: motor: tbm2g_11526d; reference: {'ratio': 6.0}; control: {'current_limit_a': 69.3}; thermal_scale: {'winding_to_housing_k_w': 2.5}

## Notes

- The plant is the R4 candidate (bank on the drive bus, R3 heat path, controller C1, 56 V trip, gate-rule dump monitor). Only the listed keys change.
- Ratio variants keep the R2 CAD drum inertia and do not rerun belt, bearing or support screens; reflected motor inertia scales with the ratio squared. 5.5:1 and 6:1 would need new pulleys (for example 22/121 and 20/120 teeth).
- The TBM2G keeps the RO100's heat-path values (winding-to-housing 0.28 K/W, winding 48.3 J/K, housing 193.2 J/K) unless a variant scales them. A frameless stator bonded into an aluminium carrier is assumed to be at least as good as the RO100 estimate; this is not measured. The heavier TBM2G (1.43 kg) would add heat capacity that is not credited.
- Kt does not fall with winding temperature in the model; the hot TBM2G Kt is about 11% below the cold value used.
- The 1.4 kg and 128 mm housed OD of the TBM2G are not checked against the R2 CAD or the ADR-003 envelope.

Reproduce: `make motor-study`.
