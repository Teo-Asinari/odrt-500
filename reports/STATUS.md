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

## Open problems, in priority order

1. **Heat is the binding limit, and its data is a placeholder.** With one motor, 500 lbf costs about 520 W of copper loss. Heavy-tempo sets peak at 106 °C, but 3 s pauses at 500 lbf reach 128 °C and slow 400 lbf sets 157 °C, against a 120 °C limit. A fan doesn't help over seconds-long peaks. **Winding thermal data (resistance, time constants, insulation class) is the most valuable unknown.** Mitigation: firmware thermal derating with a winding thermistor (H-08).
2. **Speed ceiling.** At 48 V the motor tops out around 2,000–2,500 rpm, which caps the cable at about 1.1 m/s. Heavy reps are fine; fast light reps (up to 1.3 m/s) are not.
3. **Cost.** $589 known from 4 of 19 lines. The supply ($268) is the biggest single line, and the buffer did not let it shrink (mean draw is about 480 W).
4. **Safety items still open:** a mechanical handle arrestor (H-01), a fault policy that separates a stuck load cell from a release (H-02), deck presence sensing (H-14, an empty platform lifts at 41 lbf), and simulating frozen or inverted torque (H-06) and encoder loss (H-07).
5. **Platform details:** sheave and axle sizing (5.9 kN snap load), real fleet-angle limit, frame joints and FEA, and tipping under off-vertical pulls.

## Tests

129 tests pass. `make ci` runs check, test, report, CAD (mechanism and platform, with interference checks), FEA and the visual exports.

## Next smallest verifiable milestones

1. Fault policy and simulation of H-06, H-07 and H-14, with independent channels identified.
2. Sheave, axle and fleet-angle design, plus a snap-load case through the platform frame.
3. Search for cited RO100 thermal data, or a better-documented motor of similar Km.
4. Price the remaining BOM lines.
