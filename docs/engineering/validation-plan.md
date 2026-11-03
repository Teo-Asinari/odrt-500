# Controlled validation and independent review plan

This document identifies evidence needed to validate the open resistance-control reference. It does not authorize purchase, assembly, energization, high-force prototyping or human loading. The current work remains simulation-only under docs/DESIGN.md Gate D.

The software package can be assessed REVISE or NO-GO while this physical evidence is outstanding. Numerical conservation/convergence and passing tests must not be presented as measured performance or safety certification.

## Review gates

| Gate | Required evidence before advancing | Responsible discipline | Present status |
|---|---|---|---|
| Model review | Equations, sign/unit contracts, energy ledger, full scenarios, faults, numerical refinement and uncertainty results; known exclusions identified | Controls/electromechanical modeling reviewer | Coupled model and reports available; independent review outstanding |
| Component/calibration review | Exact variants and rating conventions; approved measurement plan, instrumentation, uncertainty and controlled test boundaries | Electrical/motor/thermal specialist | Primary-source candidates available; critical measurements outstanding |
| Mechanical containment review | Rope/termination/fatigue evidence, real arrestor/stops, load paths and retention, asymmetric and transient loads, containment | Mechanical/structural specialist | Current geometry and virtual stops are unqualified |
| Electrical/control review | Preliminary schematic/harness, protection, isolation/earthing, energy discharge, fault detection and independent stopping; foreseeable combined faults | Electrical/safety/controls specialists | Detailed reference implementation and hardware review outstanding |
| Controlled hardware validation | Approved equipment-specific procedures, containment, remote operation, emergency response, calibrated records and explicit abort criteria | Independent review team and qualified laboratory | Not authorized by this project |
| Human interaction | Complete verification and applicable compliance plan, reviewed residual risks and independent authorization | Qualified independent safety/compliance reviewers | Not authorized; simulation cannot close this gate |

Applicable standards, required safety functions and compliance jurisdiction must be selected by qualified reviewers. No claim is made that an enable pin is certified STO, that a proposed factor of five is adequate for dynamic/human-interactive duty, or that a named consumer product establishes equivalence.

## Required measurements

