# R3 with candidate controller C1 (kp 4, 2.5 m/s release limiter, 0.15 m end zone)

Fingerprint: `4740ff458aa3edcfb59ab57ddc83652f7eea0238f6f6a1f263da4b1f9a0c2974`

**Assessment: REVISE.** R2 joins the [R2 CAD](r2_package.md), the [power revision](revision_power.md) and the [support revision](support_revision.md) into one simulated machine: 5:1 belt, drum-referred inertia 0.016331 kg m² (R1: 0.024254), routing 0.062 m, 20 × TV 3 V cells upstream of a Regen Clamp, EPP-500-54 at 52 V, motor current limit 50 A. Controller: see below.

| Bank / case | Tracking % | Peak N | Bus min–max V | Winding °C | Bar ° | Trip | Failed comparisons |
|---|---:|---:|---:|---:|---:|---|---|
| r2_fresh / single_endurance_full | 21.35 | 1121 | 45.1–53.0 | 128.6 | 0.0 | none | proposed normal overshoot, proposed tracking RMS |
| r2_fresh / single_curl_full | 0.13 | 179 | 51.7–52.8 | 28.4 | 0.0 | none | none |
| r2_fresh / single_row_full | 0.11 | 538 | 50.6–53.0 | 48.9 | 0.0 | none | none |
| r2_fresh / single_press_full | 0.12 | 673 | 49.5–53.1 | 56.8 | 0.0 | none | none |
| r2_fresh / single_slow_full | 0.07 | 896 | 50.4–52.7 | 104.6 | 0.0 | none | none |
| r2_fresh / single_eccentric_full | 0.09 | 669 | 51.0–52.9 | 58.9 | 0.0 | none | none |
| r2_fresh / single_heavy_full | 0.10 | 1120 | 46.3–53.1 | 105.6 | 0.0 | none | none |
| r2_fresh / single_hold_full | 0.09 | 1120 | 49.9–52.0 | 114.2 | 0.0 | none | none |
| r2_fresh / single_low_full | 0.74 | 36 | 51.9–52.8 | 25.6 | 0.0 | none | none |
| r2_fresh / single_fast_full | 11.36 | 1064 | 34.8–53.5 | 63.1 | 0.0 | none | proposed normal overshoot, proposed tracking RMS, recommended electrical frequency |
| r2_fresh / single_stroke_full | 14.14 | 648 | 49.3–53.2 | 36.9 | 0.0 | none | proposed normal overshoot, proposed tracking RMS, recommended electrical frequency |
| r2_fresh / paired_heavy_full | 0.11 | 1125 | 46.3–53.1 | 105.6 | 0.0 | none | none |
| r2_fresh / paired_asymmetric | 0.10 | 1121 | 46.4–53.1 | 105.3 | 0.6 | none | none |
| r2_fresh / left_power_loss_uncoordinated | 0.30 | 1249 | 47.6–53.1 | 47.5 | 76.2 | none | none |
| r2_fresh / left_power_loss_coordinated | 0.30 | 1125 | 50.5–53.1 | 33.3 | 3.6 | none | none |
| r2_fresh / left_power_loss_buffered | 0.30 | 1125 | 42.6–53.1 | 48.2 | 0.0 | none | none |
| r2_fresh / left_power_loss_buffered_coordinated | 0.30 | 1125 | 42.6–53.1 | 48.2 | 0.0 | none | none |
| r2_fresh / left_sensor_loss | 0.30 | 1129 | 50.5–53.1 | 33.2 | 1.7 | none | none |
| r2_fresh / left_encoder_loss | 0.30 | 1125 | 50.7–53.1 | 33.3 | 2.1 | none | none |
| r2_fresh / left_torque_inverted | 0.30 | 1197 | 43.9–53.1 | 33.2 | 6.0 | none | recommended electrical frequency, virtual motor voltage controllability |
| r2_fresh / left_torque_frozen | 0.30 | 1125 | 50.7–53.1 | 33.4 | 2.1 | none | none |
| r2_fresh / paired_communication_loss | 0.30 | 1125 | 51.3–53.1 | 33.3 | 0.0 | none | none |
| r2_fresh / paired_release | 0.30 | 1125 | 47.2–53.1 | 31.8 | 0.3 | none | none |
| r2_fresh / paired_release_asymmetric | 0.30 | 1125 | 47.2–53.1 | 31.8 | 46.6 | none | none |
| r2_fresh / paired_emergency_stop | 0.30 | 1125 | 51.3–53.1 | 33.0 | 0.0 | none | none |
| r2_fresh / paired_dump_failure | 1.29 | 1248 | 48.5–56.9 | 47.3 | 76.2 | overvoltage | none |
| r2_fresh / paired_dump_failure_coordinated | 1.29 | 1125 | 51.4–56.9 | 29.9 | 1.5 | overvoltage | none |
| r2_aged / single_endurance_full | 21.39 | 1121 | 32.9–53.0 | 128.6 | 0.0 | none | proposed normal overshoot, proposed tracking RMS |
| r2_aged / single_curl_full | 0.13 | 179 | 51.7–52.8 | 28.4 | 0.0 | none | none |
| r2_aged / single_row_full | 0.11 | 538 | 50.3–53.0 | 48.9 | 0.0 | none | none |
| r2_aged / single_press_full | 0.12 | 673 | 47.7–53.2 | 56.8 | 0.0 | none | none |
| r2_aged / single_slow_full | 0.07 | 896 | 50.3–52.7 | 104.6 | 0.0 | none | none |
| r2_aged / single_eccentric_full | 0.09 | 669 | 51.0–52.9 | 58.9 | 0.0 | none | none |
| r2_aged / single_heavy_full | 0.10 | 1120 | 40.1–53.1 | 105.6 | 0.0 | none | none |
| r2_aged / single_hold_full | 0.09 | 1120 | 49.1–52.0 | 114.2 | 0.0 | none | none |
| r2_aged / single_low_full | 0.74 | 36 | 51.9–52.8 | 25.6 | 0.0 | none | none |
| r2_aged / single_fast_full | 62.00 | 1109 | 30.2–53.5 | 49.8 | 0.0 | undervoltage | latched protective trip during normal operation, proposed normal overshoot, proposed tracking RMS, recommended electrical frequency |
| r2_aged / single_stroke_full | 14.51 | 664 | 47.7–53.2 | 36.9 | 0.0 | none | proposed normal overshoot, proposed tracking RMS, recommended electrical frequency |
| r2_aged / paired_heavy_full | 0.11 | 1125 | 40.1–53.1 | 105.6 | 0.0 | none | none |
| r2_aged / paired_asymmetric | 0.10 | 1121 | 40.2–53.1 | 105.3 | 0.6 | none | none |
| r2_aged / left_power_loss_uncoordinated | 0.30 | 1250 | 42.0–53.1 | 47.5 | 76.2 | none | none |
| r2_aged / left_power_loss_coordinated | 0.30 | 1125 | 50.1–53.1 | 33.3 | 3.6 | none | none |
| r2_aged / left_power_loss_buffered | 0.30 | 1125 | 32.1–53.1 | 48.2 | 0.0 | none | none |
| r2_aged / left_power_loss_buffered_coordinated | 0.30 | 1125 | 32.1–53.1 | 48.2 | 0.0 | none | none |
| r2_aged / left_sensor_loss | 0.30 | 1129 | 50.1–53.1 | 33.2 | 1.7 | none | none |
| r2_aged / left_encoder_loss | 0.30 | 1125 | 50.4–53.1 | 33.3 | 2.1 | none | none |
| r2_aged / left_torque_inverted | 0.30 | 1188 | 40.3–53.1 | 33.2 | 6.0 | none | recommended electrical frequency, virtual motor voltage controllability |
| r2_aged / left_torque_frozen | 0.30 | 1125 | 50.4–53.1 | 33.4 | 2.1 | none | none |
| r2_aged / paired_communication_loss | 0.30 | 1125 | 51.2–53.1 | 33.3 | 0.0 | none | none |
| r2_aged / paired_release | 0.30 | 1125 | 44.0–53.1 | 31.8 | 0.3 | none | none |
| r2_aged / paired_release_asymmetric | 0.30 | 1125 | 44.0–53.1 | 31.8 | 46.6 | none | none |
| r2_aged / paired_emergency_stop | 0.30 | 1125 | 51.2–53.1 | 33.0 | 0.0 | none | none |
| r2_aged / paired_dump_failure | 1.29 | 1247 | 45.7–56.9 | 47.3 | 76.2 | overvoltage | none |
| r2_aged / paired_dump_failure_coordinated | 1.29 | 1125 | 51.2–56.9 | 29.9 | 1.5 | overvoltage | none |

