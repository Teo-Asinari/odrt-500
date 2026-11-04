# Dump-monitor measurement study (R4)

Fingerprint: `500f68af892cc5611342f13a12f7bba2c7bc1207015371c13a5c26bc6758946b`

**Study only. The R4 candidate keeps the ideal monitor.** The R4 dump monitor was simulated as ideal. A real supervisor estimates the chopper duty from its own bus-voltage reading, while the Regen Clamp switches on its own analog threshold (cited 2.35 V typical, 2.50 V maximum above input) across a ramp only 0.15 V wide. This study adds measurement errors, plant tolerances and noise, and checks false trips in every non-dump-failure case and detection in the dump failures.

| Rule : corner / bank | False trips | Dump failure: reason, latency s, bus max V | Dump failure (coordinated) | Closest non-trip timer s |
|---|---|---|---|---|
| estimated:ideal/r2_fresh | none | dump_fault, 0.51, 55.14 | dump_fault, 0.51, 55.14 | 0.000 of 0.1 (—) |
| estimated:ideal/r2_aged | none | overvoltage, 0.38, 55.92 | overvoltage, 0.38, 55.92 | 0.000 of 0.1 (—) |
| estimated:noise_only/r2_fresh | none | dump_fault, 0.51, 55.17 | dump_fault, 0.51, 55.17 | 0.045 of 0.1 (single_press_full/unit_0) |
| estimated:noise_only/r2_aged | none | overvoltage, 0.38, 55.92 | overvoltage, 0.38, 55.92 | 0.050 of 0.1 (single_endurance_full/unit_0) |
| estimated:false_trip_corner/r2_fresh | single_endurance_full/unit_0, single_row_full/unit_0, single_press_full/unit_0, single_heavy_full/unit_0, single_fast_full/unit_0, single_stroke_full/unit_0, paired_heavy_full/unit_0, paired_heavy_full/unit_1, paired_asymmetric/unit_0, paired_asymmetric/unit_1, left_power_loss_uncoordinated/unit_0, left_power_loss_uncoordinated/unit_1, left_power_loss_coordinated/unit_0, left_power_loss_coordinated/unit_1, left_power_loss_buffered/unit_0, left_power_loss_buffered/unit_1, left_power_loss_buffered_coordinated/unit_0, left_power_loss_buffered_coordinated/unit_1, left_sensor_loss/unit_0, left_sensor_loss/unit_1, left_encoder_loss/unit_0, left_encoder_loss/unit_1, left_torque_inverted/unit_0, left_torque_inverted/unit_1, left_torque_frozen/unit_0, left_torque_frozen/unit_1, paired_communication_loss/unit_0, paired_communication_loss/unit_1, paired_release/unit_0, paired_release/unit_1, paired_release_asymmetric/unit_0, paired_release_asymmetric/unit_1, paired_emergency_stop/unit_0, paired_emergency_stop/unit_1, paired_dump_failure/unit_1, paired_dump_failure_coordinated/unit_1 | dump_fault, 0.48, 54.94 | dump_fault, 0.48, 54.94 | 0.000 of 0.1 (—) |
| estimated:false_trip_corner/r2_aged | single_endurance_full/unit_0, single_row_full/unit_0, single_press_full/unit_0, single_eccentric_full/unit_0, single_heavy_full/unit_0, single_fast_full/unit_0, single_stroke_full/unit_0, paired_heavy_full/unit_0, paired_heavy_full/unit_1, paired_asymmetric/unit_0, paired_asymmetric/unit_1, left_power_loss_uncoordinated/unit_0, left_power_loss_uncoordinated/unit_1, left_power_loss_coordinated/unit_0, left_power_loss_coordinated/unit_1, left_power_loss_buffered/unit_0, left_power_loss_buffered/unit_1, left_power_loss_buffered_coordinated/unit_0, left_power_loss_buffered_coordinated/unit_1, left_sensor_loss/unit_0, left_sensor_loss/unit_1, left_encoder_loss/unit_0, left_encoder_loss/unit_1, left_torque_inverted/unit_0, left_torque_inverted/unit_1, left_torque_frozen/unit_0, left_torque_frozen/unit_1, paired_communication_loss/unit_0, paired_communication_loss/unit_1, paired_release/unit_0, paired_release/unit_1, paired_release_asymmetric/unit_0, paired_release_asymmetric/unit_1, paired_emergency_stop/unit_0, paired_emergency_stop/unit_1, paired_dump_failure/unit_1, paired_dump_failure_coordinated/unit_1 | overvoltage, 0.38, 55.92 | overvoltage, 0.38, 55.92 | 0.000 of 0.1 (—) |
| estimated:missed_detection_corner/r2_fresh | none | dump_fault, 0.54, 55.33 | dump_fault, 0.54, 55.33 | 0.000 of 0.1 (paired_dump_failure_coordinated/unit_1) |
| estimated:missed_detection_corner/r2_aged | none | overvoltage, 0.38, 55.92 | overvoltage, 0.38, 55.92 | 0.000 of 0.1 (paired_dump_failure_coordinated/unit_1) |
| estimated_margin_0.5:ideal/r2_fresh | none | dump_fault, 0.56, 55.41 | dump_fault, 0.56, 55.41 | 0.000 of 0.1 (paired_dump_failure_coordinated/unit_1) |
| estimated_margin_0.5:ideal/r2_aged | none | overvoltage, 0.38, 55.92 | overvoltage, 0.38, 55.92 | 0.000 of 0.1 (—) |
| estimated_margin_0.5:noise_only/r2_fresh | none | dump_fault, 0.57, 55.43 | dump_fault, 0.57, 55.43 | 0.000 of 0.1 (—) |
| estimated_margin_0.5:noise_only/r2_aged | none | overvoltage, 0.38, 55.92 | overvoltage, 0.38, 55.92 | 0.000 of 0.1 (paired_dump_failure_coordinated/unit_1) |
| estimated_margin_0.5:false_trip_corner/r2_fresh | none | dump_fault, 0.53, 55.25 | dump_fault, 0.53, 55.25 | 0.009 of 0.1 (paired_asymmetric/unit_1) |
| estimated_margin_0.5:false_trip_corner/r2_aged | none | overvoltage, 0.38, 55.92 | overvoltage, 0.38, 55.92 | 0.013 of 0.1 (single_endurance_full/unit_0) |
| estimated_margin_0.5:missed_detection_corner/r2_fresh | none | dump_fault, 0.62, 55.58 | dump_fault, 0.62, 55.58 | 0.000 of 0.1 (—) |
| estimated_margin_0.5:missed_detection_corner/r2_aged | none | overvoltage, 0.38, 55.92 | overvoltage, 0.38, 55.92 | 0.000 of 0.1 (paired_dump_failure/unit_1) |
| gate:ideal/r2_fresh | none | dump_fault, 0.51, 55.14 | dump_fault, 0.51, 55.14 | 0.000 of 0.1 (—) |
| gate:ideal/r2_aged | none | overvoltage, 0.38, 55.92 | overvoltage, 0.38, 55.92 | 0.000 of 0.1 (—) |
| gate:noise_only/r2_fresh | none | dump_fault, 0.51, 55.14 | dump_fault, 0.51, 55.14 | 0.003 of 0.1 (single_fast_full/unit_0) |
| gate:noise_only/r2_aged | none | overvoltage, 0.38, 55.92 | overvoltage, 0.38, 55.92 | 0.003 of 0.1 (single_fast_full/unit_0) |
| gate:false_trip_corner/r2_fresh | none | dump_fault, 0.52, 55.22 | dump_fault, 0.52, 55.22 | 0.005 of 0.1 (single_fast_full/unit_0) |
| gate:false_trip_corner/r2_aged | none | overvoltage, 0.38, 55.92 | overvoltage, 0.38, 55.92 | 0.006 of 0.1 (single_fast_full/unit_0) |
| gate:missed_detection_corner/r2_fresh | none | dump_fault, 0.49, 55.04 | dump_fault, 0.49, 55.04 | 0.000 of 0.1 (paired_asymmetric/unit_1) |
| gate:missed_detection_corner/r2_aged | none | overvoltage, 0.38, 55.92 | overvoltage, 0.38, 55.92 | 0.001 of 0.1 (single_fast_full/unit_0) |

