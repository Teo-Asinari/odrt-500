# Motor study (R4)

Fingerprint: `96e9a618893bec6fef499ca2f866a16839980ef44905a475299836d17b6aa8e0`

**Study only. The R4 candidate keeps the RO100.** With the RO100 at a 52 V bus no belt ratio passes heavy (needs at least 5:1 at 50 A) and fast motion (needs about 4:1) together, and endurance is Km-limited. This study puts a candidate motor with a higher Km and a lower back-EMF per unit torque, the Kollmorgen TBM2G-11526D (data/motor_candidates.yaml), into the full R4 plant and sweeps the ratio, the drive current limit and the motor heat path.

## Variants at a glance

| Variant | Motor | Km | Ratio | Current limit A | Motor / drum torque limit N·m | Model no-load drum rpm at 52 V | Reflected motor inertia kg·m² | Winding–housing K/W |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| r4_ro100 | ro100_lite | 0.53 | 5 | 50 | 10.0 / 50 | 387 | 0.0132 | 0.28 |
| tbm_5 | tbm2g_11526d | 0.80 | 5 | 69.3 | 9.2 / 46 | 586 | 0.0089 | 0.28 |
| tbm_5_100a | tbm2g_11526d | 0.80 | 5 | 86.6 | 11.5 / 57 | 586 | 0.0089 | 0.28 |
| tbm_5.5 | tbm2g_11526d | 0.80 | 5.5 | 69.3 | 9.2 / 50 | 532 | 0.0107 | 0.28 |
| tbm_6 | tbm2g_11526d | 0.80 | 6 | 69.3 | 9.2 / 55 | 488 | 0.0128 | 0.28 |
| tbm_5.5_weak_path | tbm2g_11526d | 0.80 | 5.5 | 69.3 | 9.2 / 50 | 532 | 0.0107 | 0.70 |
| tbm_6_weak_path | tbm2g_11526d | 0.80 | 6 | 69.3 | 9.2 / 55 | 488 | 0.0128 | 0.70 |
| ro100kv80_5.5 | ro100_kv80_hypothetical | 0.53 | 5.5 | 66.7 | 9.2 / 50 | 512 | 0.0160 | 0.28 |
| ro100kv80_6 | ro100_kv80_hypothetical | 0.53 | 6 | 66.7 | 9.2 / 55 | 469 | 0.0190 | 0.28 |
| ro100kv80_6_weak_path | ro100_kv80_hypothetical | 0.53 | 6 | 66.7 | 9.2 / 55 | 469 | 0.0190 | 0.70 |
| u13kv65_5.5 | tmotor_u13ii_kv65 | 0.54 | 5.5 | 69.3 | 10.2 / 56 | 479 | 0.0281 | 0.28 |
| u13kv65_6 | tmotor_u13ii_kv65 | 0.54 | 6 | 69.3 | 10.2 / 61 | 439 | 0.0335 | 0.28 |
| u13kv65_5.5_weak_path | tmotor_u13ii_kv65 | 0.54 | 5.5 | 69.3 | 10.2 / 56 | 479 | 0.0281 | 0.70 |
| u15kv80_6.5 | tmotor_u15ii_kv80 | 0.92 | 6.5 | 69.3 | 8.3 / 54 | 499 | 0.1521 | 0.28 |
| tbm_6_km0.60 | tbm2g_11526d | 0.60 | 6 | 69.3 | 9.2 / 55 | 488 | 0.0128 | 0.28 |
| tbm_6_km0.65 | tbm2g_11526d | 0.65 | 6 | 69.3 | 9.2 / 55 | 488 | 0.0128 | 0.28 |
| tbm_6_km0.70 | tbm2g_11526d | 0.70 | 6 | 69.3 | 9.2 / 55 | 488 | 0.0128 | 0.28 |
| tbm_6_km0.75 | tbm2g_11526d | 0.75 | 6 | 69.3 | 9.2 / 55 | 488 | 0.0128 | 0.28 |

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
| ro100kv80_5.5 | 2.7% ✗ | 1.1% ✗ | 0.1% | 0.1% | 0.1% | 14.1% ✗ |
| ro100kv80_6 | 3.7% ✗ | 1.2% ✗ | 0.1% | 0.1% | 0.1% | 7.3% ✗ |
| ro100kv80_6_weak_path | 3.7% ✗ | 1.2% ✗ | 0.1% | 0.1% | 0.1% | 26.2% ✗ |
| u13kv65_5.5 | 3.9% ✗ | 1.5% ✗ | 0.1% | 0.1% | 0.1% | 11.9% ✗ |
| u13kv65_6 | 5.1% ✗ | 1.6% ✗ | 0.1% | 0.1% | 0.1% | 5.0% ✗ |
| u13kv65_5.5_weak_path | 4.0% ✗ | 1.5% ✗ | 0.1% | 0.1% | 0.1% | 30.6% ✗ |
| u15kv80_6.5 | 46.1% ✗ | 5.5% ✗ | 0.3% | 0.4% | 0.1% | 0.2% |
| tbm_6_km0.60 | 2.5% | 1.1% ✗ | 0.1% | 0.1% | 0.1% | 0.1% |
| tbm_6_km0.65 | 2.3% | 1.1% ✗ | 0.1% | 0.1% | 0.1% | 0.1% |
| tbm_6_km0.70 | 2.2% | 1.1% ✗ | 0.1% | 0.1% | 0.1% | 0.1% |
| tbm_6_km0.75 | 2.0% | 1.1% ✗ | 0.1% | 0.1% | 0.1% | 0.1% |

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
| ro100kv80_5.5 | 76.2% trip ✗ | 1.1% ✗ | 0.1% | 0.1% | 0.1% | 14.2% ✗ |
| ro100kv80_6 | 61.5% trip ✗ | 1.2% ✗ | 0.1% | 0.1% | 0.1% | 7.4% ✗ |
| ro100kv80_6_weak_path | 61.5% trip ✗ | 1.2% ✗ | 0.1% | 0.1% | 0.1% | 26.3% ✗ |
| u13kv65_5.5 | 79.1% trip ✗ | 1.5% ✗ | 0.1% | 0.1% | 0.1% | 12.0% ✗ |
| u13kv65_6 | 68.8% trip ✗ | 1.6% ✗ | 0.1% | 0.1% | 0.1% | 5.1% ✗ |
| u13kv65_5.5_weak_path | 79.1% trip ✗ | 1.5% ✗ | 0.1% | 0.1% | 0.1% | 30.6% ✗ |
| u15kv80_6.5 | 81.8% trip ✗ | 5.5% ✗ | 0.3% | 0.4% | 0.1% | 0.2% |
| tbm_6_km0.60 | 48.3% trip ✗ | 1.1% ✗ | 0.1% | 0.1% | 0.1% | 0.1% |
| tbm_6_km0.65 | 43.0% trip ✗ | 1.1% ✗ | 0.1% | 0.1% | 0.1% | 0.1% |
| tbm_6_km0.70 | 30.2% trip ✗ | 1.1% ✗ | 0.1% | 0.1% | 0.1% | 0.1% |
| tbm_6_km0.75 | 14.0% trip ✗ | 1.1% ✗ | 0.1% | 0.1% | 0.1% | 0.1% |

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
| ro100kv80_5.5 | r2_fresh | single_fast_full | 18% | 57.4 | 56.5 | 929 | 41.3 | recommended electrical frequency |
| ro100kv80_5.5 | r2_fresh | single_stroke_full | 0% | 27.4 | 34.9 | 921 | 50.4 | proposed normal overshoot; recommended electrical frequency |
| ro100kv80_5.5 | r2_fresh | single_heavy_full | 0% | 59.0 | 89.5 | 459 | 48.7 | — |
| ro100kv80_5.5 | r2_fresh | paired_heavy_full | 0% | 59.0 | 89.5 | 461 | 48.7 | — |
| ro100kv80_5.5 | r2_fresh | single_slow_full | 0% | 47.1 | 88.4 | 115 | 50.6 | — |
| ro100kv80_5.5 | r2_fresh | single_endurance_full | 0% | 59.2 | 127.5 | 863 | 45.1 | proposed normal overshoot; proposed tracking RMS; recommended electrical frequency |
| ro100kv80_5.5 | r2_aged | single_fast_full | 10% | 58.4 | 39.7 | 952 | 31.0 | latched protective trip during normal operation; proposed tracking RMS; recommended electrical frequency |
| ro100kv80_5.5 | r2_aged | single_stroke_full | 0% | 27.4 | 34.9 | 921 | 48.9 | proposed normal overshoot; recommended electrical frequency |
| ro100kv80_5.5 | r2_aged | single_heavy_full | 0% | 59.0 | 89.5 | 459 | 45.5 | — |
| ro100kv80_5.5 | r2_aged | paired_heavy_full | 0% | 59.0 | 89.5 | 461 | 45.5 | — |
| ro100kv80_5.5 | r2_aged | single_slow_full | 0% | 47.1 | 88.4 | 115 | 50.5 | — |
| ro100kv80_5.5 | r2_aged | single_endurance_full | 0% | 59.2 | 127.5 | 822 | 37.0 | proposed normal overshoot; proposed tracking RMS; recommended electrical frequency |
| ro100kv80_6 | r2_fresh | single_fast_full | 20% | 54.2 | 51.7 | 1017 | 42.5 | recommended electrical frequency |
| ro100kv80_6 | r2_fresh | single_stroke_full | 0% | 25.9 | 33.5 | 1002 | 50.4 | proposed normal overshoot; recommended electrical frequency |
| ro100kv80_6 | r2_fresh | single_heavy_full | 0% | 54.2 | 78.0 | 501 | 49.4 | — |
| ro100kv80_6 | r2_fresh | paired_heavy_full | 0% | 54.2 | 77.7 | 504 | 49.4 | — |
| ro100kv80_6 | r2_fresh | single_slow_full | 0% | 43.2 | 76.9 | 125 | 50.8 | — |
| ro100kv80_6 | r2_fresh | single_endurance_full | 0% | 54.4 | 127.3 | 839 | 45.7 | proposed normal overshoot; proposed tracking RMS; recommended electrical frequency |
| ro100kv80_6 | r2_aged | single_fast_full | 17% | 55.4 | 42.7 | 1072 | 30.8 | latched protective trip during normal operation; proposed normal overshoot; proposed tracking RMS; recommended electrical frequency |
| ro100kv80_6 | r2_aged | single_stroke_full | 0% | 25.9 | 33.5 | 1002 | 49.1 | proposed normal overshoot; recommended electrical frequency |
| ro100kv80_6 | r2_aged | single_heavy_full | 0% | 54.2 | 78.0 | 501 | 47.1 | — |
| ro100kv80_6 | r2_aged | paired_heavy_full | 0% | 54.2 | 77.7 | 504 | 47.1 | — |
| ro100kv80_6 | r2_aged | single_slow_full | 0% | 43.2 | 76.9 | 125 | 50.7 | — |
| ro100kv80_6 | r2_aged | single_endurance_full | 0% | 54.4 | 127.3 | 792 | 39.6 | proposed normal overshoot; proposed tracking RMS; recommended electrical frequency |
| ro100kv80_6_weak_path | r2_fresh | single_fast_full | 20% | 54.2 | 58.8 | 1018 | 42.4 | recommended electrical frequency |
| ro100kv80_6_weak_path | r2_fresh | single_stroke_full | 0% | 25.9 | 36.2 | 1002 | 50.4 | proposed normal overshoot; recommended electrical frequency |
| ro100kv80_6_weak_path | r2_fresh | single_heavy_full | 0% | 54.2 | 100.8 | 501 | 49.2 | — |
| ro100kv80_6_weak_path | r2_fresh | paired_heavy_full | 0% | 54.2 | 100.4 | 504 | 49.3 | — |
| ro100kv80_6_weak_path | r2_fresh | single_slow_full | 0% | 43.2 | 110.9 | 125 | 50.7 | — |
| ro100kv80_6_weak_path | r2_fresh | single_endurance_full | 0% | 54.4 | 130.4 | 935 | 47.0 | proposed normal overshoot; proposed tracking RMS; recommended electrical frequency |
| ro100kv80_6_weak_path | r2_aged | single_fast_full | 17% | 55.4 | 45.7 | 1073 | 30.9 | latched protective trip during normal operation; proposed normal overshoot; proposed tracking RMS; recommended electrical frequency |
| ro100kv80_6_weak_path | r2_aged | single_stroke_full | 0% | 25.9 | 36.2 | 1002 | 49.1 | proposed normal overshoot; recommended electrical frequency |
| ro100kv80_6_weak_path | r2_aged | single_heavy_full | 0% | 54.2 | 100.8 | 501 | 46.7 | — |
| ro100kv80_6_weak_path | r2_aged | paired_heavy_full | 0% | 54.2 | 100.4 | 504 | 46.7 | — |
| ro100kv80_6_weak_path | r2_aged | single_slow_full | 0% | 43.2 | 110.9 | 125 | 50.6 | — |
| ro100kv80_6_weak_path | r2_aged | single_endurance_full | 0% | 54.4 | 130.4 | 934 | 43.4 | proposed normal overshoot; proposed tracking RMS; recommended electrical frequency |
| u13kv65_5.5 | r2_fresh | single_fast_full | 20% | 59.6 | 56.1 | 948 | 41.1 | recommended electrical frequency |
| u13kv65_5.5 | r2_fresh | single_stroke_full | 0% | 28.5 | 34.5 | 919 | 50.4 | proposed normal overshoot; recommended electrical frequency |
| u13kv65_5.5 | r2_fresh | single_heavy_full | 0% | 55.5 | 85.8 | 460 | 48.9 | — |
| u13kv65_5.5 | r2_fresh | paired_heavy_full | 0% | 55.5 | 85.4 | 467 | 49.0 | — |
| u13kv65_5.5 | r2_fresh | single_slow_full | 0% | 44.2 | 84.7 | 115 | 50.7 | — |
| u13kv65_5.5 | r2_fresh | single_endurance_full | 0% | 55.8 | 128.3 | 810 | 45.9 | proposed normal overshoot; proposed tracking RMS; recommended electrical frequency |
| u13kv65_5.5 | r2_aged | single_fast_full | 9% | 60.3 | 37.9 | 1008 | 31.4 | latched protective trip during normal operation; proposed normal overshoot; proposed tracking RMS; recommended electrical frequency |
| u13kv65_5.5 | r2_aged | single_stroke_full | 0% | 28.5 | 34.5 | 919 | 48.9 | proposed normal overshoot; recommended electrical frequency |
| u13kv65_5.5 | r2_aged | single_heavy_full | 0% | 55.5 | 85.8 | 460 | 46.1 | — |
| u13kv65_5.5 | r2_aged | paired_heavy_full | 0% | 55.5 | 85.4 | 467 | 46.1 | — |
| u13kv65_5.5 | r2_aged | single_slow_full | 0% | 44.2 | 84.7 | 115 | 50.6 | — |
| u13kv65_5.5 | r2_aged | single_endurance_full | 0% | 55.8 | 128.3 | 775 | 39.6 | proposed normal overshoot; proposed tracking RMS; recommended electrical frequency |
| u13kv65_6 | r2_fresh | single_fast_full | 26% | 57.0 | 51.6 | 1031 | 42.0 | proposed tracking RMS; recommended electrical frequency |
| u13kv65_6 | r2_fresh | single_stroke_full | 2% | 27.2 | 33.2 | 995 | 50.4 | proposed normal overshoot; recommended electrical frequency |
| u13kv65_6 | r2_fresh | single_heavy_full | 0% | 50.9 | 74.9 | 502 | 49.6 | — |
| u13kv65_6 | r2_fresh | paired_heavy_full | 0% | 51.0 | 74.7 | 511 | 49.6 | — |
| u13kv65_6 | r2_fresh | single_slow_full | 0% | 40.5 | 74.0 | 125 | 50.8 | — |
| u13kv65_6 | r2_fresh | single_endurance_full | 0% | 51.3 | 128.1 | 677 | 47.4 | proposed normal overshoot; proposed tracking RMS |
| u13kv65_6 | r2_aged | single_fast_full | 18% | 57.6 | 40.2 | 1033 | 30.8 | latched protective trip during normal operation; proposed normal overshoot; proposed tracking RMS; recommended electrical frequency |
| u13kv65_6 | r2_aged | single_stroke_full | 2% | 27.2 | 33.2 | 995 | 48.9 | proposed normal overshoot; recommended electrical frequency |
| u13kv65_6 | r2_aged | single_heavy_full | 0% | 50.9 | 74.9 | 502 | 47.4 | — |
| u13kv65_6 | r2_aged | paired_heavy_full | 0% | 51.0 | 74.7 | 511 | 47.4 | — |
| u13kv65_6 | r2_aged | single_slow_full | 0% | 40.5 | 74.0 | 125 | 50.7 | — |
| u13kv65_6 | r2_aged | single_endurance_full | 0% | 51.3 | 128.2 | 681 | 41.9 | proposed normal overshoot; proposed tracking RMS |
| u13kv65_5.5_weak_path | r2_fresh | single_fast_full | 20% | 59.6 | 64.6 | 949 | 40.9 | recommended electrical frequency |
| u13kv65_5.5_weak_path | r2_fresh | single_stroke_full | 0% | 28.5 | 37.6 | 919 | 50.4 | proposed normal overshoot; recommended electrical frequency |
| u13kv65_5.5_weak_path | r2_fresh | single_heavy_full | 0% | 55.5 | 112.3 | 460 | 48.7 | — |
| u13kv65_5.5_weak_path | r2_fresh | paired_heavy_full | 0% | 55.5 | 111.7 | 467 | 48.7 | — |
| u13kv65_5.5_weak_path | r2_fresh | single_slow_full | 0% | 44.2 | 124.7 | 115 | 50.6 | — |
| u13kv65_5.5_weak_path | r2_fresh | single_endurance_full | 0% | 55.8 | 131.1 | 892 | 47.3 | proposed normal overshoot; proposed tracking RMS; recommended electrical frequency |
| u13kv65_5.5_weak_path | r2_aged | single_fast_full | 9% | 60.3 | 39.2 | 1009 | 31.4 | latched protective trip during normal operation; proposed normal overshoot; proposed tracking RMS; recommended electrical frequency |
| u13kv65_5.5_weak_path | r2_aged | single_stroke_full | 0% | 28.5 | 37.6 | 919 | 48.9 | proposed normal overshoot; recommended electrical frequency |
| u13kv65_5.5_weak_path | r2_aged | single_heavy_full | 0% | 55.5 | 112.3 | 460 | 45.5 | — |
| u13kv65_5.5_weak_path | r2_aged | paired_heavy_full | 0% | 55.5 | 111.7 | 467 | 45.5 | — |
| u13kv65_5.5_weak_path | r2_aged | single_slow_full | 0% | 44.2 | 124.7 | 115 | 50.5 | — |
| u13kv65_5.5_weak_path | r2_aged | single_endurance_full | 0% | 55.8 | 131.1 | 891 | 42.9 | proposed normal overshoot; proposed tracking RMS; recommended electrical frequency |
| u15kv80_6.5 | r2_fresh | single_fast_full | 15% | 69.3 | 37.3 | 1133 | 41.2 | proposed normal overshoot; proposed tracking RMS; recommended electrical frequency |
| u15kv80_6.5 | r2_fresh | single_stroke_full | 0% | 62.6 | 28.8 | 1088 | 50.2 | proposed normal overshoot; proposed tracking RMS; recommended electrical frequency |
| u15kv80_6.5 | r2_fresh | single_heavy_full | 0% | 63.0 | 39.4 | 554 | 50.6 | — |
| u15kv80_6.5 | r2_fresh | paired_heavy_full | 0% | 64.5 | 39.4 | 564 | 50.5 | — |
| u15kv80_6.5 | r2_fresh | single_slow_full | 0% | 46.8 | 39.1 | 136 | 51.4 | — |
| u15kv80_6.5 | r2_fresh | single_endurance_full | 0% | 62.0 | 57.8 | 439 | 50.4 | — |
| u15kv80_6.5 | r2_aged | single_fast_full | 6% | 69.3 | 29.8 | 1085 | 30.0 | latched protective trip during normal operation; proposed normal overshoot; proposed tracking RMS; recommended electrical frequency |
| u15kv80_6.5 | r2_aged | single_stroke_full | 0% | 62.6 | 28.8 | 1088 | 47.9 | proposed normal overshoot; proposed tracking RMS; recommended electrical frequency |
| u15kv80_6.5 | r2_aged | single_heavy_full | 0% | 63.0 | 39.4 | 554 | 50.2 | — |
| u15kv80_6.5 | r2_aged | paired_heavy_full | 0% | 64.5 | 39.4 | 564 | 50.1 | — |
| u15kv80_6.5 | r2_aged | single_slow_full | 0% | 46.8 | 39.1 | 136 | 51.3 | — |
| u15kv80_6.5 | r2_aged | single_endurance_full | 0% | 62.0 | 58.4 | 439 | 49.1 | — |
| tbm_6_km0.60 | r2_fresh | single_fast_full | 18% | 53.1 | 45.6 | 482 | 43.0 | — |
| tbm_6_km0.60 | r2_fresh | single_stroke_full | 0% | 25.1 | 32.0 | 481 | 50.4 | proposed normal overshoot |
| tbm_6_km0.60 | r2_fresh | single_heavy_full | 0% | 56.2 | 65.4 | 239 | 50.1 | — |
| tbm_6_km0.60 | r2_fresh | paired_heavy_full | 0% | 56.2 | 65.4 | 239 | 50.1 | — |
| tbm_6_km0.60 | r2_fresh | single_slow_full | 0% | 44.9 | 64.4 | 60 | 50.9 | — |
| tbm_6_km0.60 | r2_fresh | single_endurance_full | 0% | 56.3 | 118.7 | 191 | 49.0 | — |
| tbm_6_km0.60 | r2_aged | single_fast_full | 20% | 54.3 | 41.3 | 493 | 30.3 | latched protective trip during normal operation; proposed tracking RMS |
| tbm_6_km0.60 | r2_aged | single_stroke_full | 0% | 25.1 | 32.0 | 481 | 49.2 | proposed normal overshoot |
| tbm_6_km0.60 | r2_aged | single_heavy_full | 0% | 56.2 | 65.4 | 239 | 48.4 | — |
| tbm_6_km0.60 | r2_aged | paired_heavy_full | 0% | 56.2 | 65.4 | 239 | 48.4 | — |
| tbm_6_km0.60 | r2_aged | single_slow_full | 0% | 44.9 | 64.5 | 60 | 50.8 | — |
| tbm_6_km0.60 | r2_aged | single_endurance_full | 0% | 56.3 | 119.2 | 191 | 45.8 | — |
| tbm_6_km0.65 | r2_fresh | single_fast_full | 17% | 53.0 | 42.7 | 482 | 43.2 | — |
| tbm_6_km0.65 | r2_fresh | single_stroke_full | 0% | 25.1 | 31.1 | 481 | 50.4 | proposed normal overshoot |
| tbm_6_km0.65 | r2_fresh | single_heavy_full | 0% | 56.2 | 59.0 | 239 | 50.2 | — |
| tbm_6_km0.65 | r2_fresh | paired_heavy_full | 0% | 56.2 | 59.0 | 239 | 50.2 | — |
| tbm_6_km0.65 | r2_fresh | single_slow_full | 0% | 44.9 | 58.2 | 60 | 51.0 | — |
| tbm_6_km0.65 | r2_fresh | single_endurance_full | 0% | 56.3 | 102.6 | 191 | 49.5 | — |
| tbm_6_km0.65 | r2_aged | single_fast_full | 21% | 54.3 | 39.7 | 492 | 30.5 | latched protective trip during normal operation; proposed tracking RMS |
| tbm_6_km0.65 | r2_aged | single_stroke_full | 0% | 25.1 | 31.1 | 481 | 49.3 | proposed normal overshoot |
| tbm_6_km0.65 | r2_aged | single_heavy_full | 0% | 56.2 | 59.0 | 239 | 49.0 | — |
| tbm_6_km0.65 | r2_aged | paired_heavy_full | 0% | 56.2 | 59.0 | 239 | 49.0 | — |
| tbm_6_km0.65 | r2_aged | single_slow_full | 0% | 44.9 | 58.2 | 60 | 50.9 | — |
| tbm_6_km0.65 | r2_aged | single_endurance_full | 0% | 56.3 | 103.2 | 191 | 46.8 | — |
| tbm_6_km0.70 | r2_fresh | single_fast_full | 16% | 53.0 | 40.3 | 482 | 43.2 | — |
| tbm_6_km0.70 | r2_fresh | single_stroke_full | 0% | 25.1 | 30.5 | 481 | 50.5 | proposed normal overshoot |
| tbm_6_km0.70 | r2_fresh | single_heavy_full | 0% | 56.2 | 54.1 | 239 | 50.3 | — |
| tbm_6_km0.70 | r2_fresh | paired_heavy_full | 0% | 56.2 | 54.1 | 239 | 50.3 | — |
| tbm_6_km0.70 | r2_fresh | single_slow_full | 0% | 44.9 | 53.4 | 60 | 51.1 | — |
| tbm_6_km0.70 | r2_fresh | single_endurance_full | 0% | 56.3 | 90.6 | 191 | 49.9 | — |
| tbm_6_km0.70 | r2_aged | single_fast_full | 24% | 54.2 | 39.0 | 491 | 30.2 | latched protective trip during normal operation; proposed tracking RMS |
| tbm_6_km0.70 | r2_aged | single_stroke_full | 0% | 25.1 | 30.5 | 481 | 49.4 | proposed normal overshoot |
| tbm_6_km0.70 | r2_aged | single_heavy_full | 0% | 56.2 | 54.1 | 239 | 49.4 | — |
| tbm_6_km0.70 | r2_aged | paired_heavy_full | 0% | 56.2 | 54.1 | 239 | 49.4 | — |
| tbm_6_km0.70 | r2_aged | single_slow_full | 0% | 44.9 | 53.4 | 60 | 51.0 | — |
| tbm_6_km0.70 | r2_aged | single_endurance_full | 0% | 56.3 | 91.2 | 191 | 47.5 | — |
| tbm_6_km0.75 | r2_fresh | single_fast_full | 16% | 53.0 | 38.5 | 482 | 43.4 | — |
| tbm_6_km0.75 | r2_fresh | single_stroke_full | 0% | 25.1 | 30.0 | 481 | 50.5 | proposed normal overshoot |
| tbm_6_km0.75 | r2_fresh | single_heavy_full | 0% | 56.2 | 50.2 | 239 | 50.4 | — |
| tbm_6_km0.75 | r2_fresh | paired_heavy_full | 0% | 56.2 | 50.2 | 239 | 50.4 | — |
| tbm_6_km0.75 | r2_fresh | single_slow_full | 0% | 44.9 | 49.6 | 60 | 51.1 | — |
| tbm_6_km0.75 | r2_fresh | single_endurance_full | 0% | 56.3 | 81.6 | 191 | 50.1 | — |
| tbm_6_km0.75 | r2_aged | single_fast_full | 27% | 54.2 | 38.4 | 491 | 30.1 | latched protective trip during normal operation; proposed tracking RMS |
| tbm_6_km0.75 | r2_aged | single_stroke_full | 0% | 25.1 | 30.0 | 481 | 49.4 | proposed normal overshoot |
| tbm_6_km0.75 | r2_aged | single_heavy_full | 0% | 56.2 | 50.2 | 239 | 49.7 | — |
| tbm_6_km0.75 | r2_aged | paired_heavy_full | 0% | 56.2 | 50.2 | 239 | 49.7 | — |
| tbm_6_km0.75 | r2_aged | single_slow_full | 0% | 44.9 | 49.6 | 60 | 51.1 | — |
| tbm_6_km0.75 | r2_aged | single_endurance_full | 0% | 56.3 | 82.2 | 191 | 47.9 | — |

