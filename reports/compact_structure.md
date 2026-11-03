# Compact mechanical load-path screen

Fingerprint: `78207b7e168fa05651551436c625c846f5da3c7c92fd885ee81c56220f5bd5c1`

**Assessment: REVISE.** This uses current CAD bearing/support locations and the compact candidate force/current envelope. It does not qualify joints, fatigue, mounts or hardware.

Rope-force corner: 2374.6 N, the maximum of the owner target, documented peak-torque stall screen (2104.6 N) and simulated peak (2374.6 N; compact_nominal/single_fast_full). Motor torque corner: 15.17 Nm, the maximum of catalog peak torque and the simulated current × Kt. These maxima may occur at different times.

Motor bearing centers: [63.99999999999999, 72.0] mm; drum bearings: [51.99999999999999, 70.0] mm; belt height 86.5 mm. Motor spindle diameter 10 mm; drum shaft 25 mm.

[NSK 6000 source](https://www.nsk.com/engineering/products/bearings/ball-bearings/deep-groove-ball-bearings/single-row-deep-groove-ball-bearings/6000-apn.html): dynamic 5050 N, static 1970 N, accessed 2026-11-02. Static rating is a comparison, not an allowable service load or fatigue life. NSK 6005 data and source are in `configs/compact_package.yaml`.

| Preload N/span | Rope z mm | Motor bearing N | Motor C0/P | Drum bearing N | Drum C0/P | Spindle MPa | Drum bridge surrogate MPa | Failed screens |
|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 300 | 48.5 | 4468 | 0.44 | 4205 | 1.39 | 270.1 | 610.2 | nominal belt preload loses slack-side tension, motor spindle equivalent stress, motor bridge beam surrogate, drum bridge beam surrogate, motor bearing static factor, drum bearing static factor |
| 300 | 73.5 | 4468 | 0.44 | 1266 | 4.62 | 270.1 | 247.1 | nominal belt preload loses slack-side tension, motor spindle equivalent stress, motor bridge beam surrogate, drum bridge beam surrogate, motor bearing static factor |
| 700 | 48.5 | 4468 | 0.44 | 4205 | 1.39 | 270.1 | 610.2 | nominal belt preload loses slack-side tension, motor spindle equivalent stress, motor bridge beam surrogate, drum bridge beam surrogate, motor bearing static factor, drum bearing static factor |
| 700 | 73.5 | 4468 | 0.44 | 1266 | 4.62 | 270.1 | 247.1 | nominal belt preload loses slack-side tension, motor spindle equivalent stress, motor bridge beam surrogate, drum bridge beam surrogate, motor bearing static factor |
| 1000 | 48.5 | 5443 | 0.36 | 4545 | 1.29 | 315.6 | 588.4 | motor spindle equivalent stress, motor bridge beam surrogate, drum bridge beam surrogate, motor bearing static factor, drum bearing static factor |
| 1000 | 73.5 | 5443 | 0.36 | 1422 | 4.11 | 315.6 | 225.5 | motor spindle equivalent stress, motor bridge beam surrogate, drum bridge beam surrogate, motor bearing static factor |

## Method and limits

Two-bearing reactions satisfy transverse force and moment equilibrium in two directions. The open belt uses exact tangent directions; tension difference is motor torque / pinion pitch radius. When the proposed preload gives a nonpositive slack side, the screen fails and a nonnegative lower-bound resultant is used for reaction estimates. This does not establish that the belt transmits the modeled torque or survives it. Tooth load, pretension setting, belt compliance and tensioner qualification remain open.

Shaft equivalent stress combines circular-section bending and torsion. The stationary drum dead shaft has no assumed rotor drive torsion. Shaft shoulders, fatigue, fits, keys and bearing axial loads are omitted. Generic stress allowables and the proposed C0/P ≥ 2 comparison are assumptions, not manufacturer approvals.

Full-width beam surrogate under a central couple; each half carries half the applied moment. Two-dimensional plate action joints bosses and local contact require FEA and review. The plate surrogate uses σ = 3M/(b t²). It is an analytical rejection indicator; full plate action can change the result. Structural qualification requires mesh/load convergence, actual bosses/joints, bolt preload and positive retention. A low shaft stress cannot qualify an unsupported bearing or thin bridge.

The compact body still has no engineered mounting bolt group, board attachment or adapter retention geometry. The legacy mount/board results are not reused for this candidate. Cable fatigue, guide contact, drum flanges/shell buckling and emergency arrestor loads remain unqualified. A collision-free model does not resolve any of these requirements.

Next revise the motor bearing span/overhang, spindle and bridge/shaft attachment design; choose a rated belt and pretension; then rerun layout, inertia, dynamics and structural checks.

Reproduce: `.venv/bin/python -m odrt.compact_structure` after the compact candidate study.
