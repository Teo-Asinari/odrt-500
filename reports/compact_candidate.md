# CAD-derived compact candidate simulation

Fingerprint: `6213b74d0dca64dd1a2559eff5920b051e953cfac057152f5bfcf1420dd237c8`

**Assessment: REVISE.** This study evaluates the compact geometry candidate, not a complete qualified product. It retains all configured normal and fault scenarios and does not retune controller gains.

Total known drum-referred inertia: 0.02425401 kg m². The equivalent additional drum term is 0.00521001; the catalog motor rotor is then added exactly once by the coupled plant.

Nominal routing length: 0.148 m. Nominal straight takeoff-to-guide 90 mm plus guide-to-body-exit 58 mm. Guide contact curvature and exit motion are unresolved; not a measured complete cable path.

Air-node capacity: 5.415 J/K; flow conductance 14.229 W/K. Gross owner body volume times assumed air density and specific heat; upper bound on air-only storage before displaced volume. Structure has not been added to this node. Conditional EPP-500 forced-air requirement, not a selected fan or demonstrated installed flow.

| Bank / case | Tracking % | Peak N | Bus min–max V | Winding °C | Bar angle ° | Trip | Failed comparisons |
|---|---:|---:|---:|---:|---:|---|---|
| compact_nominal / single_curl_full | 0.62 | 181.6 | 47.78–48.81 | 28.9 | 0.00 | none | none in listed screens |
| compact_nominal / single_row_full | 0.44 | 542.6 | 46.63–49.04 | 49.3 | 0.00 | none | none in listed screens |
| compact_nominal / single_press_full | 0.61 | 677.8 | 45.89–49.06 | 55.9 | 0.00 | none | none in listed screens |
| compact_nominal / single_slow_full | 0.09 | 897.6 | 46.60–48.74 | 96.3 | 0.00 | none | none in listed screens |
| compact_nominal / single_eccentric_full | 0.16 | 670.0 | 47.17–49.01 | 56.4 | 0.00 | none | none in listed screens |
| compact_nominal / single_heavy_full | 0.16 | 1124.6 | 44.35–49.07 | 78.5 | 0.00 | none | none in listed screens |
| compact_nominal / single_hold_full | 0.13 | 1123.1 | 46.37–48.17 | 83.6 | 0.00 | none | none in listed screens |
| compact_nominal / single_low_full | 4.55 | 39.7 | 47.90–48.22 | 25.8 | 0.00 | none | proposed normal overshoot |
| compact_nominal / single_fast_full | 55.95 | 2374.6 | 40.84–49.11 | 46.5 | 0.00 | none | proposed normal overshoot, proposed tracking RMS, recommended electrical frequency, virtual motor voltage controllability, virtual travel stop engagement |
| compact_nominal / single_stroke_full | 66.41 | 1665.7 | 45.73–49.11 | 36.8 | 0.00 | none | proposed normal overshoot, proposed tracking RMS, recommended electrical frequency, virtual travel stop engagement |
| compact_nominal / single_endurance_full | 30.45 | 1215.1 | 42.64–49.06 | 129.9 | 0.00 | none | proposed normal overshoot, proposed tracking RMS |
| compact_nominal / paired_heavy_full | 0.74 | 1128.9 | 43.40–49.07 | 78.2 | 0.00 | none | none in listed screens |
| compact_nominal / paired_asymmetric | 61.90 | 1581.0 | 40.02–49.08 | 58.5 | 93.85 | undervoltage | latched protective trip during normal operation, proposed normal overshoot, proposed tracking RMS, recommended electrical frequency, virtual travel stop engagement |
| compact_nominal / left_power_loss_uncoordinated | 0.62 | 1198.7 | 42.54–49.07 | 40.4 | 76.66 | none | none in listed screens |
| compact_nominal / left_power_loss_coordinated | 0.62 | 1124.5 | 47.37–49.07 | 30.9 | 2.28 | none | none in listed screens |
| compact_nominal / left_power_loss_buffered | 0.62 | 1124.5 | 40.01–49.07 | 37.1 | 53.95 | undervoltage | none in listed screens |
| compact_nominal / left_power_loss_buffered_coordinated | 0.62 | 1124.5 | 40.03–49.07 | 35.4 | 2.15 | undervoltage | none in listed screens |
| compact_nominal / left_sensor_loss | 0.62 | 1124.5 | 47.22–49.07 | 31.0 | 1.24 | none | none in listed screens |
| compact_nominal / left_encoder_loss | 0.62 | 1124.5 | 47.41–49.07 | 31.0 | 1.36 | none | none in listed screens |
| compact_nominal / left_torque_inverted | 0.62 | 1177.8 | 43.81–49.07 | 31.0 | 3.85 | none | recommended electrical frequency, virtual motor voltage controllability |
| compact_nominal / left_torque_frozen | 0.62 | 1124.5 | 47.40–49.07 | 31.1 | 1.38 | none | none in listed screens |
| compact_nominal / paired_communication_loss | 0.62 | 1124.5 | 47.41–49.07 | 31.0 | 0.00 | none | none in listed screens |
| compact_nominal / paired_release | 0.62 | 1124.5 | 43.27–49.07 | 29.7 | 0.00 | none | none in listed screens |
| compact_nominal / paired_release_asymmetric | 0.62 | 1124.4 | 43.24–49.07 | 29.7 | 47.82 | none | none in listed screens |
| compact_nominal / paired_emergency_stop | 0.62 | 1124.5 | 47.41–49.07 | 30.8 | 0.00 | none | none in listed screens |
| compact_nominal / paired_dump_failure | 0.09 | 1196.8 | 42.77–49.98 | 40.6 | 76.56 | overvoltage | none in listed screens |
| compact_nominal / paired_dump_failure_coordinated | 0.09 | 1153.2 | 47.41–49.98 | 29.9 | 0.27 | overvoltage | none in listed screens |
| compact_aged / single_curl_full | 0.62 | 181.6 | 47.72–49.00 | 29.0 | 0.00 | none | none in listed screens |
| compact_aged / single_row_full | 0.44 | 542.6 | 46.33–49.05 | 49.4 | 0.00 | none | none in listed screens |
| compact_aged / single_press_full | 0.61 | 677.8 | 43.60–49.07 | 56.0 | 0.00 | none | none in listed screens |
| compact_aged / single_slow_full | 0.09 | 897.6 | 46.50–49.00 | 96.3 | 0.00 | none | none in listed screens |
| compact_aged / single_eccentric_full | 0.16 | 670.0 | 47.08–49.02 | 56.5 | 0.00 | none | none in listed screens |
| compact_aged / single_heavy_full | 0.16 | 1124.6 | 40.37–49.07 | 78.5 | 0.00 | none | none in listed screens |
| compact_aged / single_hold_full | 0.13 | 1123.1 | 46.21–48.43 | 83.6 | 0.00 | none | none in listed screens |
| compact_aged / single_low_full | 4.55 | 39.7 | 47.88–48.44 | 25.8 | 0.00 | none | proposed normal overshoot |
| compact_aged / single_fast_full | 94.53 | 1039.3 | 41.52–49.11 | 26.5 | 0.00 | undervoltage | latched protective trip during normal operation, proposed normal overshoot, proposed tracking RMS, recommended electrical frequency |
| compact_aged / single_stroke_full | 66.59 | 1643.1 | 44.18–49.11 | 36.8 | 0.00 | none | proposed normal overshoot, proposed tracking RMS, recommended electrical frequency, virtual travel stop engagement |
| compact_aged / single_endurance_full | 99.41 | 1123.9 | 40.02–49.06 | 35.3 | 0.00 | undervoltage | latched protective trip during normal operation, proposed tracking RMS |
| compact_aged / paired_heavy_full | 72.06 | 1124.5 | 40.02–49.08 | 49.2 | 0.00 | undervoltage | latched protective trip during normal operation, proposed tracking RMS |
| compact_aged / paired_asymmetric | 73.33 | 1605.5 | 40.10–49.08 | 49.6 | 94.76 | undervoltage | latched protective trip during normal operation, proposed normal overshoot, proposed tracking RMS, virtual travel stop engagement |
| compact_aged / left_power_loss_uncoordinated | 0.62 | 1124.5 | 40.10–49.08 | 31.6 | 14.99 | none | none in listed screens |
| compact_aged / left_power_loss_coordinated | 0.62 | 1124.5 | 47.09–49.08 | 30.9 | 2.28 | none | none in listed screens |
| compact_aged / left_power_loss_buffered | 0.62 | 1124.5 | 40.03–49.08 | 33.5 | 8.67 | undervoltage | none in listed screens |
| compact_aged / left_power_loss_buffered_coordinated | 0.62 | 1124.5 | 40.03–49.08 | 33.2 | 1.76 | undervoltage | none in listed screens |
| compact_aged / left_sensor_loss | 0.62 | 1124.5 | 46.89–49.08 | 31.0 | 1.24 | none | none in listed screens |
| compact_aged / left_encoder_loss | 0.62 | 1124.5 | 47.19–49.08 | 31.0 | 1.36 | none | none in listed screens |
| compact_aged / left_torque_inverted | 0.62 | 1141.1 | 41.82–49.08 | 30.9 | 2.38 | undervoltage | none in listed screens |
| compact_aged / left_torque_frozen | 0.62 | 1124.5 | 47.13–49.08 | 31.1 | 1.38 | none | none in listed screens |
| compact_aged / paired_communication_loss | 0.62 | 1124.5 | 47.26–49.08 | 31.0 | 0.00 | none | none in listed screens |
| compact_aged / paired_release | 0.62 | 1124.5 | 42.88–49.08 | 29.7 | 0.00 | undervoltage | none in listed screens |
| compact_aged / paired_release_asymmetric | 0.62 | 1124.4 | 42.86–49.08 | 29.7 | 48.47 | undervoltage | none in listed screens |
| compact_aged / paired_emergency_stop | 0.62 | 1124.5 | 47.26–49.08 | 30.8 | 0.00 | none | none in listed screens |
| compact_aged / paired_dump_failure | 0.09 | 1124.5 | 40.24–49.97 | 30.3 | 8.99 | overvoltage | none in listed screens |
| compact_aged / paired_dump_failure_coordinated | 0.09 | 1143.2 | 47.26–49.97 | 29.8 | 0.59 | overvoltage | none in listed screens |

