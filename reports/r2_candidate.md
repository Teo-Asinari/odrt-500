# R2 candidate simulation

Fingerprint: `7e251a624386a5c2e58c0ad0b6940574b02686731031ef11558972ac88437af8`

**Assessment: REVISE.** R2 joins the [R2 CAD](r2_package.md), the [power revision](revision_power.md) and the [support revision](support_revision.md) into one simulated machine: 5:1 belt, drum-referred inertia 0.016331 kg m² (R1: 0.024254), routing 0.062 m, 20 × TV 3 V cells upstream of a Regen Clamp, EPP-500-54 at 52 V, motor current limit 50 A. Controller gains are unchanged from the reference.

| Bank / case | Tracking % | Peak N | Bus min–max V | Winding °C | Bar ° | Trip | Failed comparisons |
|---|---:|---:|---:|---:|---:|---|---|
| r2_fresh / single_endurance_full | 40.14 | 1123 | 45.1–53.0 | 131.8 | 0.0 | none | proposed normal overshoot, proposed tracking RMS |
| r2_fresh / single_curl_full | 0.37 | 181 | 51.7–52.8 | 30.1 | 0.0 | none | none |
| r2_fresh / single_row_full | 0.28 | 541 | 50.6–53.0 | 59.3 | 0.0 | none | none |
| r2_fresh / single_press_full | 0.28 | 676 | 49.5–53.1 | 69.4 | 0.0 | none | none |
| r2_fresh / single_slow_full | 3.45 | 897 | 48.7–52.7 | 128.5 | 0.0 | none | proposed normal overshoot |
| r2_fresh / single_eccentric_full | 0.12 | 670 | 51.0–52.9 | 71.3 | 0.0 | none | none |
| r2_fresh / single_heavy_full | 0.12 | 1123 | 46.3–53.1 | 106.2 | 0.0 | none | none |
| r2_fresh / single_hold_full | 0.10 | 1123 | 49.9–52.0 | 114.8 | 0.0 | none | none |
| r2_fresh / single_low_full | 2.73 | 38 | 51.9–52.8 | 25.9 | 0.0 | none | none |
| r2_fresh / single_fast_full | 67.71 | 1298 | 40.1–53.5 | 48.9 | 0.0 | undervoltage | latched protective trip during normal operation, proposed normal overshoot, proposed tracking RMS, recommended electrical frequency |
| r2_fresh / single_stroke_full | 35.75 | 1515 | 49.6–53.2 | 37.2 | 0.0 | none | proposed normal overshoot, proposed tracking RMS, recommended electrical frequency, virtual travel stop engagement |
| r2_fresh / paired_heavy_full | 0.18 | 1123 | 46.3–53.1 | 106.0 | 0.0 | none | none |
| r2_fresh / paired_asymmetric | 0.79 | 1135 | 42.3–53.1 | 105.5 | 10.8 | none | proposed normal overshoot |
| r2_fresh / left_power_loss_uncoordinated | 0.44 | 1175 | 45.7–53.1 | 47.9 | 76.4 | none | none |
| r2_fresh / left_power_loss_coordinated | 0.44 | 1123 | 51.0–53.1 | 33.4 | 3.2 | none | none |
| r2_fresh / left_power_loss_buffered | 0.44 | 1123 | 42.5–53.1 | 48.3 | 0.0 | none | none |
| r2_fresh / left_power_loss_buffered_coordinated | 0.44 | 1123 | 42.5–53.1 | 48.3 | 0.0 | none | none |
| r2_fresh / left_sensor_loss | 0.44 | 1134 | 50.4–53.1 | 33.4 | 1.6 | none | none |
| r2_fresh / left_encoder_loss | 0.44 | 1123 | 51.1–53.1 | 33.4 | 1.9 | none | none |
| r2_fresh / left_torque_inverted | 0.44 | 1201 | 46.1–53.1 | 33.4 | 5.5 | none | recommended electrical frequency, virtual motor voltage controllability |
| r2_fresh / left_torque_frozen | 0.44 | 1123 | 51.1–53.1 | 33.6 | 1.9 | none | none |
| r2_fresh / paired_communication_loss | 0.44 | 1123 | 51.2–53.1 | 33.5 | 0.0 | none | none |
| r2_fresh / paired_release | 0.44 | 1123 | 47.1–53.1 | 32.0 | 0.7 | none | none |
| r2_fresh / paired_release_asymmetric | 0.44 | 1123 | 47.1–53.1 | 32.0 | 48.4 | none | none |
| r2_fresh / paired_emergency_stop | 0.44 | 1123 | 51.2–53.1 | 33.2 | 0.0 | none | none |
| r2_fresh / paired_dump_failure | 0.13 | 1177 | 48.0–57.0 | 47.6 | 76.4 | overvoltage | none |
| r2_fresh / paired_dump_failure_coordinated | 0.13 | 1123 | 51.3–57.0 | 30.2 | 1.3 | overvoltage | none |
| r2_aged / single_endurance_full | 97.91 | 1123 | 40.0–53.0 | 86.2 | 0.0 | undervoltage | latched protective trip during normal operation, proposed tracking RMS |
| r2_aged / single_curl_full | 0.37 | 181 | 51.7–52.8 | 30.1 | 0.0 | none | none |
| r2_aged / single_row_full | 0.28 | 541 | 50.3–53.0 | 59.3 | 0.0 | none | none |
| r2_aged / single_press_full | 0.28 | 676 | 47.5–53.1 | 69.4 | 0.0 | none | none |
| r2_aged / single_slow_full | 3.45 | 897 | 46.0–52.7 | 128.5 | 0.0 | none | proposed normal overshoot |
| r2_aged / single_eccentric_full | 0.12 | 670 | 51.0–52.9 | 71.3 | 0.0 | none | none |
| r2_aged / single_heavy_full | 0.12 | 1123 | 40.1–53.1 | 106.2 | 0.0 | none | none |
| r2_aged / single_hold_full | 0.10 | 1123 | 49.1–52.0 | 114.8 | 0.0 | none | none |
| r2_aged / single_low_full | 2.73 | 38 | 51.9–52.8 | 25.9 | 0.0 | none | none |
| r2_aged / single_fast_full | 90.63 | 1160 | 40.2–53.5 | 31.4 | 0.0 | undervoltage | latched protective trip during normal operation, proposed normal overshoot, proposed tracking RMS, recommended electrical frequency |
| r2_aged / single_stroke_full | 35.77 | 1522 | 47.8–53.2 | 37.1 | 0.0 | none | proposed normal overshoot, proposed tracking RMS, recommended electrical frequency, virtual travel stop engagement |
| r2_aged / paired_heavy_full | 16.98 | 1123 | 40.0–53.1 | 101.9 | 0.0 | undervoltage | latched protective trip during normal operation, proposed tracking RMS |
| r2_aged / paired_asymmetric | 43.20 | 1508 | 40.0–53.1 | 89.3 | 92.9 | undervoltage | latched protective trip during normal operation, proposed normal overshoot, proposed tracking RMS, virtual travel stop engagement |
| r2_aged / left_power_loss_uncoordinated | 0.44 | 1123 | 40.1–53.1 | 34.4 | 21.6 | none | none |
| r2_aged / left_power_loss_coordinated | 0.44 | 1123 | 50.7–53.1 | 33.4 | 3.2 | none | none |
| r2_aged / left_power_loss_buffered | 0.44 | 1123 | 40.0–53.1 | 38.7 | 10.4 | undervoltage | none |
| r2_aged / left_power_loss_buffered_coordinated | 0.44 | 1123 | 40.0–53.1 | 38.3 | 2.6 | undervoltage | none |
| r2_aged / left_sensor_loss | 0.44 | 1134 | 50.0–53.1 | 33.4 | 1.6 | none | none |
| r2_aged / left_encoder_loss | 0.44 | 1123 | 50.9–53.1 | 33.4 | 1.9 | none | none |
| r2_aged / left_torque_inverted | 0.44 | 1194 | 42.2–53.1 | 33.4 | 5.4 | none | recommended electrical frequency, virtual motor voltage controllability |
| r2_aged / left_torque_frozen | 0.44 | 1123 | 50.9–53.1 | 33.6 | 1.9 | none | none |
| r2_aged / paired_communication_loss | 0.44 | 1123 | 51.0–53.1 | 33.5 | 0.0 | none | none |
| r2_aged / paired_release | 0.44 | 1123 | 43.9–53.1 | 32.0 | 0.8 | none | none |
| r2_aged / paired_release_asymmetric | 0.44 | 1123 | 43.9–53.1 | 32.0 | 48.5 | none | none |
| r2_aged / paired_emergency_stop | 0.44 | 1123 | 51.0–53.1 | 33.2 | 0.0 | none | none |
| r2_aged / paired_dump_failure | 0.13 | 1177 | 42.9–57.0 | 47.6 | 76.4 | overvoltage | none |
| r2_aged / paired_dump_failure_coordinated | 0.13 | 1123 | 51.1–57.0 | 30.2 | 1.3 | overvoltage | none |

