# R4 with the Kollmorgen TBM2G-11526D at 6:1 (motor study variant tbm_6; study, not adopted)

Fingerprint: `77166a52e849ea3634d41db6eaa64f6232903bd214a44856e81c1df745f2f11b`

**Assessment: REVISE.** R2 joins the [R2 CAD](r2_package.md), the [power revision](revision_power.md) and the [support revision](support_revision.md) into one simulated machine: 6:1 belt, drum-referred inertia 0.016331 kg m² (R1: 0.024254), routing 0.062 m, 20 × TV 3 V cells on the drive bus (bidirectional; one-way supply and dump unchanged), EPP-500-54 at 52 V, motor current limit 69.3 A. Controller: see below.

| Bank / case | Tracking % | Peak N | Bus min–max V | Winding °C | Bar ° | Trip | Failed comparisons |
|---|---:|---:|---:|---:|---:|---|---|
| r2_fresh / single_endurance_full | 0.07 | 1121 | 50.2–54.4 | 74.2 | 0.0 | none | none |
| r2_fresh / single_curl_full | 0.13 | 179 | 51.8–52.6 | 26.5 | 0.0 | none | none |
| r2_fresh / single_row_full | 0.10 | 538 | 51.2–54.4 | 33.1 | 0.0 | none | none |
| r2_fresh / single_press_full | 0.12 | 673 | 50.7–54.4 | 35.5 | 0.0 | none | none |
| r2_fresh / single_slow_full | 0.07 | 896 | 51.2–53.2 | 46.4 | 0.0 | none | none |
| r2_fresh / single_eccentric_full | 0.09 | 669 | 51.5–53.4 | 35.2 | 0.0 | none | none |
| r2_fresh / single_heavy_full | 0.10 | 1120 | 50.4–54.4 | 47.0 | 0.0 | none | none |
| r2_fresh / single_hold_full | 0.09 | 1120 | 51.1–52.6 | 48.3 | 0.0 | none | none |
| r2_fresh / single_low_full | 0.72 | 36 | 51.9–52.1 | 25.5 | 0.0 | none | none |
| r2_fresh / single_fast_full | 1.93 | 913 | 43.6–54.4 | 37.0 | 0.0 | none | none |
| r2_fresh / single_stroke_full | 1.05 | 532 | 50.5–54.4 | 29.5 | 0.0 | none | proposed normal overshoot |
| r2_fresh / paired_heavy_full | 0.11 | 1124 | 50.4–54.4 | 47.0 | 0.0 | none | none |
| r2_fresh / paired_asymmetric | 0.10 | 1121 | 50.4–54.4 | 46.9 | 0.6 | none | none |
| r2_fresh / left_power_loss_uncoordinated | 0.30 | 1375 | 49.0–54.4 | 31.7 | 76.3 | none | none |
| r2_fresh / left_power_loss_coordinated | 0.30 | 1124 | 51.4–54.4 | 27.4 | 4.7 | none | none |
| r2_fresh / left_power_loss_buffered | 0.30 | 1124 | 47.7–54.4 | 31.9 | 0.0 | none | none |
| r2_fresh / left_power_loss_buffered_coordinated | 0.30 | 1124 | 47.7–54.4 | 31.9 | 0.0 | none | none |
| r2_fresh / left_sensor_loss | 0.30 | 1145 | 51.0–54.4 | 27.4 | 2.0 | none | none |
| r2_fresh / left_encoder_loss | 0.30 | 1124 | 51.7–54.4 | 27.4 | 2.7 | none | none |
| r2_fresh / left_torque_inverted | 0.30 | 1188 | 43.6–54.4 | 27.4 | 7.8 | none | virtual motor voltage controllability |
| r2_fresh / left_torque_frozen | 0.30 | 1124 | 51.7–54.4 | 27.4 | 2.7 | none | none |
| r2_fresh / paired_communication_loss | 0.30 | 1124 | 51.8–54.4 | 27.4 | 0.0 | none | none |
| r2_fresh / paired_release | 0.30 | 1124 | 45.7–54.4 | 27.1 | 0.8 | none | none |
| r2_fresh / paired_release_asymmetric | 0.30 | 1124 | 45.7–54.4 | 27.1 | 46.0 | none | none |
| r2_fresh / paired_emergency_stop | 0.30 | 1124 | 51.8–54.4 | 27.3 | 0.0 | none | none |
| r2_fresh / paired_dump_failure | 1.29 | 1375 | 50.3–55.4 | 31.7 | 76.3 | dump_fault | none |
| r2_fresh / paired_dump_failure_coordinated | 1.29 | 1124 | 51.8–55.4 | 26.4 | 1.1 | dump_fault | none |
| r2_aged / single_endurance_full | 0.07 | 1121 | 48.3–54.4 | 74.8 | 0.0 | none | none |
| r2_aged / single_curl_full | 0.13 | 179 | 51.8–53.3 | 26.5 | 0.0 | none | none |
| r2_aged / single_row_full | 0.10 | 538 | 50.8–54.4 | 33.2 | 0.0 | none | none |
| r2_aged / single_press_full | 0.12 | 673 | 50.1–54.4 | 35.6 | 0.0 | none | none |
| r2_aged / single_slow_full | 0.07 | 896 | 51.1–54.1 | 46.4 | 0.0 | none | none |
| r2_aged / single_eccentric_full | 0.09 | 669 | 51.4–54.4 | 35.2 | 0.0 | none | none |
| r2_aged / single_heavy_full | 0.10 | 1120 | 50.0–54.4 | 47.0 | 0.0 | none | none |
| r2_aged / single_hold_full | 0.09 | 1120 | 51.0–53.1 | 48.3 | 0.0 | none | none |
| r2_aged / single_low_full | 0.72 | 36 | 51.9–52.3 | 25.5 | 0.0 | none | none |
| r2_aged / single_fast_full | 6.33 | 965 | 30.9–54.4 | 37.0 | 0.0 | none | proposed tracking RMS |
| r2_aged / single_stroke_full | 1.05 | 532 | 49.5–54.4 | 29.5 | 0.0 | none | proposed normal overshoot |
| r2_aged / paired_heavy_full | 0.11 | 1124 | 50.0–54.4 | 47.0 | 0.0 | none | none |
| r2_aged / paired_asymmetric | 0.10 | 1121 | 50.0–54.4 | 46.9 | 0.6 | none | none |
| r2_aged / left_power_loss_uncoordinated | 0.30 | 1375 | 43.4–54.4 | 31.7 | 76.3 | none | none |
| r2_aged / left_power_loss_coordinated | 0.30 | 1124 | 50.8–54.4 | 27.4 | 4.7 | none | none |
| r2_aged / left_power_loss_buffered | 0.30 | 1124 | 42.2–54.4 | 31.9 | 0.0 | none | none |
| r2_aged / left_power_loss_buffered_coordinated | 0.30 | 1124 | 42.2–54.4 | 31.9 | 0.0 | none | none |
| r2_aged / left_sensor_loss | 0.30 | 1145 | 50.2–54.4 | 27.4 | 2.0 | none | none |
| r2_aged / left_encoder_loss | 0.30 | 1124 | 51.3–54.4 | 27.4 | 2.7 | none | none |
| r2_aged / left_torque_inverted | 0.30 | 1176 | 42.2–54.4 | 27.4 | 7.6 | none | virtual motor voltage controllability |
| r2_aged / left_torque_frozen | 0.30 | 1124 | 51.3–54.4 | 27.4 | 2.7 | none | none |
| r2_aged / paired_communication_loss | 0.30 | 1124 | 51.7–54.4 | 27.4 | 0.0 | none | none |
| r2_aged / paired_release | 0.30 | 1124 | 42.4–54.4 | 27.1 | 0.2 | none | none |
| r2_aged / paired_release_asymmetric | 0.30 | 1124 | 42.4–54.4 | 27.1 | 46.1 | none | none |
| r2_aged / paired_emergency_stop | 0.30 | 1124 | 51.7–54.4 | 27.3 | 0.0 | none | none |
| r2_aged / paired_dump_failure | 1.29 | 1373 | 49.0–55.9 | 31.7 | 76.3 | overvoltage | none |
| r2_aged / paired_dump_failure_coordinated | 1.29 | 1124 | 51.7–55.9 | 26.3 | 1.6 | overvoltage | none |

