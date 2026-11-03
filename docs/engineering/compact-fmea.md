# Compact candidate failure-mode and review register

This register connects the current compact CAD, functional circuit and coupled
simulation to the validation plan. It is preliminary: occurrence probabilities,
diagnostic coverage and severity rankings have not been validated. No numerical
risk priority score or safety integrity level is claimed.

| ID | Failure / trigger | Consequence | Current evidence / limitation | Required engineering and validation |
|---|---|---|---|---|
| CF-01 | Belt slack, tooth jump, rupture or excess pretension | Loss of force, uncontrolled payout/retraction, bearing overload | Rigid ratio and efficiency in simulation; pitch envelopes in CAD. Structural screen compares preload and reactions; no selected rated belt | Select belt/pulleys and tension setting from vendor design method; model slack/drive loss and torque transfer; review guards, fatigue and independent energy management |
| CF-02 | Motor spindle, bearing seat or rotor carrier failure | Rotor contact, fragments or force loss | CAD-derived carrier inertia is coupled; bearing/spindle loads are analytical surrogates. Rotor attachment, fits, keys and retention are absent | Obtain motor mating geometry; engineer bearing span/overhang, carrier and positive retention; resolve combined radial/axial loads and fatigue; independent mechanical review |
| CF-03 | Drum dead-shaft joint, bridge, post or base failure | Cable-load path separation and loss of force | Proposed load path and CAD exist; beam surrogate is not plate/joint FEA. No complete fastener group | Define shaft boss/clamp, bridge stiffness, joints, preload and secondary retention; verify load/mesh convergence and dynamic load history; inspectability and controlled proof validation plan |
| CF-04 | Cell mismatch, failed balancing, cell overvoltage or short circuit | Capacitor damage, heat, bank fault or loss of support | Bulk bank assumes identical balanced cells. Uniform aging/ESR are simulated; individual-cell voltage and balancing are not | Select per-cell monitoring/balance and protection; analyze tolerance/aging mismatch, precharge, leakage, balancing loss and interruption energy; electrical specialist review and instrumented cell-level validation |
| CF-05 | Source reverse current, precharge bypass or welded disconnect | Supply damage, inrush, hazardous retained energy | Source reverse block is ideal. Circuit has unselected precharge/disconnect functions; actual device failure modes absent | Select fuse/interruption and blocking devices; model stored energy, discharge and welded-state detection; verify actual DC interrupt ratings and independent isolation |
| CF-06 | Dump open/short, cutoff failure or chopper rating mismatch | Bus overvoltage, force interruption, resistor overheating | Dump failure and latched voltage trip are simulated with ideal threshold detection. Chopper hardware revision, duty/pulse energy and wiring inductance unresolved | Select exact drive revision and rated resistor/cutoff; establish current, pulse-energy and duty limits; verify sensing delay, switching overshoot and safe thermal placement |
| CF-07 | Incorrect phase-transfer sequence, stuck contact or braking-network failure | Inverter short, excess torque, free payout or asymmetric stop | Disabled-phase brake is DC-equivalent and instantaneous. No actual transfer circuit/latency is modeled | Engineer break-before-make topology, interlock and failure feedback; include switching delay/contact failures and phase inductance; independently review stored-energy response |
| CF-08 | Force/encoder fault, controller freeze or sign error | Excess/insufficient force or unstable control | Injected named faults and ideal detection delays compare responses. Real detector algorithms, sensor redundancy and calibration are absent | Define sensor placement, overload path, sign checks, diagnostics and tolerances; test bias/noise/dropout/timebase failures with independent truth data; verify supervisor independence |
| CF-09 | Logic rail loss, common-cause software fault or stale peer data | Both safety functions unavailable, delayed/asymmetric stop | Separate supervisor and isolated peer are functional proposals. Shared auxiliary power and reset behavior unengineered | Define power domains, startup/inhibit defaults, independent watchdog and local stopping path; analyze common causes and corrupt/out-of-order communications; do not rely on simulator fault flags as detectors |
| CF-10 | Guide desynchronization, jam, end-stop failure or rope crossover | Local abrasion, cable snap, force spike or loss of travel | Ideal winding radius and unilateral cable; illustrative screw/carriage and swept volume. Guide actuator, feedback and contact curvature unselected | Engineer guide/exit contact and synchronization; model jam/position faults and layer transition; qualify D/d, splices, wear, repeated bending and inspection/replacement criteria |
| CF-11 | Fan stall, blocked inlet, recirculation or hot ambient | Derating, insulation damage, loss of force | Candidate assumes supply-required airflow; no selected fan/duct or installed pressure-flow measurement. Thermal resistances remain proposals | Select fan/duct/filter and airflow diagnostics; derive thermal network from assembly; validate winding, housing, resistor, cell and mains hot spots over duty/ambient extremes and fault shutdown |
| CF-12 | Cable release, break or asymmetric paired fault | Snap/retraction, bar rotation, user imbalance | Unilateral cable and paired release are simulated. Cable-break fracture energy, real contact/arrestor and human response are absent; large angles exceed validated model geometry | Design independent arrestor/energy management and local/peer policies; extend contact/direction/fracture model; define force/motion limits with qualified reviewers and controlled non-human validation |
| CF-13 | Incorrect mount engagement, latch wear, wrong adapter or weak substrate | Unit/board movement or detachment | Common interface intent only. Compact CAD lacks engineered mount/board joints; legacy mounting results do not apply | Complete joints/retention, state sensing and load histories for board/rack/wall adapters; qualify substrates/installation and misuse. No high-force door capability is established |
| CF-14 | Mains/logic separation, earth bonding or harness failure | Electric shock, short circuit, fire or lost sensing | Functional domains and earth net exist, but wire gauges/routes, pinouts, clearances and strain relief remain TBD; 1 mm partition is illustrative | Select actual components and insulation system; engineer PE continuity, creepage/clearance, terminals, fusing, harness segregation and retention; formal electrical safety/EMC review and authorized validation |

The simulator's latched stop has ideal instantaneous voltage/thermal detection
and no within-scenario reset. A hardware restart authorization process, external
stop circuit and independently validated state machine remain required.

Current uncertainty checks vary the plant and, for reflected inertia, its
feedforward estimate together. They do not prove robustness to an independently
wrong controller inertia estimate. Add calibration mismatch, sensor noise/bias,
timing uncertainty and actual detector logic before claiming controller robustness.

Measurements and held-out validation records must follow
[validation-plan.md](validation-plan.md). The existing hardware gates remain in
effect; this document does not authorize building or energizing hardware.

Closure requires a named design revision, linked analysis/measurement evidence,
acceptance criterion and specialist review for each row. An entry is not closed
by a green software test, a drawn functional block or a nonintersecting CAD box.
