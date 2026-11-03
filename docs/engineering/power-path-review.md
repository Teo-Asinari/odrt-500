# R4 power-path review — 2026-11-03

**Decision: the R4 power path is functionally defined and sized, and every check passes after the owner's 56 V trip decision. Parts are not selected, and three primary sources could not be read.**

> **Update (2026-11-03): overvoltage trip lowered from 57 V to 56 V** (owner decision; `data/r4_power.yaml`). The full R4 suite was rerun: only the two aged-bank dump-failure cases change. They trip 58 ms earlier, peaking at 55.92 V instead of 56.96 V, which is 2.1 V below the clamp maximum. Every normal and other fault case is unchanged, and refinements still pass.

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
| Regen Clamp voltage | 55.92 V max (aged dump failure) vs 58 V rating; 56 V trip | pass, 2 V margin (was 1 V at 57 V) |
| Regen Clamp forward / brake | 9.6 A vs 20 A free air; 19.8 A average brake vs 40 A; 54.5 A switched vs 80 A / 3 s | pass; the meaning of the 40 A rating must be confirmed |
| Source fuse | ≥ 12 A DC | unselected |
| Bank fuse | ≥ 17.8 A, time-delay (peak 34.7 A); prospective fault 238 A fresh / 124 A aged (7× rating) | unselected; I²t check needed |
| Bank disconnect | back-to-back MOSFETs, 80 V class, about 0.8 W | unselected |
| Pre-charge / service discharge | one 6.8 Ω pulse resistor; supply held at 7.7 A of 9.6 A; 6.7 kJ per charge, 400 W peak | does not depend on the supply's unverified overload mode |
| Start-up time | 68 s to drive enable (fresh), 43 s (aged) | a UX cost; see below |
| Service discharge | 80 s to 5 V (fresh) through the same resistor; bleed alone takes 14 h (τ) | discharge is required, not optional |
| Balancing | passive 260 Ω per cell, 0.5 W; worst cell 2.69 V in use, 2.82 V at the 56 V trip (−10% capacitance cell) | pass; replaces the 1.05 guess; leakage assumed |
| Dump monitoring | 1 mΩ shunt; fault when measured < ½ of expected (duty × V / R) for 0.1 s, or bus > 54.5 V for 0.1 s | rule defined; not simulated |
| Bank duty limit | the existing 55–65 °C capacitor torque derate, fed by bank temperature sensing | already in the model; sensor added to the definition |

## Owner and engineering choices

1. **Trip voltage: decided, 56 V.** Normal operation peaks at 54.4 V, so 1.6 V of headroom remains. The fresh-bank dump failure peaks at 55.6 V and still does not trip, so the independent dump monitor remains necessary.
2. **Start-up time.** A resistor pre-charge at 80% of supply current takes about 68 s to drive enable with a fresh bank. If the EPP-500-54 is confirmed to current-limit cleanly into a capacitor (constant current, not hiccup), charging straight from the supply takes about 27 s. A dedicated constant-current pre-charge stage would do the same at the cost of parts.

## Not verified

- The EPP-500-54 overload mode: the datasheet text could not be extracted.
- Eaton TV cell leakage and the upper capacitance tolerance: the fetch timed out. A leakage spread of 0.1 mA is assumed.
- Whether the Regen Clamp's 40 A brake rating is an average or an instantaneous limit, and the chopper ripple.
- Fuse time-current curves, resistor pulse ratings, MOSFET SOA, bank wiring inductance, and switch weld detection.
- The dump-monitor rule and the pre-charge/discharge sequence are not simulated. The supervisor's latching and reset policy is still open.