## Numerical refinement

| Case | Max medium–fine change | Outcome |
|---|---:|---|
| r2_fresh__single_heavy_full | 0.000% | pass |
| r2_aged__single_fast_full | 0.001% | pass |
| r2_fresh__paired_release_asymmetric | 0.003% | pass |
| r2_aged__left_power_loss_buffered_coordinated | 0.001% | pass |

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

## Uncertainties (paired heavy set, fresh bank; heat-path bounds on the slow heavy pull; controller variants as name:bank:case)

| Perturbation | Tracking % | Winding °C | Minimum bus V | Trip | Failed comparisons |
|---|---:|---:|---:|---|---|
| nominal | 0.11 | 105.6 | 46.3 | none | none |
| half_airflow | 0.11 | 105.6 | 46.3 | none | none |
| quarter_airflow | 0.11 | 105.6 | 46.3 | none | none |
| long_routing | 0.11 | 105.6 | 46.3 | none | none |
| low_km | 75.70 | 121.5 | 30.0 | undervoltage | latched protective trip during normal operation, proposed tracking RMS |
| warm_room | 0.87 | 124.6 | 45.8 | none | drive rated ambient conditions |
| extra_inertia | 0.11 | 105.3 | 46.4 | none | none |

## Support screen at simulated R2 loads

