# Compact buffer experiment

Fingerprint: `0cbe354bf4df8c5897cb48abaf3e390f7e1f913eb5f1a5c8203fff3eeea70a50`

This experiment retains the coupled reference mechanics, source, control and thermal network. It changes the capacitor cell only. No complete enclosure fit or protection circuit is established.

Manufacturer facts: [Eaton HV datasheet](https://www.eaton.com/content/dam/eaton/products/electronic-components/resources/data-sheet/eaton-hv-supercapacitors-cylindrical-cells-data-sheet.pdf), accessed 2026-11-02. Thermal capacity is an assumption: 20 J/K per cell, bracketed at 10 and 40 J/K. The aging corner combines minimum initial capacitance with a further 30% loss and doubled ESR. It is not a life prediction. Open-air current ratings do not qualify an enclosed pack.

| Variant | Bank F | ESR Ω | Cells kg | Cell bodies L |
|---|---:|---:|---:|---:|
| reference | 15.909 | 0.0704 | 1.32 | 1.178 |
| compact_nominal | 4.545 | 0.2640 | 0.44 | 0.358 |
| compact_initial_min | 4.091 | 0.2640 | 0.44 | 0.358 |
| compact_aged | 2.864 | 0.5280 | 0.44 | 0.358 |
| compact_aged_low_heat_capacity | 2.864 | 0.5280 | 0.44 | 0.358 |
| compact_aged_high_heat_capacity | 2.864 | 0.5280 | 0.44 | 0.358 |

Cell-body volume excludes leads, balance/protection boards, insulation, clearances and harness.

| Variant / case | Bus min–max V | Winding °C | Cell °C | Cell RMS A | Tracking % | Failed checks |
|---|---:|---:|---:|---:|---:|---|
| reference / single_heavy_full | 46.26–49.03 | 78.5 | 25.1 | 6.51 | 0.14 | none in evaluated comparisons |
| reference / single_fast_full | 46.12–49.05 | 51.3 | 25.2 | 12.78 | 40.25 | proposed normal overshoot, proposed tracking RMS, recommended electrical frequency, virtual motor voltage controllability, virtual travel stop engagement |
| reference / single_endurance_full | 45.97–49.01 | 129.7 | 28.5 | 3.81 | 28.51 | proposed normal overshoot, proposed tracking RMS |
| reference / paired_heavy_full | 46.26–49.03 | 78.3 | 25.1 | 6.54 | 0.23 | none in evaluated comparisons |
| reference / left_power_loss_buffered | 46.02–49.03 | 40.9 | 25.0 | 8.54 | 0.51 | none in evaluated comparisons |
| reference / left_power_loss_buffered_coordinated | 46.02–49.03 | 40.9 | 25.0 | 8.54 | 0.51 | none in evaluated comparisons |
| reference / paired_dump_failure | 46.82–49.41 | 40.9 | 25.0 | 6.88 | 0.17 | none in evaluated comparisons |
| reference / paired_dump_failure_coordinated | 46.82–49.41 | 40.9 | 25.0 | 6.88 | 0.17 | none in evaluated comparisons |
| compact_nominal / single_heavy_full | 44.35–49.07 | 78.5 | 25.3 | 3.91 | 0.14 | none in evaluated comparisons |
| compact_nominal / single_fast_full | 41.38–49.10 | 51.2 | 25.7 | 8.00 | 40.24 | proposed normal overshoot, proposed tracking RMS, recommended electrical frequency, virtual motor voltage controllability, virtual travel stop engagement |
| compact_nominal / single_endurance_full | 42.63–49.05 | 129.7 | 31.0 | 2.64 | 28.71 | proposed normal overshoot, proposed tracking RMS |
| compact_nominal / paired_heavy_full | 44.38–49.07 | 78.3 | 25.3 | 3.95 | 0.23 | none in evaluated comparisons |
| compact_nominal / left_power_loss_buffered | 40.00–49.07 | 37.5 | 25.1 | 6.21 | 0.51 | none in evaluated comparisons |
| compact_nominal / left_power_loss_buffered_coordinated | 40.01–49.07 | 35.8 | 25.1 | 6.21 | 0.51 | none in evaluated comparisons |
| compact_nominal / paired_dump_failure | 43.42–49.95 | 40.8 | 25.0 | 0.69 | 0.17 | none in evaluated comparisons |
| compact_nominal / paired_dump_failure_coordinated | 47.38–49.95 | 29.9 | 25.0 | 0.69 | 0.17 | none in evaluated comparisons |
| compact_initial_min / single_heavy_full | 44.22–49.07 | 78.5 | 25.3 | 3.93 | 0.14 | none in evaluated comparisons |
| compact_initial_min / single_fast_full | 41.32–49.10 | 51.2 | 25.7 | 8.04 | 40.24 | proposed normal overshoot, proposed tracking RMS, recommended electrical frequency, virtual motor voltage controllability, virtual travel stop engagement |
| compact_initial_min / single_endurance_full | 42.46–49.05 | 129.7 | 31.0 | 2.64 | 28.71 | proposed normal overshoot, proposed tracking RMS |
| compact_initial_min / paired_heavy_full | 44.23–49.07 | 78.3 | 25.3 | 3.97 | 0.23 | none in evaluated comparisons |
| compact_initial_min / left_power_loss_buffered | 40.01–49.07 | 36.9 | 25.1 | 5.42 | 0.51 | none in evaluated comparisons |
| compact_initial_min / left_power_loss_buffered_coordinated | 40.01–49.07 | 35.3 | 25.1 | 5.42 | 0.51 | none in evaluated comparisons |
| compact_initial_min / paired_dump_failure | 43.32–49.95 | 40.8 | 25.0 | 0.69 | 0.17 | none in evaluated comparisons |
| compact_initial_min / paired_dump_failure_coordinated | 47.38–49.95 | 29.9 | 25.0 | 0.69 | 0.17 | none in evaluated comparisons |
| compact_aged / single_heavy_full | 40.37–49.07 | 78.5 | 25.5 | 3.86 | 0.14 | none in evaluated comparisons |
| compact_aged / single_fast_full | 41.60–49.11 | 26.5 | 25.0 | 0.39 | 94.58 | latched protective trip during normal operation, proposed normal overshoot, proposed tracking RMS, recommended electrical frequency |
| compact_aged / single_endurance_full | 40.01–49.06 | 35.3 | 25.3 | 0.25 | 99.41 | latched protective trip during normal operation, proposed tracking RMS |
| compact_aged / paired_heavy_full | 40.56–49.08 | 78.3 | 25.5 | 3.89 | 0.23 | none in evaluated comparisons |
| compact_aged / left_power_loss_buffered | 40.03–49.08 | 33.9 | 25.1 | 2.92 | 0.51 | none in evaluated comparisons |
| compact_aged / left_power_loss_buffered_coordinated | 40.03–49.08 | 33.6 | 25.1 | 2.92 | 0.51 | none in evaluated comparisons |
| compact_aged / paired_dump_failure | 40.43–49.85 | 30.3 | 25.0 | 0.31 | 0.17 | none in evaluated comparisons |
| compact_aged / paired_dump_failure_coordinated | 47.22–49.85 | 29.8 | 25.0 | 0.31 | 0.17 | none in evaluated comparisons |
| compact_aged_low_heat_capacity / single_heavy_full | 40.37–49.07 | 78.5 | 25.9 | 3.86 | 0.14 | none in evaluated comparisons |
| compact_aged_low_heat_capacity / single_fast_full | 41.60–49.11 | 26.5 | 25.0 | 0.39 | 94.58 | latched protective trip during normal operation, proposed normal overshoot, proposed tracking RMS, recommended electrical frequency |
| compact_aged_low_heat_capacity / single_endurance_full | 40.01–49.06 | 35.3 | 25.3 | 0.25 | 99.41 | latched protective trip during normal operation, proposed tracking RMS |
| compact_aged_low_heat_capacity / paired_heavy_full | 40.56–49.08 | 78.3 | 25.9 | 3.89 | 0.23 | none in evaluated comparisons |
| compact_aged_low_heat_capacity / left_power_loss_buffered | 40.03–49.08 | 33.9 | 25.1 | 2.92 | 0.51 | none in evaluated comparisons |
| compact_aged_low_heat_capacity / left_power_loss_buffered_coordinated | 40.03–49.08 | 33.6 | 25.1 | 2.92 | 0.51 | none in evaluated comparisons |
| compact_aged_low_heat_capacity / paired_dump_failure | 40.43–49.85 | 30.3 | 25.0 | 0.31 | 0.17 | none in evaluated comparisons |
| compact_aged_low_heat_capacity / paired_dump_failure_coordinated | 47.22–49.85 | 29.8 | 25.0 | 0.31 | 0.17 | none in evaluated comparisons |
| compact_aged_high_heat_capacity / single_heavy_full | 40.37–49.07 | 78.5 | 25.2 | 3.86 | 0.14 | none in evaluated comparisons |
| compact_aged_high_heat_capacity / single_fast_full | 41.60–49.11 | 26.5 | 25.0 | 0.39 | 94.58 | latched protective trip during normal operation, proposed normal overshoot, proposed tracking RMS, recommended electrical frequency |
| compact_aged_high_heat_capacity / single_endurance_full | 40.01–49.06 | 35.3 | 25.2 | 0.25 | 99.41 | latched protective trip during normal operation, proposed tracking RMS |
| compact_aged_high_heat_capacity / paired_heavy_full | 40.56–49.08 | 78.3 | 25.3 | 3.89 | 0.23 | none in evaluated comparisons |
| compact_aged_high_heat_capacity / left_power_loss_buffered | 40.03–49.08 | 33.9 | 25.0 | 2.92 | 0.51 | none in evaluated comparisons |
| compact_aged_high_heat_capacity / left_power_loss_buffered_coordinated | 40.03–49.08 | 33.6 | 25.0 | 2.92 | 0.51 | none in evaluated comparisons |
| compact_aged_high_heat_capacity / paired_dump_failure | 40.43–49.85 | 30.3 | 25.0 | 0.31 | 0.17 | none in evaluated comparisons |
| compact_aged_high_heat_capacity / paired_dump_failure_coordinated | 47.22–49.85 | 29.8 | 25.0 | 0.31 | 0.17 | none in evaluated comparisons |

All cases retain software fault injection and the limitations in `reports/coupled.md`. Current peaks are recorded, but the datasheet’s one-second pulse definition is not an arbitrary instantaneous current limit. Per-cell imbalance, leakage, balancing and wiring parasitics are not modeled. The open-air RMS comparison scales by inverse square root of ESR growth to preserve the initial rated resistive heat; this is an analytical screen, not a vendor aged-cell rating.

The experiment caps solver work at 2000 internal steps per output interval, without changing the reference time-step cap or tolerances. Failure is retained explicitly. Voltage and thermal zero crossings now latch the affected unit off. Recovery does not rearm it; configured peer stops follow the recorded trip time plus the assumed peer delay. Hardware detection and phase-transfer latency remain unvalidated. The earlier non-latching experiment is historical.

## Selected resolution verification

| Study | Max medium–fine change | Trip-time change s | Outcome |
|---|---:|---:|---|
| compact_nominal__left_power_loss_buffered_coordinated | 0.000% | 2.15e-06 | pass |
| compact_nominal__paired_dump_failure_coordinated | 0.002% | 3.61e-09 | pass |
| compact_aged__single_fast_full | 0.000% | 2.33e-08 | pass |
| compact_aged__single_heavy_full | 0.000% | — | pass |

Refinement uses maximum steps 2/1/0.5 ms and relative tolerances 1e-6/2.5e-7/6.25e-8; the original relative normal/fault criteria apply. Trip modes must agree and medium-to-fine trip time must change by at most 0.1 ms. This covers four selected cases only.

Solver backends and any event-interpolation fallback are recorded per case in the JSON. SciPy BDF uses the same equations and error tolerances when CVODES returns CV_ILL_INPUT; an independent analytic decay/event/quadrature test covers the fallback path.

## Protective trip records

| Variant / case | Unit | Reason | Time s |
|---|---:|---|---:|
| compact_nominal / left_power_loss_buffered | 0 | undervoltage | 4.169827 |
| compact_nominal / left_power_loss_buffered | 1 | undervoltage | 4.710314 |
| compact_nominal / left_power_loss_buffered_coordinated | 0 | undervoltage | 4.169825 |
| compact_nominal / paired_dump_failure | 0 | overvoltage | 1.487820 |
| compact_nominal / paired_dump_failure_coordinated | 0 | overvoltage | 1.487820 |
| compact_initial_min / left_power_loss_buffered | 0 | undervoltage | 4.007057 |
| compact_initial_min / left_power_loss_buffered | 1 | undervoltage | 4.546541 |
| compact_initial_min / left_power_loss_buffered_coordinated | 0 | undervoltage | 4.007037 |
| compact_initial_min / paired_dump_failure | 0 | overvoltage | 1.487658 |
| compact_initial_min / paired_dump_failure_coordinated | 0 | overvoltage | 1.487658 |
| compact_aged / single_fast_full | 0 | undervoltage | 1.692919 |
| compact_aged / single_endurance_full | 0 | undervoltage | 4.207679 |
| compact_aged / left_power_loss_buffered | 0 | undervoltage | 3.513238 |
| compact_aged / left_power_loss_buffered | 1 | undervoltage | 3.643312 |
| compact_aged / left_power_loss_buffered_coordinated | 0 | undervoltage | 3.513247 |
| compact_aged / paired_dump_failure | 0 | overvoltage | 1.429769 |
| compact_aged / paired_dump_failure | 1 | undervoltage | 2.359829 |
| compact_aged / paired_dump_failure_coordinated | 0 | overvoltage | 1.429769 |
| compact_aged_low_heat_capacity / single_fast_full | 0 | undervoltage | 1.692919 |
| compact_aged_low_heat_capacity / single_endurance_full | 0 | undervoltage | 4.207680 |
| compact_aged_low_heat_capacity / left_power_loss_buffered | 0 | undervoltage | 3.513236 |
| compact_aged_low_heat_capacity / left_power_loss_buffered | 1 | undervoltage | 3.643311 |
| compact_aged_low_heat_capacity / left_power_loss_buffered_coordinated | 0 | undervoltage | 3.513227 |
| compact_aged_low_heat_capacity / paired_dump_failure | 0 | overvoltage | 1.429769 |
| compact_aged_low_heat_capacity / paired_dump_failure | 1 | undervoltage | 2.359829 |
| compact_aged_low_heat_capacity / paired_dump_failure_coordinated | 0 | overvoltage | 1.429769 |
| compact_aged_high_heat_capacity / single_fast_full | 0 | undervoltage | 1.692919 |
| compact_aged_high_heat_capacity / single_endurance_full | 0 | undervoltage | 4.207676 |
| compact_aged_high_heat_capacity / left_power_loss_buffered | 0 | undervoltage | 3.513249 |
| compact_aged_high_heat_capacity / left_power_loss_buffered | 1 | undervoltage | 3.643321 |
| compact_aged_high_heat_capacity / left_power_loss_buffered_coordinated | 0 | undervoltage | 3.513249 |
| compact_aged_high_heat_capacity / paired_dump_failure | 0 | overvoltage | 1.429769 |
| compact_aged_high_heat_capacity / paired_dump_failure | 1 | undervoltage | 2.359829 |
| compact_aged_high_heat_capacity / paired_dump_failure_coordinated | 0 | overvoltage | 1.429770 |

Reproduce: `.venv/bin/python -m odrt.buffer_study`.