| ID | Question / model parameters | Needed instrumentation/evidence | Acceptance and model action |
|---|---|---|---|
| V-01 | Exact motor variant, Kt, Ke, phase/line resistance and inductance, current conventions | Variant/serial photos and documentation; calibrated electrical and torque instrumentation; winding temperature and uncertainty records | Reconcile phase/RMS/amplitude definitions and the virtual DC-equivalent port. Fit parameters with intervals; reject unsupported conversion assumptions |
| V-02 | Rotor/drum inertia, friction, backlash, cogging and torque ripple | Reviewed non-human dynamometer characterization across direction, speed and temperature; repeated trials and identified fixtures | Replace placeholder inertia/friction; verify residual spectra and low-force tracking sensitivity rather than just peak torque |
| V-03 | Winding→housing→mount→air thermal paths | Winding/case/mount/air temperatures, power losses, documented mounting/cooling boundary conditions and time history | Fit RC parameters against held-out duty profiles; quantify sensor bias, thermal delay and model prediction bounds |
| V-04 | Drive current/voltage limits and modulation mapping | Manufacturer confirmation plus reviewed driver characterization; isolated synchronized voltage/current measurements and board temperatures | Establish valid current/voltage/frequency envelope, transient margins and ambient/cooling conditions. Do not translate virtual equivalent current directly to phase commands |
| V-05 | Supply regulation, derating, overload, reverse-current behavior and loss | Exact supply configuration, input conditions, airflow, output waveform, thermal records and manufacturer restrictions | Replace ideal droop/current ceiling; establish reverse-blocking need and real ride-through/overload response. Forced-air ratings cannot be used without matching cooling |
| V-06 | Buffer bank capacitance/ESR/leakage/aging, cell balance and pre-charge/discharge | Exact cell lot/assembly and lifecycle status, cell/bank voltages and temperatures, calibrated current and synchronized power records | Fit RC/ESR vs temperature and state; use tolerance and end-life cases. Qualify balancing/protection separately; no cell overvoltage or short-circuit capability inferred from model |
| V-07 | Rope stiffness, damping, terminations, winding stability and bend fatigue | Supplier application review and qualified fatigue/strength laboratory data for exact rope, splice, drum/sheave geometry, load spectrum, temperature and contamination | Establish rating reductions, lifetime and inspection/retirement criteria. Static breaking strength and D/d alone do not establish service life |
| V-08 | Cable exits, arrestor/end stops and structural transient load paths | Reviewed containment and instrumented structural/contact tests designed by qualified specialists; deformation/force/time records | Replace virtual springs/dampers and validate energy dissipation and peak loads. Extend convergence tests to the measured contact law |
| V-09 | Board, universal interface, adapters and installation substrate | Drawings, tolerances, fastener/joint and material data, directional/asymmetric load cases, retention and fatigue evidence | Verify unit→adapter→board/wall/rack→substrate load path. Door mounting remains unsupported unless its entire path is independently qualified |
| V-10 | Force/encoder/thermal sensing, delays, drift, plausibility and independent stop chain | Calibrated sensor records, synchronized digital traces, real fault injection and documented independence/common-cause analysis | Replace ideal filter/detection/latency assumptions; bound missed/false detections. Simulator injection flags must never become production detectors |
| V-11 | Paired control and peer failure | Initially software/HIL replay with no physical output; later only approved controlled fixture measurements | Exercise one-sided faults, clock skew, stale/out-of-order messages, link loss, restart/rearm and unequal motion. Local stop must not require a healthy peer |
| V-12 | Acoustic behavior, enclosure temperature, access and wear | Calibrated acoustic/thermal measurements and serviceability review under defined boundary conditions | Establish noise metric, touch/maintenance limits and enclosure/airflow requirements through the compliance review; current targets are proposals |

## Validation sequence and abort decisions

1. Review simulations and exact component data before defining any physical procedure. Carry every failed/unqualified criterion into the review record.
2. Validate sensor/time-base and electrical/motor conventions before fitting closed-loop gains or making force claims.
3. Identify submodel parameters with declared uncertainty; reserve independent records for prediction validation. Do not fit and validate on the same trace.
4. Validate component power/thermal behavior and mechanical containment under an independently approved plan before combining energized subsystems.
5. Compare complete trajectories and fault timelines to model predictions, including peak force, force error, motion, bus voltage/current, every thermal node and energy balance. A mean error alone cannot pass transient validation.
6. For every discrepancy, identify whether the cause is measurement uncertainty, a wrong parameter, an omitted physical effect or a model/software defect. Revise the model and rerun the full affected conformance suite.
7. Advance only when the relevant independent reviewers accept the evidence and define the next controlled boundaries. No human-use step is implied by this sequence.

Numerical limits in requirements/engineering.yaml are design/verification proposals unless explicitly owner-defined. Physical safe operating/abort limits must be set by reviewers from actual component capabilities, containment and risk analysis. The current source data, unqualified mounts and virtual stops are insufficient to prescribe physical high-force tests.

## Data, provenance and reproducibility

Use [measurement-record.schema.json](measurement-record.schema.json) for each future measurement record. Store raw synchronized time series, calibration certificates, acquisition software/version, exact fixtures and component variants, ambient/cooling/mounting conditions, uncertainty analysis, reviewer approvals, deviations and hashes. Empty templates are not measured evidence.

Record model version/fingerprint, configuration and solver settings with every prediction. Archive both successful and failed runs. Publish de-identified engineering data only with appropriate authorization; this project currently has no human-subject data.

## Current acceptance position

The coupled solver has numerical verification evidence in reports/coupled.md and reports/coupled.json. It does not close V-01 through V-12. The full compact architecture, connected mechanical/electrical definition, complete preliminary economics and independent review remain necessary. Assessment must stay REVISE/NO-GO for unsupported capability claims.
