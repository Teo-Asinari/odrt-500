# R4 candidate simulation: bank on the drive bus (bidirectional), R3 + C1

Fingerprint: `a3fc4ff5c709b4a6cee115e0477caaa70eb8033bf6c1b09a4762cc296e9ff89f`

**Assessment: REVISE.** R2 joins the [R2 CAD](r2_package.md), the [power revision](revision_power.md) and the [support revision](support_revision.md) into one simulated machine: 5:1 belt, drum-referred inertia 0.016331 kg m² (R1: 0.024254), routing 0.062 m, 20 × TV 3 V cells on the drive bus (bidirectional; one-way supply and dump unchanged), EPP-500-54 at 52 V, motor current limit 50 A. Controller: see below.

| Bank / case | Tracking % | Peak N | Bus min–max V | Winding °C | Bar ° | Trip | Failed comparisons |
|---|---:|---:|---:|---:|---:|---|---|
| r2_fresh / single_endurance_full | 21.13 | 1121 | 45.7–54.4 | 128.5 | 0.0 | none | proposed normal overshoot, proposed tracking RMS |
| r2_fresh / single_curl_full | 0.13 | 179 | 51.8–52.6 | 28.4 | 0.0 | none | none |
| r2_fresh / single_row_full | 0.11 | 538 | 50.9–54.4 | 48.6 | 0.0 | none | none |
| r2_fresh / single_press_full | 0.12 | 673 | 50.3–54.4 | 56.5 | 0.0 | none | none |
| r2_fresh / single_slow_full | 0.07 | 896 | 50.4–52.2 | 104.6 | 0.0 | none | none |
| r2_fresh / single_eccentric_full | 0.09 | 669 | 51.1–53.2 | 58.8 | 0.0 | none | none |
| r2_fresh / single_heavy_full | 0.10 | 1120 | 47.2–54.4 | 105.6 | 0.0 | none | none |
| r2_fresh / single_hold_full | 0.09 | 1120 | 49.9–52.0 | 114.2 | 0.0 | none | none |
| r2_fresh / single_low_full | 0.74 | 36 | 51.9–52.1 | 25.6 | 0.0 | none | none |
| r2_fresh / single_fast_full | 8.02 | 974 | 44.3–54.4 | 63.2 | 0.0 | none | proposed tracking RMS, recommended electrical frequency |
| r2_fresh / single_stroke_full | 10.73 | 645 | 50.1–54.4 | 36.8 | 0.0 | none | proposed normal overshoot, proposed tracking RMS, recommended electrical frequency |
| r2_fresh / paired_heavy_full | 0.11 | 1125 | 47.2–54.4 | 105.6 | 0.0 | none | none |
| r2_fresh / paired_asymmetric | 0.10 | 1121 | 47.2–54.4 | 105.3 | 0.6 | none | none |
| r2_fresh / left_power_loss_uncoordinated | 0.30 | 1250 | 48.7–54.4 | 47.5 | 76.2 | none | none |
| r2_fresh / left_power_loss_coordinated | 0.30 | 1125 | 51.0–54.4 | 33.3 | 3.6 | none | none |
| r2_fresh / left_power_loss_buffered | 0.30 | 1125 | 43.8–54.4 | 48.2 | 0.0 | none | none |
| r2_fresh / left_power_loss_buffered_coordinated | 0.30 | 1125 | 43.8–54.4 | 48.2 | 0.0 | none | none |
| r2_fresh / left_sensor_loss | 0.30 | 1129 | 51.0–54.4 | 33.2 | 1.7 | none | none |
| r2_fresh / left_encoder_loss | 0.30 | 1125 | 51.2–54.4 | 33.3 | 2.1 | none | none |
| r2_fresh / left_torque_inverted | 0.30 | 1196 | 45.1–54.4 | 33.2 | 6.0 | none | recommended electrical frequency, virtual motor voltage controllability |
| r2_fresh / left_torque_frozen | 0.30 | 1125 | 51.2–54.4 | 33.4 | 2.1 | none | none |
| r2_fresh / paired_communication_loss | 0.30 | 1125 | 51.4–54.4 | 33.3 | 0.0 | none | none |
| r2_fresh / paired_release | 0.30 | 1125 | 47.7–54.4 | 31.9 | 0.1 | none | none |
| r2_fresh / paired_release_asymmetric | 0.30 | 1125 | 47.7–54.4 | 31.9 | 46.5 | none | none |
| r2_fresh / paired_emergency_stop | 0.30 | 1125 | 51.4–54.4 | 33.0 | 0.0 | none | none |
| r2_fresh / paired_dump_failure | 1.29 | 1125 | 49.2–55.6 | 48.2 | 0.0 | none | none |
| r2_fresh / paired_dump_failure_coordinated | 1.29 | 1125 | 49.2–55.6 | 48.2 | 0.0 | none | none |
| r2_aged / single_endurance_full | 21.18 | 1121 | 37.0–54.4 | 128.5 | 0.0 | none | proposed normal overshoot, proposed tracking RMS |
| r2_aged / single_curl_full | 0.13 | 179 | 51.8–53.2 | 28.4 | 0.0 | none | none |
| r2_aged / single_row_full | 0.11 | 538 | 50.5–54.4 | 48.7 | 0.0 | none | none |
| r2_aged / single_press_full | 0.12 | 673 | 48.8–54.4 | 56.6 | 0.0 | none | none |
| r2_aged / single_slow_full | 0.07 | 896 | 50.3–52.4 | 104.6 | 0.0 | none | none |
| r2_aged / single_eccentric_full | 0.09 | 669 | 51.0–54.2 | 58.8 | 0.0 | none | none |
| r2_aged / single_heavy_full | 0.10 | 1120 | 42.1–54.4 | 105.6 | 0.0 | none | none |
| r2_aged / single_hold_full | 0.09 | 1120 | 49.2–52.0 | 114.2 | 0.0 | none | none |
| r2_aged / single_low_full | 0.74 | 36 | 51.9–52.3 | 25.6 | 0.0 | none | none |
| r2_aged / single_fast_full | 12.08 | 1024 | 33.3–54.4 | 63.2 | 0.0 | none | proposed normal overshoot, proposed tracking RMS, recommended electrical frequency |
| r2_aged / single_stroke_full | 11.49 | 648 | 48.6–54.4 | 36.8 | 0.0 | none | proposed normal overshoot, proposed tracking RMS, recommended electrical frequency |
| r2_aged / paired_heavy_full | 0.11 | 1125 | 42.1–54.4 | 105.6 | 0.0 | none | none |
| r2_aged / paired_asymmetric | 0.10 | 1121 | 42.2–54.4 | 105.3 | 0.6 | none | none |
| r2_aged / left_power_loss_uncoordinated | 0.30 | 1249 | 43.3–54.4 | 47.5 | 76.2 | none | none |
| r2_aged / left_power_loss_coordinated | 0.30 | 1125 | 50.4–54.4 | 33.3 | 3.6 | none | none |
| r2_aged / left_power_loss_buffered | 0.30 | 1125 | 33.7–54.4 | 48.2 | 0.0 | none | none |
| r2_aged / left_power_loss_buffered_coordinated | 0.30 | 1125 | 33.7–54.4 | 48.2 | 0.0 | none | none |
| r2_aged / left_sensor_loss | 0.30 | 1129 | 50.4–54.4 | 33.2 | 1.7 | none | none |
| r2_aged / left_encoder_loss | 0.30 | 1125 | 50.6–54.4 | 33.3 | 2.1 | none | none |
| r2_aged / left_torque_inverted | 0.30 | 1189 | 43.7–54.4 | 33.2 | 6.0 | none | recommended electrical frequency, virtual motor voltage controllability |
| r2_aged / left_torque_frozen | 0.30 | 1125 | 50.6–54.4 | 33.4 | 2.1 | none | none |
| r2_aged / paired_communication_loss | 0.30 | 1125 | 51.2–54.4 | 33.3 | 0.0 | none | none |
| r2_aged / paired_release | 0.30 | 1125 | 42.2–54.4 | 31.8 | 0.1 | none | none |
| r2_aged / paired_release_asymmetric | 0.30 | 1125 | 42.2–54.4 | 31.8 | 46.5 | none | none |
| r2_aged / paired_emergency_stop | 0.30 | 1125 | 51.2–54.4 | 33.0 | 0.0 | none | none |
| r2_aged / paired_dump_failure | 1.29 | 1248 | 45.4–57.0 | 47.4 | 76.2 | overvoltage | none |
| r2_aged / paired_dump_failure_coordinated | 1.29 | 1125 | 51.2–57.0 | 30.5 | 0.5 | overvoltage | none |

