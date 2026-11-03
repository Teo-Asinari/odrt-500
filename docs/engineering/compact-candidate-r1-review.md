# Compact candidate R1 review — 2026-11-02

**Decision: REVISE this candidate. The original engineering goal remains active.**
The preceding turn made progress through latching, electrical/cost definitions and
a compact CAD space claim. This turn couples that CAD's known rotating inertia,
compact buffer and routing/air estimates into complete scenarios, then applies
the resulting load envelope to the actual shaft/bearing/support geometry.

## Current reproducible evidence

- `make test`: **207 passed**, 147.94 s. Includes independent CAD-to-plant stored
  energy, analytical bearing equilibrium/shaft sections, and a regression for two
  fallback events between saved output samples.
- `make coupled-verify`: 27 reference cases, five resolution comparisons and
  13 uncertainty cases; numerical verification passes after the fallback fix.
- `make buffer-study`: 48 selected combinations plus four refinement studies;
  all cases integrate and selected numerical verification passes after the fix.
- `make compact-candidate`: **54/54 complete configured scenarios** across fresh
  and aged compact banks, four three-resolution studies and eight physical
  uncertainty cases. Numerical verification passes. Maximum scenario energy
  residual fraction is **1.20e-5**. Largest medium-to-fine metric change in the
  selected refinement is about **0.00183%**. Physical design failures are retained.
- `make compact-structure`: analytical load corners using current CAD and the
  candidate's observed force/current envelope. Equilibrium residual is below
  2.6e-13 N and zero Nmm at reported precision. The hardware design comparisons fail.

Generated evidence: [candidate results](../../reports/compact_candidate.md),
[mechanical screen](../../reports/compact_structure.md),
[CAD experiment](../../reports/compact_package.md),
[tracking plot](../../reports/figures/compact_candidate_tracking.png), and
[fault plot](../../reports/figures/compact_candidate_faults.png).
Plots were generated from saved traces and visually inspected; their input-file
hashes are in `reports/compact_plot_provenance.json`.

## What now agrees, and what still does not

The catalog rotor, CAD drum/wheel, motor adapter, spindle and pinion are represented
once in the candidate plant: **0.024254 kg·m²** referred to the drum. The added drum-
equivalent term is 0.005210 kg·m²; the catalog rotor is then added by the plant.
This replaces the reference's 0.019344 kg·m² for this separate candidate only.

Nominal routing length is **0.148 m**, based on 90 mm takeoff-to-guide plus 58 mm
guide-to-body exit. Guide contact curvature and actual exit motion remain unresolved.
The air-only storage estimate is **5.415 J/K**, based on gross body volume before
solid displacement. Conditional 25 CFM gives **14.229 W/K** heat-flow conductance;
this is the supply's required flow, not a selected or verified installed fan.
Other thermal paths remain proposals. Controller gains are unchanged.

The candidate remains a space claim for much of the electrical package. Wiring,
connectors, cell leads, sensor overload paths, guide actuator, shaft retention,
mounts and cooling/isolation geometry are incomplete. The 1 mm supply partition
is not a qualified mains clearance. The CAD's geometric fit is not a full fit claim.

## Design failures that change the next action

| Evidence | Result | Consequence |
|---|---|---|
| Single heavy set | About 0.16% RMS error in fresh and uniformly aged bank cases | Conditional simulated result only; does not establish paired robustness |
| Paired heavy set | About 0.74% RMS fresh; about 72% aged with undervoltage shutdown | The aged compact bank lacks margin for the requested operating case |
| Fast reversal, fresh bank | About 56% RMS error; peak about 2375 N | Controller/drive/inertia envelope is inadequate for this request; that peak feeds mechanical screening |
| Endurance | About 30% RMS fresh; aged case trips and approaches 99% error | Thermal/power/duty requirements remain unresolved |
| Explicit 1% paired release imbalance | About 48° bar rotation in both bank corners | Existing stop policy and simplified physical model cannot establish acceptable release behavior |
| 10 mm motor spindle | About 270–316 MPa equivalent stress versus proposed 175 MPa allowable | Revise spindle, span and overhang; do not qualify the existing support |
| Motor bearing reaction | About 4.47–5.44 kN versus 1.97 kN catalog static rating | Current bearing arrangement is rejected by the static comparison; C0/P is only 0.36–0.44 versus proposed minimum 2 |
| Drum bridge beam surrogate | About 226–610 MPa versus proposed 120 MPa | Thin bridge needs a boss/rib/section and joint redesign; this surrogate is not validated plate FEA |