A trip needs the condition held for 0.1 s. "Closest non-trip timer" is the longest the condition persisted in any case that did not trip on it (dump-failure units excluded): the margin against nuisance trips.

## Corners

- **ideal**: ideal measurements, nominal plant
- **noise_only**: measurement: {'current_gain': 0, 'current_offset_a': 0, 'voltage_gain': 0, 'voltage_offset_v': 0}
- **false_trip_corner**: measurement: {'current_gain': -0.02, 'current_offset_a': -0.2, 'voltage_gain': 0.005, 'voltage_offset_v': 0.05}; plant: {'threshold_offset_v': 0.15, 'resistance_factor': 1.1}
- **missed_detection_corner**: measurement: {'current_gain': 0.02, 'current_offset_a': 0.5, 'voltage_gain': -0.005, 'voltage_offset_v': -0.05}; plant: {'threshold_offset_v': -0.15, 'resistance_factor': 0.9}
- Noise (all non-ideal corners): {'current_sigma_a': 0.3, 'voltage_sigma_v': 0.05, 'sample_s': 0.001, 'seed': 7}; filter 0.005 s.

## Rules

- **estimated**: duty_source: estimated
- **estimated_margin_0.5**: duty_source: estimated; estimate_margin_v: 0.5
- **gate**: duty_source: gate

## Notes

- The threshold offset uses the cited 2.35 V typical / 2.50 V maximum clamp activation (0.15 V); the minimum is not cited, so the same 0.15 V is assumed below typical. Supply setpoint error, which moves the clamp's input-relative threshold, is not added separately.
- Voltage-sense gain ±0.5% is about ±0.27 V at 54 V, larger than the 0.15 V duty ramp; that is the point of the corner.
- Noise is a seeded Gaussian sequence at 1 kHz, low-pass filtered with 5 ms before the rule; one realisation per case, not a statistical false-alarm rate.

Reproduce: `make monitor-study`.
