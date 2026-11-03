# Coupled reference model interface, revision 0.2

The objective is an open resistance-control foundation, with one compact trainer as the reference hardware candidate. This interface is experimental: equations and conformance evidence are versioned before hardware adapters or user-facing exercise applications.

## Public entry points

- `load_coupled(root, scenarios)` validates selected component roles/required data, SI parameters, thresholds, case names, faults, unit count and command scales. Missing required source data fails explicitly.
- `build_model(config, components, scenario, defaults, stroke, case, **perturbations)` returns the symbolic reference plant and initial state. Its internal CasADi objects are for analytical/conformance checks, not a hardware-control API.
- `simulate(...)` returns `metrics` and `signals`, plus internal verification objects. Every signal is a named one-dimensional NumPy array sharing `t`. Times begin at zero, include the complete requested horizon and known injected event times. A windowed case is labeled separately from a full duty cycle.
- `run_study(root, reports, only=None, verify=False)` writes case traces and a report with source/model fingerprint, solver versions, scope, failures and limitations. Partial-case results use separate filenames. Model/input changes during a run prevent publication under the wrong fingerprint.

Reproduce with `make coupled` or `make coupled-verify`. The latter runs dt/dt÷2/dt÷4 maximum-step and tolerance refinements plus parameter uncertainties. A failed convergence/energy check returns a nonzero CLI status. A successfully analyzed physically rejected design can still produce an execution-success result; read the explicit design-screen outcomes.

## Coordinates, units and ports

- Payout position is metres, positive away from the unit; speed is metres/second. Force is newtons. `command_n` is each unit's requested force, not an assertion that it is achievable.
- Drum angle is radians in the payout direction. `radius_m` is the derivative of payout with respect to angle. Occupied winding layers, dead turns and full stroke determine the angle/payout map.
- Motor torque is N·m and positive when resisting payout. Motor shaft speed is reduction × drum speed. `motor_bus_w` is positive when consuming DC energy and negative during regeneration.
- A paired bar has centre payout and angle in radians. Endpoints are centre ± half-span × sin(angle); forces create both translation and rotation. Paired devices have independent electrical and thermal storage.
- `capacitor_v` is the internal ideal bank voltage. `bus_v` is the distinct drive-side DC-link voltage. Current from bank to bus is `(Vcap − Vbus)/ESR`; its heat is `I² × ESR`. Series/parallel capacitance, ESR, heat capacity and mass use the actual selected cell data.
- Temperatures are °C; differences are kelvins. Thermal capacities are J/K, resistances K/W. Winding resistance changes with temperature and changes copper loss/current limits in the same simulation.

The motor uses a DC-equivalent port `torque = Kt I`, `back EMF = Kt ω`, `R = (Kt/Km)²`. This conserves electromechanical power. Its mapping to published phase amplitude/RMS current and inverter modulation requires calibration and uncertainty treatment; these currents must not be used directly to energize hardware.

## Energy contract

At every output time:

`user work + wall input − room heat = change in total stored energy + numerical residual`.

Total stored energy includes handle/bar translation and rotation, reflected rotor/drum kinetic energy, unilateral cable elastic energy, virtual-stop energy, capacitor bank and DC link, and winding/housing/drive/supply/bank/dump/air heat. Gear, cable damping, friction, braking, ESR and conversion losses go to identified thermal nodes or explicit room heat.

Cable stiffness is `EA/(routing length + payout)` for positive payout. The drum-side force includes the derivative of this length-dependent spring energy; omitting it creates or destroys energy. Gear efficiency is smoothed through zero shaft power with nonnegative dissipated power, avoiding a discontinuous sign-induced chatter at rest.

Conservation establishes bookkeeping consistency, not physical truth. Source data, omitted dynamics and model validity remain separate acceptance questions. The near-zero-voltage motor-port regularization is logged explicitly.

## State and trace naming

Global fields: `bar_position_m`, `bar_speed_m_s`, `bar_angle_rad`, `bar_angular_speed_rad_s`.