Structural corners deliberately combine uncorrelated maxima: 2375 N rope force,
15.17 Nm motor torque from the largest of catalog peak or simulated current × Kt,
two winding heights and proposed belt preloads. Low preloads also fail the positive
slack-side comparison. The surrogate does not establish actual belt transmission,
joint strength, fatigue or a complete mount load path. Higher-fidelity loads and
FEA must follow an engineered support revision; these numbers are not allowable
human-use loads.

The small-room/flow/inertia sensitivities are selected short paired sets. They
do not prove long-duty cooling performance. Inertia perturbations currently
co-vary plant inertia and feedforward estimate; independently wrong calibration
is not covered. Low-Km or extra-inertia cases can look cooler because they trip;
that is a failed operating case, not a thermal improvement.

The parallel-cable rigid-bar model omits gravity along the payout axis and has
virtual endpoint/drum travel stops, not engineered physical contact. Large-angle
and released-body trajectories therefore cannot qualify actual bar motion.
These limitations must be resolved or bounded for the intended mounting/exercise
geometry before claiming physical fault performance.

## Original-goal evidence audit at this checkpoint

| Original item | Evidence now present | Remaining work; no completion inference |
|---|---|---|
| 1. Measurable requirements | Typed owner/provisional criteria, force/stroke/speed/duty scenarios, owner body target | Mount-specific conditions and acceptance/validation of provisional thresholds remain open |
| 2. Compact architectures | 6912-case screen, compact CAD, CAD inertia, variable winding, release cases and analytical load rejection | Revise failed support/power/dynamic envelope; select rated transmission and resolve guide/rope fatigue |
| 3. Credible candidates | Sourced motor/drive/supply/cells/rope/bearings and explicit unknown availability/pricing | Protection, sensing, connectors, actuator, fan and retention parts are largely unselected |
| 4. Coupled simulation | Reference and CAD-derived candidate, one/two-unit mechanics/control/power/ESR/thermal and named faults | Cell imbalance, detector implementations, switching/inductance/contact/fracture, calibrated thermal paths and released-body validity remain unresolved |
| 5. CAD/electrical/harness | 64-part compact experiment; 25-function/92-port semantic circuit; preliminary harness register | Mechanically rejected supports; no complete pin-level preliminary circuit or engineered conductor routing/gauges/connectors; incomplete sensors/mounts/cooling/isolation |
| 6. Verification | Independent equations/energy tests, full suite, selected convergence and uncertainty studies, failed design criteria visible | New support/plate/joint FEA, independently wrong controller calibration, fault-acceptance limits and physical validation remain open |
| 7. Preliminary economics | 36 allowance lines, unit/pair/board/adapter alternatives and production/commercial/NRE assumptions; all electrical functions allocated | Quotes, actual production drawings and assembly/test time are absent; revision will change estimates |
| 8. Validation/reviews | Validation plan, measurement provenance schema and compact FMEA | Close review actions against the actual revised design; no physical validation or hardware authorization inferred |

The audit does not prove completion. The open platform contracts and reproducible
models are useful engineering infrastructure; the reference machine is still
under development. Preserve the entire original scope.

## Next implementation

Revise the motor bearing span/overhang, spindle, shaft boss/bridges, positive
retention and rated belt/preload together. Reassess the buffer/voltage/power margin
and rotating-mass envelope without weakening the owner force or size target.
Batch geometry/component changes before rerunning the complete candidate suite.
Then engineer the remaining circuit/harness/thermal/mount interfaces and their
verification. Follow [compact-fmea.md](compact-fmea.md) and the validation plan.
Do not treat the current rejected assembly as the final virtual product.
