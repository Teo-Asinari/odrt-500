# Status

## Active engineering goal — 2026-11-03

**Simulated today:** [dump monitor and pre-charge sequence](../docs/engineering/power-path-review.md). The dump monitor (active in R4) catches the fresh-bank dump failure 0.51 s after the fault (bus 55.14 V), with no false trips across the suite; the aged case still trips on 56 V overvoltage first.
**Start-up decided: direct supply charging** (owner, 2026-11-03): drive enabled at 24 s fresh / 15 s aged; the bank disconnect must close by default (the supervisor only powers up at 6.6 s); a failed-open disconnect times out with the drive disabled. Depends on the unverified EPP-500-54 constant-current mode; the resistor sequence (120 s) is the fallback, and the resistor stays as the service-discharge path.
Service discharge 83 s to 5 V; the discharge switch must be normally closed because the auxiliary rail collapses within 0.4 s.

**Power path (R4):** [review](../docs/engineering/power-path-review.md), [sizing](power_path.md). Bank behind the Regen Clamp's output: the clamp's diode blocks supply back-feed and its chopper stays the dump.
Sized: ≥17.8 A time-delay bank fuse, back-to-back MOSFET disconnect, one 6.8 Ω pulse resistor for pre-charge (68 s to enable, fresh) and service discharge (80 s to 5 V), passive 260 Ω balancing
(worst cell 2.82 V at the trip), dump current shunt with a fault rule independent of overvoltage. **Trip lowered to 56 V** (owner decision): full R4 rerun changes only the aged dump-failure cases (trip 58 ms earlier, 55.92 V peak, 2 V under the clamp's 58 V); all power-path checks pass.
Unverified: supply overload mode, cell leakage, clamp brake-rating meaning; no parts selected. Electrical definition and cost allowances now follow R4.

**Current decision: REVISE R4 — new lead candidate.** [R4 review](../docs/engineering/r4-review.md), [results](r4_candidate.md).
R4 = R3 + C1 with the bank moved onto the drive bus. Across all 54 scenarios it improves or holds every case with no new failed comparison: fast reversal 11.4 → 8.0% (aged 62% with trip → 12.1%, no trip),
full stroke 14 → 11%, higher bus minimums everywhere; refinements pass. Fast reversal/full stroke (voltage-limited at 5:1) and endurance (Km) still fail, pending the owner's motor/bus decision.
New: the bank exceeds its 11.7 A continuous rating only in fast reversal (aged cells would reach 70 °C if repeated back to back); worst cell at the 57 V trip is 2.99 V of 3.0 V; a fresh-bank dump failure
no longer trips, so dump detection must be independent. Without the non-realisable planned feedforward, fast reversal is 9.7%. Pre-charge, reverse blocking, balancing and fusing are not designed.


**Fast-motion review (earlier today):** [review](../docs/engineering/fast-motion-review.md), [study](fast_motion_study.md). The controller study's bandwidth diagnosis was wrong.
Fast reversal and full stroke are **voltage-limited** (52% / 32% of the motion on the back-EMF/bus bound, carrying 85% / 78% of the error). The one-way Regen Clamp also dumps 317 W of the
fast-reversal regeneration, draining the bank. A **bidirectional bank** at 5:1 takes fast reversal 11.4 → 8.0% (aged: 62% with trip → 12%, no trip), with no heavy/slow/endurance regression;
proposed as the R4 power topology, fault suite not yet rerun. No ratio passes heavy (needs ≥5:1 at 50–60 A) and fast (needs ≤4:1) together with the RO100 at 52 V: **owner decision** on motor/bus class or a reduced fast envelope, alongside the endurance Km decision.
The planned-acceleration feedforward is not realisable on hardware and should be retired. New report-only diagnostics: `voltage_limited_fraction`, `voltage_limited_error_share`.

## Previous checkpoint — 2026-11-02

**Controller study:** [review](../docs/engineering/controller-study.md). Proposed controller C1 (kp 4, release limiter 2.5 m/s, 0.15 m end zone)
on the full R3 suite ([results](r3c_candidate.md)): fast reversal 29 → 11%, full stroke 36 → 14% with no stop engagement, aged asymmetric set no longer trips.
Not adopted yet: fast reversal still fails 5%, gains need noise/margin analysis, and the end zone/limiter need human-factors review.

**Current decision: REVISE R3.** [R3 review](../docs/engineering/r3-review.md).
R3 = R2 + a conducted motor-to-frame heat path (aluminium base/skin) + a 30 V undervoltage trip (ODrive Pro: 15–58 V). [Results](r3_candidate.md):
slow heavy pull 128.5 → 104.7 °C; aged paired heavy 17% with trip → 0.18%, no trip; aged power-loss, aged endurance and fresh fast reversal no longer trip.
Remaining: endurance is motor-Km-limited (winding ~127 °C in derate all session; owner decision needed: derated envelope, 6:1, or a better motor);
fast reversal and full stroke need a controller study; aged asymmetric set and aged fast reversal still trip; 1% release imbalance still rotates the bar ~48°.

**Previous decision: REVISE R2.** [R2 review](../docs/engineering/r2-review.md).
R2 integrates the support and power revisions into one [CAD](r2_package.md) (56 parts, no clashes inside 323 × 139 × 100 mm) and one
[full-suite simulation](r2_candidate.md) (54 scenarios, refinements pass). Bearings and shafts now pass at the simulated loads with 850–1000 N belt preload,
and fresh paired heavy tracking improves to 0.18%. But 5:1 raises winding heat (slow heavy pull 128.5 °C, past derate), the aged bank still trips
in every hard case, and fast reversal, full stroke, endurance and asymmetric release still fail. Next: motor thermal path, bank energy, then fast-reversal control.
`make quick` / `make t` iterate without the full suite; `make ci` skips studies whose input fingerprint is unchanged.

**Previous decision (R1): REVISE the compact candidate.** [R1 review and original-goal audit](../docs/engineering/compact-candidate-r1-review.md).
The [CAD-derived candidate](compact_candidate.md) completes 54/54 scenarios with selected numerical verification passing; 207 full-suite tests pass.
The [current mechanical screen](compact_structure.md) rejects the spindle/bearing/bridge arrangement under its proposed analytical criteria.
Paired aged-bank operation trips; fast reversal and endurance remain failed design cases. A [compact FMEA](../docs/engineering/compact-fmea.md)
tracks outstanding circuit, wiring, cooling, retention, mounting and model-validation work. The goal is active and incomplete.
The next action is a combined support/transmission and power/buffer revision, preserving owner force and size requirements.

**Latest evidence:** [latched-trip and compact-layout review](../docs/engineering/latched-trip-and-layout-review.md).
Voltage/thermal trips now latch; recovery cannot restart a unit. The reference completes 27 cases with passing numerical verification;
the alternative-buffer experiment completes 48 selected combinations and four refinement studies. The full software run passes 198 tests;
three additional targeted CAD checks pass. [Compact CAD experiment](compact_package.md): 64 parts inside the owner body target with no modeled
unintended solid or rope/guide swept collisions. Missing wiring, sensors, retention, cooling and electrical clearances still prevent a complete package claim.
CAD-derived inertia differs from the reference: the next action is a full candidate simulation with consistent inertia/bank/routing/thermal assumptions.
Electrical/cost allocation now covers guide actuation too: 25 functions / 92 ports. Earlier checkpoints below are historical where superseded.

Latest checkpoint: [compact-buffer review](../docs/engineering/compact-buffer-review.md).
The separate [compact capacitor experiment](compact_buffer.md) evaluates 36 variant/case combinations:
20 integrate and 16 retain explicit solver failures at voltage-switching events. The smaller bank is not selected or qualified.
[Functional electrical schematic/netlist and preliminary harness](electrical_definition.md) now define 24 functions / 84 semantic ports;
physical wiring and circuit ratings remain open. [Full-function preliminary cost allowances](preliminary_costs.md)
include mechanics, protection, harness, board, mounts and production/commercial assumptions; they are unquoted estimates.
The next simulation action is explicit voltage-trip latching/reset and event handling, followed by reference and alternative re-verification.
The complete compact assembly is still outstanding. Thirty-three targeted tests pass; the earlier 190-test full run remains baseline evidence.

The full eight-item goal is in [goal.md](../docs/engineering/goal.md), with evidence tracked in [plan.md](../docs/engineering/plan.md). **The goal is active and incomplete.**

The owner rejected the 20 L placeholder and chose a **323 × 139 × 100 mm (4.4897 L) envelope or smaller per unit**: [ADR-003](../docs/architecture-decisions/ADR-003-voltra-sized-envelope.md). The published VOLTRA mass of 5.8 kg is a provisional comparison benchmark, not an adopted owner mass limit.

New reproducible evidence (`make architecture`):

- [Measurable criteria](engineering_requirements.md), with owner/provisional/verification origins.
- [Primary-source component review](component_review.md). The legacy 56 V dump and 60 V trip conflict with the S1's 50.5 V maximum; the historical 53 V bus result **does not pass component compatibility**.
- [Compact architecture screen](architecture_screen.md): 6,912 combinations, including direct drive, legacy and folded belt layouts, winding layers and guided/unguided paths. Zero pass all current comparison screens. This is assumption-dependent screening, not proof that the product is impossible; no full electrical package or coupled candidate model has yet been qualified.
- 49 targeted engineering/input/structural tests pass (3.63 s); input validation and architecture generation pass. The complete legacy test suite and all exports have not been rerun for this goal turn.

The coupled reference core is now implemented: [coupled report](coupled.md), [machine-readable results](coupled.json), [model interface](../docs/engineering/model-interface.md) and [platform charter](../docs/engineering/platform-charter.md). The owner wants a reusable open resistance-control foundation with a trainer as its reference implementation. The original eight-item engineering goal remains intact.

Current verified evidence:

- **190 tests pass** in the complete test run (107.91 s).
- **25/25 coupled cases** complete, including all 11 full reference/limit duty cycles, paired asymmetry, independent/peer power-loss response, stuck sensing, inverted/frozen command, communication loss, release, emergency stop and dump failure.
- **Five solver-resolution refinements pass**, including symmetric and explicitly 1%-imbalanced paired release. Mean/difference coordinates corrected a numerical symmetry problem without suppressing physical asymmetry or loosening criteria.
- **13 parameter-uncertainty cases** complete. Low Km and low user damping materially degrade tracking; this is retained as failed performance evidence.
- Maximum full-suite energy residual fraction is **2.32e-6**. This validates bookkeeping consistency, not physical fidelity.
- The source/configuration fingerprint in `reports/coupled.json` matches the current implementation. Three plots were generated from the saved traces; heavy-set and paired-fault plots were visually inspected.

Under the current assumptions, the single heavy set tracks at about 0.14% RMS error, winds to about 78.5 °C and keeps the bus around 46.3–49.0 V. Fast reversal, full-stroke motion and endurance fail proposed tracking/overshoot criteria; high-speed cases also exceed electrical-frequency/voltage-control screens. A 1% paired release imbalance predicts large bar rotation in the simplified model. No hardware operating envelope is qualified.

The selected **simulation reference** is RO100 Lite / 6:1 / 30 mm drum core / six turns and two layers / 5 mm rope. It uses the documented 22-series 350 F cell bank (15.91 F, 0.0704 Ω), a separate 3 mF drive bus and a sourced EPP-500-48 supply candidate with its forced-air assumption. This is not yet a complete package inside the owner envelope, and its DC-equivalent motor current conventions need calibration.

The controlled measurement and independent-review requirements are documented in [validation-plan.md](../docs/engineering/validation-plan.md), with a future measurement provenance/uncertainty schema. No measurements, physical output or hardware tests were performed.

**Next work:** carry the reference and rejection evidence into mechanically connected CAD/load paths, preliminary electrical schematic/placement/harness, complete per-unit/paired/accessory cost estimates, and a requirement-by-requirement final package audit. Preserve the remaining model limitations, particularly real fault detection, latching/rearm, switching/inductance, cable-break/contact/fatigue behavior and hardware parameter validation. The engineering goal is active and incomplete.

The iteration-3 results below are a **historical reference**, with the superseded volume target and incompatible bus assumptions. They have not been regenerated for the changed engineering inputs. Do not treat their earlier pass statements as a current integrated feasibility result.

## Historical iteration-3 reference

Last updated: 2026-11-02 (iteration 3). Hand-written; other reports are generated by the CLI.

## Current decision and implementation

Simulation-only concept. [ADR-002](../docs/architecture-decisions/ADR-002-modular-units.md) supersedes the integrated single-unit platform: two independent 250 lbf units, 500 lbf combined on a bar, each with mains power, a supply and a buffer. A common board is an accessory; wall, rack and door adapters share a proposed interface. No physical high-force prototyping or human-load testing is authorized; Gate D remains open.

The executable iteration-3 reference retains one RO100 and a 6:1 belt per unit. The supply limit is now **500 W per unit**, with an ideal **2 F buffer**. The smaller supply has no selected vendor part, price or verified dimensions. Estimated electrical envelopes are explicitly labeled. The old platform and exercise-animation code remain as historical references; the default CAD/visual workflow generates modular unit and paired-board artifacts.

## Results and assessment: REVISE

| Item | Current result | Interpretation |
|---|---|---|
| Full heavy set, 250 lbf per unit | 1.7% RMS tracking error; bus 47.3–53.4 V | Passes the ideal bus limits in this case; ESR, supply dynamics and enclosure heating are not coupled into the dynamic model |
| Winding, heavy tempo / 3 s pauses / slow 200 lbf | About 47 / 50 / 54 °C from cold | Lower unit force greatly improves predicted heating; motor constants and thermal paths are still uncertain |
| Low-force tracking at 8 lbf | About 12% error | Acceptance criteria and measured feel remain unresolved |
| Fast reversal | About 29% tracking error | The retained drivetrain is not satisfactory across the full motion envelope |
| Release with safety layer enabled | 932 lbf snap peak | A mechanical arrestor/damper and its load case remain unresolved |
| Reference unit package | 444 × 840 × 278 mm; 103.8 L | Fails the provisional 20 L compactness target (A-026); this is not a Voltra-sized design |
| Known modeled metal + motor mass | At least 19.5 kg per unit | Includes the proposed 3 mm aluminium skin; electronics, rope and hardware are additional |
| Mechanism / electrical placement collisions | 0 | Mechanism solid checks plus electrical/rope keep-out boxes; not a wiring, service-access or safety-clearance qualification |
| Rear mounting group | Up to 352 MPa vs proposed 120 MPa allowable | Fails at the snap load; the large exit-to-mount lever dominates |
| Common 25 mm board | 12.2 MPa bending; 6.5 mm edge deflection | Stress passes the placeholder allowable; deflection fails the proposed 2 mm limit |
| Side-plate FEA, static motor stall | 30 MPa; 3.0% mesh change; 0.08% load error | Converged for that static load only; not a snap-load or complete-mount validation |

The 72 mm single-layer drum and retained 4° fleet angle require **515 mm of straight lead** before the turning sheave. Putting electronics into a separate tray makes the integration reproducible, but does not solve compactness. The enclosure, board assembly and interface are concept space claims with unresolved supports and adapter joints; they are not fabrication drawings.

The mount calculation screens six pull directions at max(stall, observed safety-on peak). For the current geometry it requires about 107 mm² tensile area per bolt under the proposed stress model, versus 36.6 mm² assumed. Moving the interface closer to the exit or changing the bolt group is a separate design trade. The ideal symmetric board model requires at least 37.1 mm thickness to meet the proposed stress and deflection criteria. Neither calculation qualifies joints, retention or substrates.

## Cost scope

The per-unit BOM has **$332.45 USD** in cited lines, plus 32.47 GBP, 71.46 CAD and 12.28 in an unverified dollar currency. **14 of 20 lines are unpriced**, including the replacement supply, buffer and interface. Two units double these amounts; the common board and adapters add further costs.

The old $267.90 supply was removed from the subtotal because it is not the new candidate. This is an unknown replacement cost, not a demonstrated saving. The known USD floor alone implies $665–1,330 retail per unit under the unsourced 2–4× multipliers. $500 retail per unit remains unsupported; a $500 manufacturing cost is unresolved.

## Verification

Input validation passes for 15 requirements, 26 assumptions, 11 scenarios and 34 component options. The simulation now includes 20 dynamic cases for each of two motor-count options. `2x` in those options means two motors on one drum, **not** two independent modular units.

Report, modular CAD/STEP/GLB, visual-copy, motor-study and FEA generation have completed successfully. **159 tests pass** in the final complete run (93.4 s). The two failures found during integration were an index-dependent negative test after adding the full-set case, and a legacy-platform packaging test using the new supply envelope; both were corrected. Current modular placement and the full-set ideal bus limits have regression coverage. All 17 generated markdown reports carry the current input hash, and current GLB files pass container-length and metre/Y-up wrapper checks.

`make ci` additionally compares reports to Git HEAD. Its final freshness check requires the regenerated changes to be committed; no commit has been made. All prior uncommitted work remains in the working tree. Historical files already present under `build/` can remain there; use the current filenames below.

## Current artifacts

- [Modular integration and mount/board calculations](modular.md)
- [Per-unit electronics budget](electronics.md)
- [Economics](economics.md), [dynamics](dynamics.md), [thermal](thermal.md) and [hazard register](hazards.md)
- `build/cad/odrt250_unit.step`; `odrt250_unit_full.glb`, `_cutaway.glb`, `_exploded.glb`
- `build/cad/odrt500_modular_board.step` and `.glb`; current GLBs are also copied to `build/visual/`
- Historical single-platform animation export remains available through `odrt visual --legacy-platform`, under `build/visual/legacy/`.

## Next smallest verifiable work

1. Trade narrower/multilayer drums or an independently reviewed cable-guiding arrangement against fleet distance, changing effective radius, inertia, rope bend life and winding capacity. The current package must shrink substantially before selecting an enclosure or mount.
2. Place the common interface near the resulting cable load path; rerun arbitrary-direction reactions, plate/joint checks, asymmetric board loads and adapter retention. Wall/rack substrates need qualification; no high-force door capability is established.
3. Model two independent units on one bar, including one-sided faults and a coordinated response that preserves each unit's local safety functions (H-16). Define mount-state and board-mode sensing (H-17).
4. Select and quote the supply, buffer and rope, then couple ESR/sag and enclosure thermal conditions into the performance model. Settle RO100 Kt/resistance uncertainty with documented data or a separately authorized controlled test plan.
5. Develop the mechanical handle arrestor/damper concept and its transient structural load case. Gate D remains required before any high-force hardware work.
