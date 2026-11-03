# Engineering package work plan

The complete objective is preserved in [goal.md](goal.md). This plan tracks evidence, not completion by intent. The goal remains active until every numbered deliverable has been implemented and inspected. A REVISE or NO-GO product assessment can be the engineering outcome; it does not excuse missing simulations or deliverables.

| Goal item | Required evidence | Current gap / action |
|---|---|---|
| 1. Measurable requirements | Typed requirement ledger with origin, units, thresholds, scenarios and acceptance methods | Existing requirements are mostly prose; add supplemental measurable design criteria, owner/provisional distinction |
| 2. Compact architecture trade | Reproducible equal-envelope drivetrain/routing sweep; radius, capacity, inertia, torque/speed/current, cable bend/strength, stored energy and load-path checks | Current reference is 104 L; evaluate narrower drums, multiple layers, guided routing and direct drive without assuming missing ratings |
| 3. Real components | Primary-source data with dates, rated conditions, electrical compatibility, availability and prices/unknowns | S1 maximum is 50.5 V; earlier 53 V bus result is incompatible. Recheck motor variants, supply cooling, rope and buffer |
| 4. Coupled simulation | One/two-unit closed-loop model linking mechanics, unilateral cable, voltage/current/ESR, regen/dump and thermal derating; asymmetric faults | Coupled one/two-unit reference implemented and numerically verified; retain physical/phase-convention/detection/contact limitations and review them with the remaining hardware definition |
| 5. Consistent geometry/electrical definition | CAD/STEP/GLB linked to selected candidate; preliminary schematic, placement, connector/harness table and explicit fidelity labels | Current CAD is a space claim; electrical blocks and mounting adapters incomplete |
| 6. Verification | Energy accounting, analytical checks, time-step refinement and parameter sensitivities; normal/fault criteria with results | Legacy unit tests do not prove integrated fidelity; add independent conservation and convergence checks |
| 7. Complete preliminary costing | Every part/function included, per-unit vs pair/accessories, prototype/100/1000 quantities, sourced prices vs explicit planning estimates/ranges, retail overhead | Existing BOM is a priced floor. No fabricated supplier quotes or hidden zero-cost lines |
| 8. Validation and review | Controlled measurements, equipment, acceptance evidence, specialist review and hardware gates | Validation/measurement/review plan and provenance schema written; connect remaining mechanical/electrical FMEA and final package evidence; no hardware activity authorized |
| Final assessment | Evidence-backed GO/REVISE/NO-GO, supported envelope, failures/uncertainty, next validation, repeatable CLI | Cannot be declared until the preceding deliverables exist and have been checked |

## Execution order

1. Formalize criteria and reconcile component ratings. Establish a reproducible compact architecture screen.
2. Implement the coupled one/two-unit simulator with conservation, convergence and sensitivity evidence. Reassess the architecture from these results.
3. Carry the selected/rejected candidate evidence into mechanical CAD/load paths, preliminary electrical schematic and harness.
4. Complete preliminary costing and validation/review documents; integrate generation into one reproducible command.
5. Audit all eight goal requirements and the final assessment against current files and actual commands before marking the goal achieved.

## Scope and decision policy

- Owner decisions: ADR-001/002/003 and the current design brief; 250 lbf/unit, two independent mains-powered modules, common board and universal mounting intent.
- Numeric compactness, mass, smoothness and transient screening thresholds are proposals unless the owner explicitly adopts them. They are not human-use safety limits.
- Missing manufacturer data remains unknown. Analytical lower bounds and estimated package dimensions are not complete layout or fatigue validation.
- A unit test passing is software evidence only. Keep physical qualification and independent review separate.
- Do not substitute visual polish or a restricted simulation for the full engineering objective.

## Initial evidence (2026-11-02)

The goal file and current clean `main` worktree at `05bc106` were inspected. This is progress: primary-source review found an S1 bus-rating conflict that changes the next design action. S1 absolute maximum is 50.5 V; its published modulation utilization is 78%. The historical simulation's 56 V dump / 60 V trip is incompatible with that candidate. The new component screen must reject it instead of repeating its previous pass claim.