## Variants

- **r4_ro100**: R4 candidate (RO100, 5:1, 50 A)
- **tbm_5**: motor: tbm2g_11526d; control: {'current_limit_a': 69.3}
- **tbm_5_100a**: motor: tbm2g_11526d; control: {'current_limit_a': 86.6}
- **tbm_5.5**: motor: tbm2g_11526d; reference: {'ratio': 5.5}; control: {'current_limit_a': 69.3}
- **tbm_6**: motor: tbm2g_11526d; reference: {'ratio': 6.0}; control: {'current_limit_a': 69.3}
- **tbm_5.5_weak_path**: motor: tbm2g_11526d; reference: {'ratio': 5.5}; control: {'current_limit_a': 69.3}; thermal_scale: {'winding_to_housing_k_w': 2.5}
- **tbm_6_weak_path**: motor: tbm2g_11526d; reference: {'ratio': 6.0}; control: {'current_limit_a': 69.3}; thermal_scale: {'winding_to_housing_k_w': 2.5}
- **ro100kv80_5.5**: motor: ro100_kv80_hypothetical; reference: {'ratio': 5.5}; control: {'current_limit_a': 66.7}
- **ro100kv80_6**: motor: ro100_kv80_hypothetical; reference: {'ratio': 6.0}; control: {'current_limit_a': 66.7}
- **ro100kv80_6_weak_path**: motor: ro100_kv80_hypothetical; reference: {'ratio': 6.0}; control: {'current_limit_a': 66.7}; thermal_scale: {'winding_to_housing_k_w': 2.5}
- **u13kv65_5.5**: motor: tmotor_u13ii_kv65; reference: {'ratio': 5.5}; control: {'current_limit_a': 69.3}
- **u13kv65_6**: motor: tmotor_u13ii_kv65; reference: {'ratio': 6.0}; control: {'current_limit_a': 69.3}
- **u13kv65_5.5_weak_path**: motor: tmotor_u13ii_kv65; reference: {'ratio': 5.5}; control: {'current_limit_a': 69.3}; thermal_scale: {'winding_to_housing_k_w': 2.5}
- **u15kv80_6.5**: motor: tmotor_u15ii_kv80; reference: {'ratio': 6.5}; control: {'current_limit_a': 69.3}
- **tbm_6_km0.60**: motor: tbm2g_11526d; reference: {'ratio': 6.0}; control: {'current_limit_a': 69.3}; sensitivity: {'km_scale': 0.748}
- **tbm_6_km0.65**: motor: tbm2g_11526d; reference: {'ratio': 6.0}; control: {'current_limit_a': 69.3}; sensitivity: {'km_scale': 0.81}
- **tbm_6_km0.70**: motor: tbm2g_11526d; reference: {'ratio': 6.0}; control: {'current_limit_a': 69.3}; sensitivity: {'km_scale': 0.873}
- **tbm_6_km0.75**: motor: tbm2g_11526d; reference: {'ratio': 6.0}; control: {'current_limit_a': 69.3}; sensitivity: {'km_scale': 0.935}