Per-unit fields use `unit_0.` and `unit_1.` prefixes. States include drum motion, torque-loop response, PI integral, force/encoder filters, both voltage states, and seven thermal nodes. Observables include tension, command, endpoint position/speed, winding radius, motor/capacitor currents, electrical frequency, power flows, enable/stop flags and voltage controllability.

Revision 0.2 appends `trip_latched`, `trip_time_s` and `trip_reason` to each unit's state. The initial values are 0, −1 s and 0; a trip records 1, its zero-crossing time and a reason code. Codes 1–5 denote undervoltage, overvoltage, winding temperature, drive temperature and cell temperature. A unit already outside a thermal limit at initialization starts latched at time zero. Consumers must use names rather than positional state indices.

`metrics.solver_segments` records the actual backend and any fallback reason. CVODES is the primary solver. Its experimental event-interpolation `CV_ILL_INPUT` failure is retried using SciPy BDF with the same equations, coordinates, quadratures, maximum step and tolerances. Other errors propagate. An analytic exponential-decay/event/quadrature check verifies the fallback independently. Refinement compares event time and mode as well as physical outcomes; a solver fallback is not a physical design pass.

Work traces: `user_work_j`, `wall_input_j`, `ambient_heat_j`, `energy_storage_j`, `energy_residual_j`. All output files are reproducible from the fingerprinted configuration and implementation. There is no physical I/O in this module.

The paired solver integrates unit means/differences, then converts to physical per-unit traces. This is a coordinate change, not an enforced equality: explicit unequal commands, parameters and one-sided faults remain asymmetric. It avoids using independent-state floating-point noise as the initiating disturbance in an otherwise exactly symmetric release.

## Fault and protection semantics

The configured suite includes mains loss with immediate braking or buffer ride-through, stuck force sensing, encoder loss, inverted torque, frozen torque command, lost peer communication, release, emergency stop and dump failure. The frozen-command case captures the actual pre-fault controller request at the event and holds that request; it does not freeze at a nominal torque chosen later.

Local stop acts without a peer. Optional peer reaction follows its own proposed delay. Force/encoder fault detection and communication-loss timing currently use ideal injected-event knowledge with specified latency. They compare response policies; they do not demonstrate a real detector or communication implementation. A hardware/software adapter must never use simulator fault-injection flags as its detector.

Voltage and winding/drive/cell temperature limits use zero-crossing events that latch the affected unit off for the remaining scenario. Recovery never clears the latch. A fresh simulation run initializes the state; no within-scenario reset or hardware restart authorization is implemented. Configured peer stops follow the recorded local trip plus the assumed peer delay. Simultaneous identical trips are applied together to preserve pair symmetry.

The event transition clears controller integral/torque-filter states and records trip metadata. Mechanical, electrical and thermal energy-bearing states remain continuous. Detection at these thresholds is ideal and instantaneous; actual detection, actuator and contact-transfer delays are not validated. Phase resistance braking, virtual stops and thermal thresholds remain proposals. Hardware reset/rearming, independent stopping, winding inductance/switching transients, cable-break energy release and real arrestor contact require further work. A retained limitation is not a safety approval.

## Contributor conformance

Before changing a component or replacing a submodel:

1. Add manufacturer source, access date, exact variant, measurement conventions, rated conditions and unknowns to the component catalog. Preserve missing values rather than inventing ratings.
2. Update configuration/schema and package data if the geometry or required functions change. A component that fits alone does not prove a complete unit fits ADR-003.
3. Run independent analytical port/storage checks and whole-system energy tests. Check unilateral tension and nonnegative losses.
4. Run complete named duty cycles, paired symmetry, explicit asymmetry and local/peer faults. Inspect trace behavior as well as aggregate errors.
5. Refine solver resolution and perturb important uncertain physical parameters. Report failed cases and the supported subset honestly.
6. Update mechanical/electrical definition, costing and validation requirements for affected interfaces. Software conformance alone cannot qualify a component or trainer for human loading.