## Numerical refinement

| Case | Max medium–fine change | Outcome |
|---|---:|---|
| r2_fresh__single_heavy_full | 0.001% | pass |
| r2_aged__single_fast_full | 0.000% | pass |
| r2_fresh__paired_release_asymmetric | 0.002% | pass |
| r2_aged__left_power_loss_buffered_coordinated | 0.001% | pass |

## Uncertainties (paired heavy set, fresh bank; heat-path bounds on the slow heavy pull)

| Perturbation | Tracking % | Winding °C | Minimum bus V | Trip | Failed comparisons |
|---|---:|---:|---:|---|---|
| nominal | 0.18 | 106.0 | 46.3 | none | none |
| half_airflow | 0.18 | 106.0 | 46.3 | none | none |
| quarter_airflow | 0.18 | 106.0 | 46.3 | none | none |
| long_routing | 0.18 | 106.0 | 46.3 | none | none |
| low_km | 84.90 | 85.2 | 40.0 | undervoltage | latched protective trip during normal operation, proposed tracking RMS |
| warm_room | 2.16 | 124.8 | 43.9 | none | drive rated ambient conditions, proposed normal overshoot, virtual travel stop engagement |
| extra_inertia | 0.23 | 105.8 | 46.4 | none | none |

## Support screen at simulated R2 loads