## Numerical refinement

| Case | Max medium–fine change | Outcome |
|---|---:|---|
| r2_fresh__single_heavy_full | 0.000% | pass |
| r2_aged__single_fast_full | 0.000% | pass |
| r2_fresh__paired_release_asymmetric | 0.002% | pass |
| r2_aged__left_power_loss_buffered_coordinated | 0.022% | pass |

## Conducted heat path

The motor housing conducts through the stator carrier/pedestal into a 2 mm aluminium base and skin acting as one lumped frame node. The frame loses heat to the room through its exposed outer faces and to the internal forced airflow through its inner faces. The R2 CAD geometry is unchanged; only the interface and the material choice are new.

| Parameter | Nominal | Bounds | Basis |
|---|---:|---|---|
| housing_to_frame_k_w | 0.3 | [0.15, 0.8] | About 0.05 K/W greased/padded interface over the ~9200 mm² motor face (2000-5000 W/m²K) plus ~0.2 K/W spreading in a 2 mm base, ln(r2/r1)/(2πkt). The RO100 case-to-stator path is unknown and not potted; that is why the upper bound is high. |
| frame_capacity_j_k | 800 | [400, 1200] | About 0.9 kg of aluminium base and 2 mm skin at 900 J/kg/K. |
| frame_to_room_w_k | 1.4 | [0.7, 2.0] | About 0.137 m² of exposed outer area (mounted base face excluded) at ~10 W/m²K natural convection plus black-finish radiation for a 30-40 K rise. Conduction into the board/wall mount is ignored. |
| frame_to_air_w_k | 1.5 | [0.5, 3.0] | About 0.15 m² of inner skin at ~10 W/m²K under the conditional 25 CFM internal flow; flow distribution is not demonstrated. |

