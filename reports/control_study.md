# Controller study (R3 machine)

Fingerprint: `6d75797ae0b022abb88fb4365dc2290d9d1114be64b558c065ca3c6d5dc8694d`

**Study only. The reference controller is unchanged.** Fast reversal is not current- or voltage-limited in R3; its error is control dynamics (about 13 kg of reflected inertia at the rope, weak force feedback, feedforward on the scenario's planned rather than measured acceleration). This sweep tests how far gains alone go before model changes.

| Variant | Changes | paired_release_asymmetric | single_fast_full | single_stroke_full | single_heavy_full | single_low_full | paired_release | left_torque_inverted | paired_asymmetric |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| reference | reference | 0.44% | 29.01% ✗ | 35.75% ✗ | 0.12% | 2.73% | 0.44% | 0.44% ✗ | 0.79% ✗ |
| kp_0.5 | kp=0.5 | 0.28% | 22.96% ✗ | 33.89% ✗ | 0.09% | 2.23% | 0.28% | 0.28% ✗ | 0.11% |
| kp_1 | kp=1.0 | 0.24% | 17.52% ✗ | 31.43% ✗ | 0.08% | 1.73% | 0.24% | 0.24% ✗ | 0.09% |
| kp_2 | kp=2.0 | 0.26% | 13.49% ✗ | 27.72% ✗ | 0.09% | 1.19% | 0.26% | 0.26% ✗ | 0.09% |
| kp_4 | kp=4.0 | 0.30% | 11.34% ✗ | 22.04% ✗ | 0.10% | 0.74% | 0.30% | 0.31% ✗ | 0.10% |
| ff_1.0 | inertia_feedforward=1.0 | 0.40% | 27.71% ✗ | 35.83% ✗ | 0.10% | 0.24% | 0.40% | 0.40% ✗ | 0.82% ✗ |
| kp_1_ff_1.0 | kp=1.0, inertia_feedforward=1.0 | 0.23% | 16.62% ✗ | 31.34% ✗ | 0.07% | 0.14% | 0.23% | 0.23% ✗ | 0.07% |
| kp_2_ki_20 | kp=2.0, ki_s=20 | 0.37% | 19.83% ✗ | 20.86% ✗ | 0.11% | 0.77% | 0.37% | 0.37% ✗ | 0.12% |
| kp_2_fast_filter | kp=2.0, force_filter_s=0.0005 | 0.07% | 13.43% ✗ | 26.27% ✗ | 0.03% | 1.19% | 0.07% | 0.07% ✗ | 0.03% |
| measured_accel | acceleration_blend=1.0 | 0.27% | 17.34% ✗ | 41.29% ✗ | 0.10% | 2.30% | 0.27% | 0.27% ✗ | 0.10% |
| kp_2_measured_accel | kp=2.0, acceleration_blend=1.0 | 0.23% | 11.48% ✗ | 33.53% ✗ | 0.08% | 1.13% | 0.23% | 0.23% ✗ | 0.08% |
| kp_4_measured_accel | kp=4.0, acceleration_blend=1.0 | 0.27% | 10.56% ✗ | 29.14% ✗ | 0.10% | 0.72% | 0.28% | 0.43% ✗ | 1.03% ✗ |
| kp_2_measured_ff1 | kp=2.0, acceleration_blend=1.0, inertia_feedforward=1.0 | 0.22% | 11.00% ✗ | 34.30% ✗ | 0.08% | 0.18% | 0.22% | 0.22% ✗ | 0.08% |
| end_zone_0.1_300 | end_zone_m=0.1, end_zone_gain_n_s_m=300 | 0.44% | 29.01% ✗ | 34.69% ✗ | 0.12% | 2.73% | 0.44% | 0.44% ✗ | 0.79% ✗ |
| end_zone_0.15_600 | end_zone_m=0.15, end_zone_gain_n_s_m=600 | 0.44% | 29.01% ✗ | 33.80% ✗ | 0.12% | 2.73% | 0.44% | 0.44% ✗ | 0.94% ✗ |
| kp_4_measured_end_zone | kp=4.0, acceleration_blend=1.0, end_zone_m=0.15, end_zone_gain_n_s_m=600 | 0.27% | 10.56% ✗ | 21.53% ✗ | 0.10% | 0.72% | 0.28% | 0.27% ✗ | 1.03% ✗ |
| kp_4_retract_2.0 | kp=4.0, retract_speed_limit_m_s=2.0 | 0.30% | 11.36% ✗ | 16.56% ✗ | 0.10% | 0.74% | 0.30% | 0.31% ✗ | 0.10% |
| kp_4_retract_2.5 | kp=4.0, retract_speed_limit_m_s=2.5 | 0.30% | 11.36% ✗ | 16.56% ✗ | 0.10% | 0.74% | 0.30% | 0.31% ✗ | 0.10% |
| kp_4_measured_retract_2.5 | kp=4.0, acceleration_blend=1.0, retract_speed_limit_m_s=2.5 | 0.27% | 10.53% ✗ | 21.86% ✗ | 0.10% | 0.72% | 0.28% | 0.43% ✗ | 1.03% ✗ |
| kp_4_retract_2.5_end_zone | kp=4.0, retract_speed_limit_m_s=2.5, end_zone_m=0.15, end_zone_gain_n_s_m=600 | 0.30% | 11.36% ✗ | 14.14% ✗ | 0.10% | 0.74% | 0.30% | 0.30% ✗ | 0.10% |

Cells: settled tracking RMS fraction (trip reason); ✗ marks any failed comparison. Failed comparisons per cell are in `control_study.json`.

- Sensor noise and quantization are not modelled; higher gains will look better here than on hardware.
- Stability margins are judged only by these time-domain cases; no loop-shaping or robustness analysis yet.
- Measured acceleration is the derivative of the filtered encoder speed; after an encoder fault it is driven by the zeroed encoder reading. End-zone braking is added to the command, so tracking is judged against the braked command.
- Release, inverted-torque and asymmetric cases are included to catch gains that destabilize fault response.

Reproduce: `make control-study`.