## Numerical refinement

| Case | Max medium–fine change | Outcome |
|---|---:|---|
| compact_nominal__single_heavy_full | 0.000% | pass |
| compact_nominal__paired_release_asymmetric | 0.002% | pass |
| compact_aged__left_power_loss_buffered_coordinated | 0.002% | pass |
| compact_aged__single_fast_full | 0.000% | pass |

## Candidate uncertainties

| Perturbation | Tracking % | Winding °C | Minimum bus V | Failed comparisons |
|---|---:|---:|---:|---|
| nominal | 0.74 | 78.2 | 43.40 | none in listed screens |
| half_airflow | 0.74 | 78.2 | 43.40 | none in listed screens |
| quarter_airflow | 0.74 | 78.2 | 43.40 | none in listed screens |
| short_routing | 0.74 | 78.2 | 43.40 | none in listed screens |
| long_routing | 0.76 | 78.2 | 43.37 | none in listed screens |
| low_km | 86.97 | 51.8 | 40.01 | latched protective trip during normal operation, proposed tracking RMS |
| warm_room | 0.74 | 96.2 | 43.15 | drive rated ambient conditions |
| extra_inertia | 71.50 | 49.4 | 40.02 | latched protective trip during normal operation, proposed tracking RMS |

## Remaining limits

- CAD and catalog rotor inertia are included; rope mass and rotating bearing details remain additional uncertainty.
- Electrical and motor thermal resistances/capacities remain reference proposals. Enclosure geometry does not validate those paths.
- The smaller bank thermal capacity remains an assumption from data/compact_buffer.yaml.
- No controller gains are retuned to make this candidate pass. Inertia feedforward uses the candidate plant parameters as in the reference controller.

The full compact CAD still lacks engineered wiring, connectors, positive retention, sensors, guide actuation detail, cooling and electrical clearances. The conditional airflow is not a demonstrated installed capability. No qualified force/speed/duty or fault envelope follows from numerical convergence. Read `compact_package.md`, `coupled.md` and the validation plan.

Reproduce: `.venv/bin/python -m odrt.compact_candidate`.
