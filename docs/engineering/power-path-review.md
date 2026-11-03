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

## Simulated: dump monitor and pre-charge sequence (2026-11-03)

**Dump monitor** (`src/odrt/dump_monitor.py`, active in R4, parameters in `data/r4_power.yaml`). It compares shunt-measured current with commanded duty × bus V / R, plus a 55.0 V backup threshold. It needs 0.1 s of persistence and latches a `dump_fault` trip. Full R4 suite rerun:

| Case | Before | With monitor |
|---|---|---|
| Fresh dump failure (both variants) | no trip, bus 55.63 V | **dump_fault** 0.51 s after the fault, bus 55.14 V; uncoordinated bar 76° (one unit stops), coordinated 0.3° |
| Aged dump failure | overvoltage trip at 55.92 V | unchanged: the bus reaches 56 V 79 ms after the condition appears, before the 0.1 s detection |
| All normal and other fault cases | — | no false trips; changes are solver-level only (tracking 0.30 → 0.31%) |

The condition first appears at the first regeneration after the fault, when expected current rises with the bus while measured stays at zero. A first version also flagged any bus above 54.5 V (full duty). Normal cases pass within 0.1 V of that, which noise would turn into nuisance trips, and the current comparison already detects the fault at the same instant, so the backup was moved to 55.0 V.

**Pre-charge sequence** ([precharge.md](../../reports/precharge.md), `make precharge`). Separate electrical model with a quasi-static bus. Two corrections came out of it:

- The drive must be enabled only after the bypass closes. The first sizing enabled it at 45 V with the bypass still open.
- The bypass must close at about 1.9 V difference, not 5 V. At 5 V the top-off current (about 21 A) exceeds the supply's limit, which reintroduces the dependence on its overload mode.

| Sequence (fresh / aged) | Drive enabled | Supply | Resistor energy / rise |
|---|---|---|---|
| A: bank charged directly by the supply | 24 / 15 s | at its 9.6 A limit for 26 / 15 s; needs constant-current mode | — |
| B: 6.8 Ω pre-charge, bypass at 1.9 V | **120 / 62 s** | peaks at 7.4 A, never at its limit | 6.3 / 3.9 kJ, +34 / +22 K (assumed 150 J/K) |
| B, bypass welded closed | behaves like A | at its limit | — |
| B, bypass fails open | never; times out at 168 / 86 s | under its limit | — |
| B, mains lost at 30 s | never; bank left at 24 / 31 V | — | — |
| Service discharge from 53.7 V | 83 / 54 s to 5 V | — | 6.9 / 4.2 kJ, +37 / +24 K |

When mains is lost, the isolated drive bus falls below the 15 V auxiliary minimum in 0.4 s. The supervisor therefore cannot hold a discharge switch on, so **the discharge path must be normally closed** (fail-to-discharge) and opened only by an energised supervisor.

**Decision (owner, 2026-11-03): start-up is direct supply charging (sequence A).** The bank disconnect closes at power-on and the supply charges the bank in constant-current mode: the drive enables at 24 s fresh / 15 s aged. The pulse resistor stays only as the normally-closed service-discharge path, and the bypass switch and pre-charge function are removed (cost allowance reduced). New fault variants for A:

| Sequence A (fresh / aged) | Result |
|---|---|
| Normal | auxiliary rail up at 6.6 / 3.5 s; drive enabled at 24 / 15 s; supply at its limit for 26 / 15 s |
| Disconnect fails open | bank never charges; start-up timeout at 35 / 22 s, drive stays disabled |
| Mains lost at 10 s | drive never enabled; the bank feeds the auxiliary rail down to 15 / 22 V |

Two consequences follow:

- **The bank disconnect must close by default at power-on** (normally closed, or closed by a hardware circuit). The bus follows the bank up from 0 V, so the supervisor only powers up after several seconds.
- **The decision depends on the EPP-500-54 current-limiting continuously into the bank.** This is unverified; resistor pre-charge (sequence B, 120 s) is the recorded fallback.

**Start-up time trade (as analysed before the decision).** Sequence B takes 2 minutes with a fresh bank but does not depend on the supply's overload mode. Sequence A takes 24 s but needs constant-current behaviour. Normal R4 operation already runs the supply at its 9.6 A limit, though (heavy and hold cases), so confirming constant-current mode is required either way. Once it is confirmed, sequence A is the better choice, and the resistor is needed only for service discharge.

## Sizing summary

| Function | Result | Status |
|---|---|---|
| Regen Clamp voltage | 55.92 V max (aged dump failure) vs 58 V rating; 56 V trip | pass, 2 V margin (was 1 V at 57 V) |
| Regen Clamp forward / brake | 9.6 A vs 20 A free air; 19.8 A average brake vs 40 A; 54.5 A switched vs 80 A / 3 s | pass; the meaning of the 40 A rating must be confirmed |
| Source fuse | ≥ 12 A DC | unselected |
| Bank fuse | ≥ 17.8 A, time-delay (peak 34.7 A); prospective fault 238 A fresh / 124 A aged (7× rating) | unselected; I²t check needed |
| Bank disconnect | back-to-back MOSFETs, 80 V class, about 0.8 W | unselected |
| Service discharge (pre-charge fallback) | one 6.8 Ω pulse resistor, normally closed for discharge; as a fallback pre-charge it would hold the supply under 7.7 A | simulated; see above |
| Start-up | **direct supply charging (decided)**: drive enabled at 24 s fresh / 15 s aged; disconnect closed by default | depends on unverified supply constant-current mode |
| Service discharge | 80 s to 5 V (fresh) through the same resistor; bleed alone takes 14 h (τ) | discharge is required, not optional |
| Balancing | passive 260 Ω per cell, 0.5 W; worst cell 2.69 V in use, 2.82 V at the 56 V trip (−10% capacitance cell) | pass; replaces the 1.05 guess; leakage assumed |
| Dump monitoring | 1 mΩ shunt; fault when measured < ½ of expected (duty × V / R) for 0.1 s, or bus > 55.0 V for 0.1 s | simulated across the full R4 suite |
| Bank duty limit | the existing 55–65 °C capacitor torque derate, fed by bank temperature sensing | already in the model; sensor added to the definition |

## Owner and engineering choices

1. **Trip voltage: decided, 56 V.** Normal operation peaks at 54.4 V, so 1.6 V of headroom remains. The fresh-bank dump failure peaks at 55.6 V and still does not trip, so the independent dump monitor remains necessary.
2. **Start-up: decided, direct supply charging** (24 s fresh). Confirming the EPP-500-54's constant-current behaviour into a capacitive load is now the critical verification item. If it fails, fall back to the resistor sequence (120 s).

## Not verified

- The EPP-500-54 overload mode: the datasheet text could not be extracted.
- Eaton TV cell leakage and the upper capacitance tolerance: the fetch timed out. A leakage spread of 0.1 mA is assumed.
- Whether the Regen Clamp's 40 A brake rating is an average or an instantaneous limit, and the chopper ripple.
- Fuse time-current curves, resistor pulse ratings, MOSFET SOA, bank wiring inductance, and switch weld detection.
- The monitor is ideal apart from its timing: shunt noise, offset and ADC filtering are not modelled. The supervisor's reset policy after a `dump_fault` is still open.
- The sequence model neglects the drive-bus capacitance and switching transients, and assumes the resistor's thermal capacity.