Peak rope force 1522 N and peak current 88.6 A × Kt = 17.72 Nm, combined as uncorrelated corners; belt tension difference 1547 N. 8/16 corners pass.

| Preload N/span | Rope z mm | Torque sign | Motor C0/P | Drum C0/P | Motor shaft MPa | Drum shaft MPa | Failed screens |
|---:|---:|---:|---:|---:|---:|---:|---|
| 700 | 28.5 | -1 | 2.79 | 7.41 | 84.0 | 14.7 | nonpositive nominal slack tension |
| 700 | 28.5 | 1 | 2.79 | 8.30 | 84.0 | 17.2 | nonpositive nominal slack tension |
| 700 | 53.5 | -1 | 2.79 | 8.45 | 84.0 | 14.4 | nonpositive nominal slack tension |
| 700 | 53.5 | 1 | 2.79 | 5.90 | 84.0 | 19.2 | nonpositive nominal slack tension |
| 850 | 28.5 | -1 | 2.57 | 6.90 | 88.9 | 14.8 | none |
| 850 | 28.5 | 1 | 2.57 | 7.60 | 88.9 | 17.2 | none |
| 850 | 53.5 | -1 | 2.57 | 7.72 | 88.9 | 14.7 | none |
| 850 | 53.5 | 1 | 2.57 | 5.63 | 88.9 | 19.4 | none |
| 1000 | 28.5 | -1 | 2.23 | 6.06 | 99.1 | 14.9 | none |
| 1000 | 28.5 | 1 | 2.23 | 6.51 | 99.1 | 17.4 | none |
| 1000 | 53.5 | -1 | 2.23 | 6.59 | 99.1 | 15.2 | none |
| 1000 | 53.5 | 1 | 2.23 | 5.14 | 99.1 | 19.8 | none |
| 1150 | 28.5 | -1 | 1.96 | 5.38 | 109.7 | 15.1 | motor bearing static factor |
| 1150 | 28.5 | 1 | 1.96 | 5.70 | 109.7 | 17.5 | motor bearing static factor |
| 1150 | 53.5 | -1 | 1.96 | 5.74 | 109.7 | 15.8 | motor bearing static factor |
| 1150 | 53.5 | 1 | 1.96 | 4.71 | 109.7 | 20.3 | motor bearing static factor |

## Limits

- Clamp is cycle-averaged; switching ripple, delay and peaks are not resolved. Upstream storage cannot absorb regeneration.
- Thermal resistances/capacities remain reference proposals; the TV cell heat capacity is assumed.
- Ideal radial supports; deck/bridge/side-wall stiffness, joints, fatigue and belt rating are not checked.
- Uncertainty perturbations co-vary plant and feedforward; independent miscalibration is not covered.
- No wiring, tray, retention, isolation or cooling geometry is qualified by the CAD space claim.

Reproduce: `make r2-candidate` (parallel; `JOBS=n` limits workers).
