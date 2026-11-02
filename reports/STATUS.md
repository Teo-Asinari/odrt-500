# Status

Last updated: 2026-11-02 (iteration 2). Hand-written by the coding agent; everything else in `reports/` is generated. `make ci` regenerates and checks all of it.

## Where the project stands

Simulation-only concept, now in **iteration 2**, driven by the owner's decisions in `docs/architecture-decisions/ADR-001-iteration-2-targets.md`: 500 lbf from one unit, held for seconds per rep, a floor platform, and a supercapacitor buffer. Every model still runs on placeholder parameters (A-001 to A-021), and Gate D (independent review) still applies before any hardware.

**Lead design:** one CubeMars RO100 motor driving a drum through a 6:1 belt, a 1 kW supply plus a 2 F supercapacitor buffer, built into a 935 × 660 × 200 mm floor platform. The cable runs to a turning sheave and up through the deck between the feet.

## Iteration 2 results

| Metric | Iteration 1 (2 motors) | Iteration 2 (1 motor) |
|---|---:|---:|
| Felt inertia at the handle | 86 kg | 43 kg |
| 8 lbf tension tracking error | ~290% (slack and snap) | 12% |
| 500 lbf tracking error | 4.5% | 1.6% (with buffer) |
| Static stall tension (runaway cap, H-06) | 1,139 lbf | 570 lbf |
| Release snap peak, speed limiter on | 1,261 lbf | 932 lbf |
| Known cost (cited lines only) | $910 | $589 |

## Since the last status (same day)

- **Fault policy (H-02, H-06, H-07, H-14).** A release is now told apart from a stuck load cell by the drum's inward acceleration. A sensor fault holds the load and ramps it down; hand lurch falls from 1.17 to 0.42 m. An independent channel (proposal) has a 50 ms watchdog and a wrong-sign check. Either trips STO with resistive phase braking, and the same braking is used on power loss (lurch 1.16 to 0.50 m). Presence sensing keeps an empty platform down. No false trips in normal use.
- **Sheave and load path.** The sheave hangs from a cross-beam between the foot stringers: 15 mm axle, bearings rated ≥ 5.9 kN static each, all checks pass. The sheave-to-rope diameter ratio of 15 is flagged for rope-fatigue review.
- **Thermal recalibration from cited data.** The winding limit is 140 °C (Class F minus margin), and the winding node is calibrated to a documented 105 mm frameless motor (Tecnotion). Heavy-tempo sets pass (127 °C). 3 s pauses at 500 lbf (151 °C) and slow 400 lbf sets (177 °C) do not. 500 lbf lasts about 26 s from cold.
- **Cost.** $600 known in USD from 7 of 19 lines; the load cell (CAD), belt wheel (GBP) and rope (currency unverified) are listed but not summed.

## Open problems, in priority order

1. **The RO100's true motor constant decides whether the single-motor design works (A-022).** Its derived Km (0.53) is 1.55× a documented motor of similar size (0.34). At the analogue's Km, even normal heavy sets reach about 227 °C. **Measuring the RO100's Kt and phase resistance is the most decisive next test.** It is a motor-only bench measurement with no human loading. If the Km is low, the fallback is two motors or a higher ratio with a higher bus voltage.
2. **Heat for long tension:** slow heavy sets and pauses at 500 lbf exceed the limit even at the cited Km. Firmware thermal derating (H-08) limits time under heavy tension.
3. **Speed ceiling:** about 1.1 m/s cable speed at 48 V.
4. **Rope:** the models assume 4 mm. The only priced rope is 6 mm (40 kN), and the requirement is ≥ 12.7 kN. Choose a rope, then size the drum, sheave and D/d ratio.
5. **Safety items still open:** a mechanical handle arrestor (H-01), safety MCU and STO hardware design, presence-sensor thresholds, and encoder loss combined with a release.
6. **Cost:** 12 lines unpriced, including the supercapacitor buffer (no listing near 2 F at 60 V was found).

## Tests

136 tests pass. `make ci` runs check, test, report, CAD (mechanism and platform, with interference checks), FEA and the visual exports.

## Next smallest verifiable milestones

1. Decide how to settle the RO100 Km question: a bench measurement, a vendor datasheet request, or a switch to a fully documented motor.
2. Rope selection, then drum, sheave and D/d resize.
3. Handle arrestor concept and its load case.
4. Price the remaining BOM lines (buffer, bearings, belts, structure).