## Notes

- The plant is the R4 candidate (bank on the drive bus, R3 heat path, controller C1, 56 V trip, gate-rule dump monitor). Only the listed keys change.
- Ratio variants keep the R2 CAD drum inertia and do not rerun belt, bearing or support screens; reflected motor inertia scales with the ratio squared. 5.5:1 and 6:1 would need new pulleys (for example 22/121 and 20/120 teeth).
- The TBM2G keeps the RO100's heat-path values (winding-to-housing 0.28 K/W, winding 48.3 J/K, housing 193.2 J/K) unless a variant scales them. A frameless stator bonded into an aluminium carrier is assumed to be at least as good as the RO100 estimate; this is not measured. The heavier TBM2G (1.43 kg) would add heat capacity that is not credited.
- Kt does not fall with winding temperature in the model; the hot TBM2G Kt is about 11% below the cold value used.
- The 1.4 kg and 128 mm housed OD of the TBM2G are not checked against the R2 CAD or the ADR-003 envelope.
- ro100_kv80_hypothetical is not a listed part. It is a first-order rewind of the RO100 Lite (same Km, peak torque, poles), used to set a custom-winding specification.
- The T-Motor values are first-order conversions of drone datasheets (Kv, internal resistance, propeller test torque) with estimated inertia, and they keep the RO100 heat path although they are open-frame motors rated with propeller airflow. The U15 II does not fit the 139 mm section.

Reproduce: `make motor-study`.
