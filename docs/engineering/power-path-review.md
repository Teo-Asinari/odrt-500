# R4 power-path review — 2026-11-03

**Decision: the R4 power path is functionally defined and sized. Parts are not selected, and three primary sources could not be read. One check fails: the Regen Clamp's 58 V rating leaves 1 V above the 57 V trip. Owner/engineering choice: lower the trip, or replace the clamp's diode and chopper with 80 V-class parts.**

Evidence: [power-path sizing](../../reports/power_path.md) (`make power-path`), built on the [R4 simulated envelope](../../reports/r4_candidate.md). [Electrical definition](../../reports/electrical_definition.md) and [cost allowances](../../reports/preliminary_costs.md) are updated to the R4 power path.

## Topology

```
mains → EPP-500-54 (52 V) → source fuse → Regen Clamp ideal diode ─┬─ drive bus (3 mF + clamp 0.8 mF) → ODrive Pro
                                                                     ├─ Regen Clamp chopper → 1 Ω dump (+ current shunt)
                                                                     └─ bank fuse → disconnect ─┬─ 20 × 100 F TV bank (balancing, monitor, temperature)
                                                                                   pre-charge/discharge resistor (switched)
```

R4 keeps the Regen Clamp from R2/R3 and moves the bank from its input side to its output side. The clamp's ideal diode now blocks back-feed into the supply, and its chopper is still the dump. This reuses a cited part instead of adding an unnamed controller.

## Sizing summary

| Function | Result | Status |
|---|---|---|
| Regen Clamp voltage | 56.96 V max (aged dump failure) vs 58 V rating | pass, but only 1.0 V above the 57 V trip; **fails** the 80 V device-class rule |
| Regen Clamp forward / brake | 9.6 A vs 20 A free air; 19.8 A average brake vs 40 A; 54.5 A switched vs 80 A / 3 s | pass; the meaning of the 40 A rating must be confirmed |
| Source fuse | ≥ 12 A DC | unselected |
| Bank fuse | ≥ 17.8 A, time-delay (peak 34.7 A); prospective fault 238 A fresh / 124 A aged (7× rating) | unselected; I²t check needed |
| Bank disconnect | back-to-back MOSFETs, 80 V class, about 0.8 W | unselected |
| Pre-charge / service discharge | one 6.8 Ω pulse resistor; supply held at 7.7 A of 9.6 A; 6.7 kJ per charge, 400 W peak | does not depend on the supply's unverified overload mode |
| Start-up time | 68 s to drive enable (fresh), 43 s (aged) | a UX cost; see below |
| Service discharge | 80 s to 5 V (fresh) through the same resistor; bleed alone takes 14 h (τ) | discharge is required, not optional |
| Balancing | passive 260 Ω per cell, 0.5 W; worst cell 2.69 V in use, 2.88 V at the trip (−10% capacitance cell) | pass; replaces the 1.05 guess; leakage assumed |
| Dump monitoring | 1 mΩ shunt; fault when measured < ½ of expected (duty × V / R) for 0.1 s, or bus > 54.5 V for 0.1 s | rule defined; not simulated |
| Bank duty limit | the existing 55–65 °C capacitor torque derate, fed by bank temperature sensing | already in the model; sensor added to the definition |

## Choices for the owner or engineering

1. **The 57 V trip against the clamp's 58 V rating.** Normal operation peaks at 54.4 V (the dump level). A 56 V trip leaves 1.6 V of headroom over normal use and 2 V below the rating. The alternative is a discrete 80 V-class ideal diode and chopper. The trip change needs a rerun of the dump-failure and release cases.
2. **Start-up time.** A resistor pre-charge at 80% of supply current takes about 68 s to drive enable with a fresh bank. If the EPP-500-54 is confirmed to current-limit cleanly into a capacitor (constant current, not hiccup), charging straight from the supply takes about 27 s. A dedicated constant-current pre-charge stage would do the same at the cost of parts.

## Not verified

- The EPP-500-54 overload mode: the datasheet text could not be extracted.
- Eaton TV cell leakage and the upper capacitance tolerance: the fetch timed out. A leakage spread of 0.1 mA is assumed.
- Whether the Regen Clamp's 40 A brake rating is an average or an instantaneous limit, and the chopper ripple.
- Fuse time-current curves, resistor pulse ratings, MOSFET SOA, bank wiring inductance, and switch weld detection.
- The dump-monitor rule and the pre-charge/discharge sequence are not simulated. The supervisor's latching and reset policy is still open.