## Owner steering incorporated

The owner rejected the 20 L placeholder and explicitly chose the published VOLTRA dimensions or smaller. ADR-003 records the 323 × 139 × 100 mm (4.4897 L) target. Mass remains a provisional comparison criterion. The earlier optional 20 L / 10 kg question is superseded and does not need an answer.

## Progress checkpoint

- Requirements ledger and primary-source component catalog implemented and validated. `make architecture` generates the measurable criteria, component review and 6,912-case compact architecture screen. Full machine-readable cases are reproducibly generated under `build/engineering/`; the tracked JSON is a compact summary.
- ADR-003 owner size target is enforced axis by axis, allowing rigid orientation changes. Mass and smoothness/lifetime criteria remain provisional.
- Architecture screen covers occupied-layer capacity, dead turns, inertia, torque/current/speed, provisional routing, D/d, stored energy and documented spliced rope strength. No candidate passes every current comparison screen; complete packaging and qualification remain open.
- `make check` passes. `pytest tests/test_engineering.py tests/test_inputs.py tests/test_modular.py`: 49 passed. Git whitespace checks pass.
- Next: implement coupled one/two-unit dynamics with ESR, winding/drive/supply/buffer thermal behavior, energy ledger, faults, time-step refinement and uncertainty sweeps. Preserve this entire plan and the full goal scope. The goal is not complete.

## Coupled foundation checkpoint

The previous goal turn made progress through requirements/component/architecture artifacts. This turn adds the coupled reference, interface/contributor contract and measurement/review plan.

Implemented in `src/odrt/coupled.py` and `configs/coupled.yaml`: variable winding payout/radius, unilateral elastic/damped cable, closed-loop control and current/voltage limits, separate bank/DC-link states joined by ESR, one-way source and regeneration/dump, seven thermal states per unit, one/two-unit rigid-bar interaction and asymmetric fault policies. The source-backed catalog remains separate from explicit modeling assumptions. No physical I/O exists.

Evidence: `make coupled-verify` completed 25 cases, five resolution comparisons and 13 uncertainty perturbations; all numerical verification criteria passed. `make test`: 190 passed. The maximum case energy residual fraction is 2.32e-6. Report/source fingerprint consistency and whitespace checks pass. Plots were inspected.

Two defects were found and corrected: discontinuous gearbox efficiency caused rest-state solver chatter; a separate-unit coordinate integration seeded spurious bar rotation during a perfectly symmetric release. The corrected model uses smooth dissipative efficiency and mean/difference coordinates. A separate explicit 1% imbalance release still produces large, converged rotation; the physical fault risk has not been removed or hidden.

Known failed design cases remain visible: fast reversal, full-stroke movement and endurance. Conditional heavy-set performance does not establish overall feasibility. The complete 4.4897 L package and preliminary connected mechanical/electrical/harness design, full preliminary economics and final all-requirement audit remain outstanding. Do not mark the goal complete from solver results alone.

Next execution: mechanically/electrically consistent reference package and load paths, then complete preliminary costing and final evidence integration. Review remaining model gaps against those interfaces; update or extend the simulation where necessary. Preserve all eight original goal requirements and the owner's open-platform intent.

## Compact buffer / electrical / preliminary cost checkpoint

See [compact-buffer-review.md](compact-buffer-review.md) for the current evidence and precise limitations. New reproducible targets are `make buffer-study`, `make electrical` and `make preliminary-costs`; local CI includes them. The compact bank reduces cell body volume and mass substantially, but 16 of 36 selected-case integrations fail at voltage-switching events. Twenty complete with maximum energy residual fraction below 1.70e-6. This changes the next action: implement explicit voltage-trip latching/reset semantics and event handling, then rerun verification before selecting this bank.

