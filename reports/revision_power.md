# Higher-voltage upstream-buffer power experiment

Fingerprint: `281ff7164391fa7f21516266986af571de0a85fdc81133f9ead20b316fb68ef4`

**REVISE: this is a topology experiment, not a selected complete machine.** The bank is upstream of a reverse-blocking Regen Clamp and cannot receive regenerated motor energy. A separate input-link state, one-way forward drop, clamp loss and relative-input averaged dump replace the bidirectional bank/DC-link path. Source, capacitor and dump thermal powers and stored energy are updated in the same plant.

Candidates: [ODrive Pro](https://docs.odriverobotics.com/v/latest/hardware/pro-datasheet.html), [EPP-500-54](https://www.meanwell.com/Upload/PDF/EPP-500/EPP-500-SPEC.PDF) adjusted within its documented range to 52 V, and [Regen Clamp](https://docs.odriverobotics.com/v/latest/hardware/regen-clamp-datasheet.html). Accessed 2026-11-02; availability/prices unverified. The original EPP-500-48 cannot provide 52 V within its 45.6–50.4 V documented range.

| Bank / case | Tracking % | Bus min–max V (averaged) | Trip | Brake RMS A | Dump J | Energy residual | Failed checks |
|---|---:|---:|---|---:|---:|---:|---|
| compact_nominal / single_heavy_full | 0.16 | 48.22–53.17 | none | 9.26 | 2204.7 | 1.28e-07 | none in listed screens |
| compact_nominal / single_fast_full | 34.03 | 42.67–53.41 | none | 19.85 | 7169.9 | 9.68e-08 | proposed normal overshoot, proposed tracking RMS, recommended electrical frequency |
| compact_nominal / single_endurance_full | 30.77 | 46.60–53.08 | none | 6.09 | 31703.1 | 5.71e-07 | proposed normal overshoot, proposed tracking RMS |
| compact_nominal / paired_heavy_full | 0.74 | 47.39–53.21 | none | 9.29 | 2219.3 | 1.46e-07 | none in listed screens |
| compact_nominal / left_power_loss_buffered_coordinated | 0.62 | 43.02–53.21 | none | 8.67 | 451.3 | 1.78e-08 | none in listed screens |
| compact_nominal / paired_dump_failure_coordinated | 0.09 | 51.44–56.95 | overvoltage | 0.00 | 0.0 | 2.13e-09 | none in listed screens |
| compact_aged / single_heavy_full | 0.16 | 44.89–53.18 | none | 9.26 | 2204.9 | 1.76e-07 | none in listed screens |
| compact_aged / single_fast_full | 86.61 | 40.13–53.41 | undervoltage | 7.63 | 1060.6 | 2.28e-07 | latched protective trip during normal operation, proposed normal overshoot, proposed tracking RMS, recommended electrical frequency |
| compact_aged / single_endurance_full | 30.80 | 40.33–53.09 | none | 6.09 | 31699.2 | 4.99e-07 | proposed normal overshoot, proposed tracking RMS |
| compact_aged / paired_heavy_full | 0.74 | 42.78–53.22 | none | 9.29 | 2219.4 | 1.19e-07 | none in listed screens |
| compact_aged / left_power_loss_buffered_coordinated | 0.62 | 40.03–53.22 | undervoltage | 8.67 | 451.3 | 3.92e-08 | none in listed screens |
| compact_aged / paired_dump_failure_coordinated | 0.09 | 51.30–56.95 | overvoltage | 0.00 | 0.0 | 7.99e-09 | none in listed screens |

## Limits

- Upstream storage cannot recover motor regeneration; reverse flow is blocked and energy is dumped.
- The clamp is cycle-averaged across hysteresis endpoints. Switching ripple/delay/15kHz limit and peaks are not resolved.
- Clamp conduction heat is added to the existing drive thermal node; separate board hotspot/OTP is unvalidated.
- Extra clamp board and input capacitance are not fitted into the CAD; R1 failed supports are unchanged.
- Pro voltage utilization/frequency screens and thermal paths remain stated model assumptions; phase conventions need calibration.

Capacitance placement and diode drop are explicit proposals in `data/revision_components.yaml`. Averaged voltages and current screens cannot establish switching-peak compliance. No physical braking/resistor/thermal qualification follows from this experiment. Selected convergence and the complete suite are still required before adoption.

Reproduce: `.venv/bin/python -m odrt.revision_power`.