## Numerical refinement

| Case | Max medium–fine change | Outcome |
|---|---:|---|
| r2_fresh__single_heavy_full | 0.000% | pass |
| r2_aged__single_fast_full | 0.001% | pass |
| r2_fresh__paired_release_asymmetric | 0.040% | pass |
| r2_aged__left_power_loss_buffered_coordinated | 0.028% | pass |

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

In R3 + C1 fast reversal the one-way clamp dumps 317 W of regeneration and the aged bank reaches the 30 V trip. With the bank on the drive bus the fast-motion study dumps 49 W and the aged fast reversal no longer trips. The supply stays one-way and the dump thresholds are unchanged; the overvoltage trip is lowered to 56 V (below).

| Check | Simulated | Limit / basis | Outcome |
|---|---:|---|---|
| Worst cell (max bank 53.74 V / 20 × 1.05) | 2.821 V | 3 V rated | pass |
| Worst cell at the 56 V trip | 2.940 V | 3 V rated | pass |
| Bank RMS current over one set, worst (r2_aged / single_fast_full) | 16.7 A | 11.7 A continuous (15 K rise) | exceeds continuous rating in r2_aged/single_fast_full, r2_fresh/single_fast_full; cells reach 30.4 °C over the 18 s set |
| Cell temperature if that set repeated continuously (fresh / aged ESR, 25 °C) | 56 / 87 °C | 65 °C case maximum | FAIL: back-to-back sets of this case need a bank duty limit or cooling |
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
| nominal | 0.11 | 47.0 | 50.4 | none | none |
| half_airflow | 0.11 | 47.0 | 50.4 | none | none |
| quarter_airflow | 0.11 | 47.0 | 50.4 | none | none |
| long_routing | 0.11 | 47.0 | 50.4 | none | none |
| low_km | 0.11 | 81.6 | 49.2 | none | none |
| warm_room | 0.11 | 63.2 | 50.4 | none | drive rated ambient conditions |
| extra_inertia | 0.11 | 47.0 | 50.4 | none | none |
| realisable_feedforward:r2_fresh:single_fast_full | 4.09 | 37.1 | 43.3 | none | none |
| realisable_feedforward:r2_fresh:single_stroke_full | 1.25 | 29.5 | 50.5 | none | proposed normal overshoot |
| realisable_feedforward:r2_fresh:paired_heavy_full | 0.21 | 47.0 | 50.4 | none | none |
| realisable_feedforward:r2_fresh:paired_asymmetric | 0.21 | 46.9 | 50.4 | none | none |
| realisable_feedforward:r2_aged:single_fast_full | 32.86 | 35.8 | 30.1 | undervoltage | latched protective trip during normal operation, proposed normal overshoot, proposed tracking RMS |
| realisable_feedforward:r2_aged:single_stroke_full | 1.25 | 29.5 | 49.4 | none | proposed normal overshoot |
| realisable_feedforward:r2_aged:paired_heavy_full | 0.21 | 47.0 | 49.9 | none | none |
| realisable_feedforward:r2_aged:paired_asymmetric | 0.21 | 46.9 | 49.9 | none | none |