Functional preliminary schematic/netlist (24 functions, 84 semantic ports) and a harness register now exist. Pinouts, conductors, gauges, lengths, connectors, physical routing and protective ratings remain unresolved. Preliminary costs cover all currently defined functions plus mechanics, board, mounts and production/commercial allowances; all prices are labeled unquoted planning ranges. No compact integrated machine is established. Thirty-three targeted tests pass, input checking passes, and the baseline and experiment source fingerprints match. The full goal remains active.

## Latched protection and compact CAD checkpoint

[Current detailed evidence](latched-trip-and-layout-review.md): voltage/thermal event latching and a recorded independent BDF fallback resolve the prior chatter/interpolation failures. The full test run passes 198 tests; three additional targeted CAD checks pass. The 27-case reference and 48-case buffer experiment complete with passing selected numerical verification. The new 64-part compact CAD experiment clears its modeled solid/rope/guide overlap checks inside the owner envelope, but missing functions and unqualified electrical/thermal clearances prevent a complete fit claim. CAD-derived reflected inertia is 0.024254 kg·m² versus the simulated reference's 0.019344. The functional electrical/cost allocation now includes guide actuation, at 25 functions / 92 ports.

Next execute a separately identified compact candidate with CAD-derived inertia and the smaller bank across the complete normal/fault suite; reconcile routing and thermal assumptions. Then finish wiring/circuit/component placement, structural/mount verification and the final original-scope audit. No goal completion is established by the new CAD space claim.

## CAD-derived candidate and load-path checkpoint

[Current R1 review and original-scope audit](compact-candidate-r1-review.md): the CAD-derived candidate completes 54 scenarios across fresh/aged banks, four resolution studies and eight uncertainty cases with passing numerical verification. The complete test run passes 207 tests. A two-events-between-samples fallback bug was reproduced, corrected and regression-tested; reference and buffer studies were rerun against the correction.

The design decision is REVISE: aged paired heavy use trips, fast reversal/endurance fail, and the actual spindle/bearing/bridge geometry fails analytical load comparisons. The new structural screen uses candidate peak loads and CAD locations, not the legacy mounts. A 14-row compact failure-mode/review register connects the missing physical work to validation. All eight original items remain tracked; the detailed circuit/harness, retention, mounts, thermal/isolation and failed support/power/dynamic envelope prevent goal completion.

Next revise the support/retention and rated belt/preload with the power/buffer margin, then rerun the consistent candidate as a batch. Preserve force/size targets and the open-platform objective; do not replace them with a smaller passing envelope.

## R2 integrated candidate checkpoint

[R2 review](r2-review.md): the support (roller bearings, two-ended 25 mm drum shaft, 5:1 belt) and power (ODrive Pro, EPP-500-54 at 52 V, Regen Clamp with upstream 20-cell TV bank) revisions are now one CAD (`make r2-package`) and one full-suite simulation (`make r2-candidate`, parallel). The support screen is repeated at the simulated loads and passes at 850–1000 N/span preload. Decision REVISE: 5:1 raises winding temperature by about 28–32 °C, the aged bank trips in every hard case, and fast reversal, full stroke, endurance and asymmetric release still fail.

Next: improve the motor thermal path (stator carrier into base/walls), recover bank energy within the envelope, then treat fast reversal/full stroke as a control/voltage problem with any gain change reported separately. Wiring between the three cell groups, trays, retention, belt rating, frame stiffness, isolation and airflow remain open. The goal remains active and incomplete.

## R3 heat path and undervoltage checkpoint

[R3 review](r3-review.md): a lumped aluminium frame node (housing-to-frame 0.3 K/W, frame-to-room 1.4 W/K, frame-to-air 1.5 W/K, 800 J/K) and a 30 V undervoltage trip (`make r3-candidate`) recover the R2 heat regression and the aged-bank trips in the heavy, power-loss and endurance cases, with numerical verification passing. Decision REVISE. Endurance is now limited by the RO100's internal winding-to-housing path (A-022) and needs an owner decision; fast reversal/full stroke need a separately reported controller study; aged asymmetric and aged fast reversal still trip. Physical work listed in the R2 review remains open. The goal remains active and incomplete.