Peak rope force 1250 N and peak current 90.5 A × Kt = 18.11 Nm, combined as uncorrelated corners; belt tension difference 1580 N. 8/16 corners pass.

| Preload N/span | Rope z mm | Torque sign | Motor C0/P | Drum C0/P | Motor shaft MPa | Drum shaft MPa | Failed screens |
|---:|---:|---:|---:|---:|---:|---:|---|
| 700 | 28.5 | -1 | 2.73 | 7.35 | 85.8 | 12.0 | nonpositive nominal slack tension |
| 700 | 28.5 | 1 | 2.73 | 8.06 | 85.8 | 14.5 | nonpositive nominal slack tension |
| 700 | 53.5 | -1 | 2.73 | 8.41 | 85.8 | 11.9 | nonpositive nominal slack tension |
| 700 | 53.5 | 1 | 2.73 | 6.14 | 85.8 | 16.7 | nonpositive nominal slack tension |
| 850 | 28.5 | -1 | 2.57 | 6.95 | 89.6 | 12.0 | none |
| 850 | 28.5 | 1 | 2.57 | 7.54 | 89.6 | 14.5 | none |
| 850 | 53.5 | -1 | 2.57 | 7.82 | 89.6 | 12.2 | none |
| 850 | 53.5 | 1 | 2.57 | 5.90 | 89.6 | 16.8 | none |
| 1000 | 28.5 | -1 | 2.23 | 6.09 | 99.7 | 12.2 | none |
| 1000 | 28.5 | 1 | 2.23 | 6.47 | 99.7 | 14.7 | none |
| 1000 | 53.5 | -1 | 2.23 | 6.65 | 99.7 | 12.8 | none |
| 1000 | 53.5 | 1 | 2.23 | 5.34 | 99.7 | 17.3 | none |
| 1150 | 28.5 | -1 | 1.96 | 5.41 | 110.3 | 12.4 | motor bearing static factor |
| 1150 | 28.5 | 1 | 1.96 | 5.67 | 110.3 | 14.8 | motor bearing static factor |
| 1150 | 53.5 | -1 | 1.96 | 5.79 | 110.3 | 13.5 | motor bearing static factor |
| 1150 | 53.5 | 1 | 1.96 | 4.86 | 110.3 | 17.8 | motor bearing static factor |

## Limits

- Clamp is cycle-averaged; switching ripple, delay and peaks are not resolved. Upstream storage cannot absorb regeneration.
- Thermal resistances/capacities remain reference proposals; the TV cell heat capacity is assumed.
- Ideal radial supports; deck/bridge/side-wall stiffness, joints, fatigue and belt rating are not checked.
- Uncertainty perturbations co-vary plant and feedforward; independent miscalibration is not covered.
- No wiring, tray, retention, isolation or cooling geometry is qualified by the CAD space claim.

Reproduce: `make r3c-candidate` (parallel; `JOBS=n` limits workers).