## Controller

Variant `kp_4_retract_2.5_end_zone` from the [controller study](control_study.md): kp=4.0, retract_speed_limit_m_s=2.5, end_zone_m=0.15, end_zone_gain_n_s_m=600. All other control values are the reference.

## Undervoltage trip

Trip lowered to 30 V ([ODrive Pro](https://docs.odriverobotics.com/v/latest/hardware/pro-datasheet.html) DC range 15–58 V). The 40 V trip was a reference choice, not a drive limit. 30 V keeps 2x margin above the documented 15 V minimum. Whether the motor can still be controlled at the reached speed is judged by the existing voltage-controllability and modulation screens, which stay unchanged. Usable aged-bank energy from 52 V rises from about 0.5*3.15*(52^2-40^2) = 1.74 kJ to 0.5*3.15*(52^2-30^2) = 2.84 kJ, before ESR losses.

- Supply constant-current limiting means delivered power falls with bus voltage; a constant-power supply mode is not assumed.
- Auxiliary/logic rails, sensors and the supervisor must be specified to ride through 30 V.
- Low-voltage operation raises bank and wiring currents for the same power; ESR heating is captured, connector/wiring ratings are not.

## Bank on the drive bus: hardware checks at the simulated envelope

In R3 + C1 fast reversal the one-way clamp dumps 317 W of regeneration and the aged bank reaches the 30 V trip. With the bank on the drive bus the fast-motion study dumps 49 W and the aged fast reversal no longer trips. The supply stays one-way; the dump thresholds and trip are unchanged.

| Check | Simulated | Limit / basis | Outcome |
|---|---:|---|---|
| Worst cell (max bank 53.68 V / 20 × 1.05) | 2.818 V | 3 V rated | pass |
| Worst cell at the 57 V trip | 2.993 V | 3 V rated | pass |
| Bank RMS current over one set, worst (r2_aged / single_fast_full) | 14.2 A | 11.7 A continuous (15 K rise) | exceeds continuous rating in r2_aged/single_fast_full, r2_fresh/single_fast_full; cells reach 29.0 °C over the 18 s set |
| Cell temperature if that set repeated continuously (fresh / aged ESR, 25 °C) | 47 / 70 °C | 65 °C case maximum | FAIL: back-to-back sets of this case need a bank duty limit or cooling |
| Supply peak current | 9.6 A | 9.6 A limit | one-way source assumed |
| Reverse-blocking loss at peak | 0.46 W | assumed 0.005 Ω | no part selected |

| Bank | Capacitance F | Pre-charge at supply limit s | Bank energy at setpoint J |
|---|---:|---:|---:|
| r2_fresh | 5.00 | 27.0 | 6760 |
| r2_aged | 3.15 | 17.0 | 4259 |

If the supply does not current-limit cleanly into the bank, a pre-charge resistor needs at least 5.4 Ω and must absorb the bank energy as a pulse. Drive enable is interlocked above 45 V. Cycle-averaged current only. Drive PWM-frequency ripple is assumed to stay in the drive-bus capacitors; bus wiring inductance is not modelled.

- Verify the EPP-500-54 overload behaviour (constant current vs hiccup) into a capacitive load; it decides the pre-charge circuit.
- Select the ideal-diode controller and pre-charge parts; add them to the electrical definition and cost allowances.
- Bank wiring inductance, fusing and a bank-disconnect for service are not designed.
- Cell balancing (passive or active) is not designed; the worst-cell factor is an assumption.

## Uncertainties (paired heavy set, fresh bank; heat-path bounds on the slow heavy pull; controller variants as name:bank:case)

| Perturbation | Tracking % | Winding °C | Minimum bus V | Trip | Failed comparisons |
|---|---:|---:|---:|---|---|
| nominal | 0.11 | 105.6 | 47.2 | none | none |
| half_airflow | 0.11 | 105.6 | 47.2 | none | none |
| quarter_airflow | 0.11 | 105.6 | 47.2 | none | none |
| long_routing | 0.11 | 105.6 | 47.2 | none | none |
| low_km | 75.02 | 123.6 | 30.0 | undervoltage | latched protective trip during normal operation, proposed tracking RMS |
| warm_room | 0.86 | 124.6 | 46.6 | none | drive rated ambient conditions |
| extra_inertia | 0.11 | 105.3 | 47.2 | none | none |
| realisable_feedforward:r2_fresh:single_fast_full | 9.74 | 63.4 | 44.3 | none | proposed normal overshoot, proposed tracking RMS, recommended electrical frequency |
| realisable_feedforward:r2_fresh:single_stroke_full | 11.17 | 36.8 | 50.1 | none | proposed normal overshoot, proposed tracking RMS, recommended electrical frequency |
| realisable_feedforward:r2_fresh:paired_heavy_full | 0.22 | 105.4 | 47.2 | none | none |
| realisable_feedforward:r2_fresh:paired_asymmetric | 0.22 | 105.1 | 47.2 | none | none |
| realisable_feedforward:r2_aged:single_fast_full | 13.57 | 63.1 | 32.8 | none | proposed normal overshoot, proposed tracking RMS, recommended electrical frequency |
| realisable_feedforward:r2_aged:single_stroke_full | 11.94 | 36.8 | 48.5 | none | proposed normal overshoot, proposed tracking RMS, recommended electrical frequency |
| realisable_feedforward:r2_aged:paired_heavy_full | 0.22 | 105.4 | 42.1 | none | none |
| realisable_feedforward:r2_aged:paired_asymmetric | 0.22 | 105.1 | 42.1 | none | none |

## Support screen at simulated R2 loads

Peak rope force 1250 N and peak current 90.4 A × Kt = 18.08 Nm, combined as uncorrelated corners; belt tension difference 1577 N. 8/16 corners pass.

| Preload N/span | Rope z mm | Torque sign | Motor C0/P | Drum C0/P | Motor shaft MPa | Drum shaft MPa | Failed screens |
|---:|---:|---:|---:|---:|---:|---:|---|
| 700 | 28.5 | -1 | 2.74 | 7.36 | 85.6 | 12.0 | nonpositive nominal slack tension |
| 700 | 28.5 | 1 | 2.74 | 8.07 | 85.6 | 14.5 | nonpositive nominal slack tension |
| 700 | 53.5 | -1 | 2.74 | 8.42 | 85.6 | 11.9 | nonpositive nominal slack tension |
| 700 | 53.5 | 1 | 2.74 | 6.15 | 85.6 | 16.7 | nonpositive nominal slack tension |
| 850 | 28.5 | -1 | 2.57 | 6.95 | 89.6 | 12.0 | none |
| 850 | 28.5 | 1 | 2.57 | 7.54 | 89.6 | 14.5 | none |
| 850 | 53.5 | -1 | 2.57 | 7.82 | 89.6 | 12.2 | none |
| 850 | 53.5 | 1 | 2.57 | 5.90 | 89.6 | 16.8 | none |
| 1000 | 28.5 | -1 | 2.23 | 6.09 | 99.7 | 12.2 | none |
| 1000 | 28.5 | 1 | 2.23 | 6.47 | 99.7 | 14.6 | none |
| 1000 | 53.5 | -1 | 2.23 | 6.65 | 99.7 | 12.8 | none |
| 1000 | 53.5 | 1 | 2.23 | 5.35 | 99.7 | 17.3 | none |
| 1150 | 28.5 | -1 | 1.96 | 5.41 | 110.3 | 12.4 | motor bearing static factor |
| 1150 | 28.5 | 1 | 1.96 | 5.67 | 110.3 | 14.8 | motor bearing static factor |
| 1150 | 53.5 | -1 | 1.96 | 5.79 | 110.3 | 13.5 | motor bearing static factor |
| 1150 | 53.5 | 1 | 1.96 | 4.86 | 110.3 | 17.8 | motor bearing static factor |

## Limits

- The bank joins the drive bus through its ESR only; wiring inductance, fusing and pre-charge transients are not modelled.
- Thermal resistances/capacities remain reference proposals; the TV cell heat capacity is assumed.
- Ideal radial supports; deck/bridge/side-wall stiffness, joints, fatigue and belt rating are not checked.
- Uncertainty perturbations co-vary plant and feedforward; independent miscalibration is not covered.
- No wiring, tray, retention, isolation or cooling geometry is qualified by the CAD space claim.

Reproduce: `make r4-candidate` (parallel; `JOBS=n` limits workers).
