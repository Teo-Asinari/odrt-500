# Latched-trip and compact-layout checkpoint — 2026-11-02

The previous goal turn made concrete progress through alternative-buffer evidence,
functional electrical/harness artifacts and cost allowances. This turn addresses
the numerical failure it exposed and develops a compact CAD integration experiment.
The complete original goal remains active; none of these results establishes a
finished virtual product.

## Protection and numerical evidence

Voltage and winding/drive/cell thermal crossings now latch a unit off. Bus recovery
does not restart it. Initial overtemperature starts latched; a new scenario run
initializes state. There is no hardware rearm authorization workflow. Configured
peer response follows the actual trip time plus the assumed delay. Event transitions
change discrete/controller states without an instantaneous stored-energy change.

CasADi 3.8.2 CVODES event interpolation failed on several aged-bank trajectories.
A narrow, recorded `CV_ILL_INPUT` fallback uses SciPy 1.13.1 BDF event location with
the same equations, modal coordinates, quadratures, tolerances and step cap. Other
errors propagate. An independent analytical exponential-decay/event/quadrature
test covers the fallback. The actual backend and original diagnostic appear in
each case's JSON. Experimental solver support remains a limitation.

Verified current results:

- `make test`: **198 passed** in 114.08 s. Three subsequently added CAD geometry/
  swept-volume/inertia checks also pass in their targeted run. No full 201-test
  result is claimed here.
- `make coupled-verify`: **27/27 reference cases**, five resolution studies and
  13 uncertainty cases; verification passes. Maximum reference energy-residual
  fraction is 4.10e-6.
- `make buffer-study`: **48/48 selected case/variant combinations** integrate with
  finite values and passing energy checks. Maximum energy-residual fraction is
  5.47e-6. Four additional three-resolution studies pass; the largest
  medium-to-fine metric change is about 0.0019%, and the largest trip-time change
  is about 2.15 microseconds, below the proposed 0.1 ms comparison criterion.
- Reference and alternative fingerprints match the current source and inputs.
  Passing integrations do not turn fast reversal/endurance or aged-bank trips
  into successful design cases. Normal-operation trips are explicit failed checks.

The earlier 20-complete/16-failed buffer experiment is historical. The current
report replaces it with latched-event results and retains the solver fallback
provenance rather than hiding the numerical defect.

## Compact geometry experiment

`make compact-package` generates STEP, full/cutaway GLBs and a tessellated CAD
preview for a vertically oriented drivetrain in the owner body envelope. It
includes a hollow drum, 6005 bearing envelopes and stationary dead shaft, a
motor spindle and 6000 bearing envelopes, connected support bridges/posts, wheel
webs, pitch/belt proxies, occupied winding space, supply partition, 22 compact
cell bodies, guide carriage/screw and provisional electrical allocations.

Current geometric evidence: **64 parts**, all within **323 × 139 × 100 mm**;
zero unintended solid overlaps; zero modeled rope-path or guide-sweep collisions.
Four belt/pulley pitch-envelope contacts are explicitly identified as tooth-
engagement proxies rather than silently deleted collisions. The first arrangement
failed collision checks and was revised; no relaxed overlap tolerance was used.

The full and cutaway GLB binary lengths and vertex-derived bounds were checked.
After the existing metre/Y-up wrapper, extents are 0.323 × 0.100 × 0.139 m and
0.323 × 0.098 × 0.139 m respectively. The CAD preview was visually inspected.

This is **not a complete package fit**. Electronics boxes are mostly unsourced
space claims. The 1 mm supply partition is not an electrical isolation rating.
Capacitor leads, wiring, sensors, positive retention, mounting joints, connectors,
guide actuator/end stops, real cooling ducts and electrical keep-outs remain
incomplete. The body slots do not establish a sealed or durable rope exit. Belt
teeth, tensioning, loads and guide contact curvature/fatigue remain unqualified.
Two-millimetre bridges/flanges require structural and joint checks.

Inertia exposes a required coupling change: CAD drum + wheel is about
0.000397 kg·m² versus 0.000300 in the reference. Including the proposed motor
adapter/spindle/pinion and catalog rotor gives about **0.024254 kg·m²** reflected
at the drum, versus **0.019344** in the existing reference. Rope and rotating
bearing mass are still additional. The compact CAD and the verified dynamics
must not be presented as the same design until this and routing/thermal
assumptions are reconciled.

The functional electrical definition now also includes guide actuation, feedback
and inhibit: **25 functions / 92 semantic ports**. Its cost allocation is covered
by the guide/traverse line; all 25 functions have exactly one cost allocation.
No actual guide motor, driver, sensing or pinout is selected. Cost totals remain
unquoted planning allowances.

## Next required engineering

1. Carry the CAD-derived inertia and compact bank into a separately fingerprinted
   candidate simulation across complete normal/fault scenarios. Keep the reference
   and its verified reports available for comparison.
2. Reconcile actual cable routing/free length, guide contact geometry and thermal
   paths with that candidate. Resolve failed operating and release cases rather
   than treating successful integration as a pass.
3. Place the remaining functions and engineer the preliminary circuit, conductor
   routes/lengths/gauges, capacitor leads, cooling and electrical isolation.
4. Calculate and verify the new bridge/shaft/frame/mount load paths, retention and
   board/adapter response using the candidate's actual load histories.
5. Update costs and validation/FMEA evidence, then perform the original eight-item
   completion audit. Detailed compact integration and the final assessment remain
   incomplete; the active goal must not be marked complete.