## Support screen at simulated R2 loads

Peak rope force 1375 N and peak current 91.0 A × Kt = 12.04 Nm, combined as uncorrelated corners; belt tension difference 1051 N. 16/16 corners pass.

| Preload N/span | Rope z mm | Torque sign | Motor C0/P | Drum C0/P | Motor shaft MPa | Drum shaft MPa | Failed screens |
|---:|---:|---:|---:|---:|---:|---:|---|
| 700 | 28.5 | -1 | 3.20 | 8.57 | 68.8 | 13.6 | none |
| 700 | 28.5 | 1 | 3.20 | 9.39 | 68.8 | 15.3 | none |
| 700 | 53.5 | -1 | 3.20 | 9.11 | 68.8 | 13.5 | none |
| 700 | 53.5 | 1 | 3.20 | 6.88 | 68.8 | 16.8 | none |
| 850 | 28.5 | -1 | 2.67 | 7.28 | 79.6 | 13.7 | none |
| 850 | 28.5 | 1 | 2.67 | 7.76 | 79.6 | 15.4 | none |
| 850 | 53.5 | -1 | 2.67 | 7.60 | 79.6 | 14.0 | none |
| 850 | 53.5 | 1 | 2.67 | 6.16 | 79.6 | 17.2 | none |
| 1000 | 28.5 | -1 | 2.29 | 6.31 | 90.8 | 13.9 | none |
| 1000 | 28.5 | 1 | 2.29 | 6.62 | 90.8 | 15.5 | none |
| 1000 | 53.5 | -1 | 2.29 | 6.52 | 90.8 | 14.6 | none |
| 1000 | 53.5 | 1 | 2.29 | 5.54 | 90.8 | 17.7 | none |
| 1150 | 28.5 | -1 | 2.01 | 5.56 | 102.3 | 14.0 | none |
| 1150 | 28.5 | 1 | 2.01 | 5.76 | 102.3 | 15.6 | none |
| 1150 | 53.5 | -1 | 2.01 | 5.70 | 102.3 | 15.2 | none |
| 1150 | 53.5 | 1 | 2.01 | 5.01 | 102.3 | 18.2 | none |

## Limits

- The bank joins the drive bus through its ESR only; wiring inductance, fusing and pre-charge transients are not modelled.
- Thermal resistances/capacities remain reference proposals; the TV cell heat capacity is assumed.
- Ideal radial supports; deck/bridge/side-wall stiffness, joints, fatigue and belt rating are not checked.
- Uncertainty perturbations co-vary plant and feedforward; independent miscalibration is not covered.
- No wiring, tray, retention, isolation or cooling geometry is qualified by the CAD space claim.

Reproduce: `make r4m-candidate` (parallel; `JOBS=n` limits workers).
