# Status

Last updated: 2026-11-02. Hand-written by the coding agent; everything else in `reports/` is generated. `make ci` regenerates and checks all of it.

## Where the project stands

Every work package in the brief now has a first, simulation-only pass. **The current design is a concept, not a validated design.** Every model uses placeholder parameters, which are listed in the assumptions register (A-001 to A-019). Gate D (independent engineering review) still applies before any hardware.

| Step | Report | State |
|---|---|---|
| WP0 bootstrap and traceability | `traceability.md` | Done |
| WP1 duty cycles | `duty_cycles.md` | Done; R-01 scoped to heavy-lift tempos (A-007, cited) |
| WP2 drivetrain baseline | `drivetrain_baseline.md` | Done (illustrative architectures) |
| WP3 real components | `components.md` | Done for 5 cited candidates; lead design: **two CubeMars RO100 motors driving one drum through a 6:1 belt** |
| R-07 thermal | `thermal.md` | Done; placeholder thermal data |
| Dynamics and faults (WP2 rest) | `dynamics.md` | Done; 11 cases × 2 designs |
| WP4 structure, CAD and FEA | `structure.md`, `cad.md`, `fea.md` | First pass done; STEP and GLB in `build/cad/` |
| WP5 hazards | `hazards.md` | Preliminary log, 13 hazards |
| WP6 economics | `economics.md` | Partial BOM; assessment **REVISE** |

## Key findings

1. **500 lbf is reachable for short holds.** The lead design gives 1,139 lbf static peak and 380 lbf continuous. It can hold 500 lbf for about 4 minutes from cold (placeholder thermal data, A-015).
2. **Low-force control (R-03) is not met.** The design feels like 86 kg of drum inertia at the handle. At 8 lbf the simple controller's tension error is about 290%, with cable slack-and-snap. Tracking at 500 lbf is good (about 4.5% error with the 1 kW supply).
3. **Releasing the handle at 500 lbf is a slingshot (H-01, S4).** The cable's stored energy launches the handle at about 5.5 m/s whatever firmware does, so a mechanical arrestor is required. Release detection does cut the follow-on end-stop snap loads.
4. **Power electronics need a braking resistor or energy buffer.** Without one, the bus passes 60 V within 0.3 s of a heavy pull. A 1 kW supply dips to undervoltage lockout when lowering 500 lbf.
5. **Shorting the motor windings on power loss looks like a reasonable passive fail-safe**: 0.2 m of hand lurch versus 1.15 m with the windings left open. This is an upper-bound model.
6. **Two of my own safety functions conflict.** A load cell stuck at zero looks like a handle release, so the load drops (H-02). A fault-handling policy is needed.
7. **The structure is sized for motor stall, but dynamic snap loads exceed stall** (up to about 4,300 lbf in the unprotected release case). They need their own load case and a mechanical end stop.
8. **FEA caught a real layout error:** the bearing bore broke through the top of the side plate. That is fixed, and the plate now shows a 2.6× static margin.
9. **Cost: REVISE.** Motors, drivers and power supply alone cost $910 at one-off prices, against a $500 retail target.

## Tests

119 tests pass (`make test`). `make ci` regenerates all reports, CAD and FEA and fails if anything changed.

## Main assumptions to challenge

- A-016: arm surrogate, cable stiffness and friction. Every dynamic result depends on them.
- A-015: thermal data is backed out of rated torque.
- A-017: every safety threshold and controller gain is a proposal.
- A-019: retail is modelled as BOM × a single multiplier.

## Open questions for the user

- How long must 500 lbf be held? This decides the thermal design.
- Is an energy buffer acceptable within "no battery operation"?
- Would you accept a lower peak, or two 250 lbf units, if that recovers low-force feel and cost?
- What mounting is intended: wall, floor or rack?

## Next smallest verifiable milestones

1. Simulate H-06 (frozen or inverted torque) and H-07 (encoder loss), and define a fault-handling policy that separates sensor faults from releases.
2. Compare inertia and cost for a lower-inertia motor set or a single dual driver, to address R-03 and R-12.
3. Mechanical handle arrestor concept plus a snap-load case in the structure model.
4. Price the remaining 14 BOM lines.
