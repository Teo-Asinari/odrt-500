# Open Digital Resistance Trainer — Engineering Design Brief

**Status:** Concept / simulation-first research specification  
**Revision:** 0.1 — 2026-11-02  
**Audience:** Codex, Claude Code, mechanical/electrical engineers, reviewers  
**Working name:** ODRT-500

## 1. Mission

Design and evaluate an **open, wall-powered, digitally controlled cable resistance trainer** that aims to provide **up to 500 lbf (2,224 N) of cable tension per unit**, smooth human-interactive resistance, and a **long-run target of $500 USD retail per unit**.

**These are ambitious targets, not demonstrated capabilities.** The system must be developed and assessed in simulation before any hardware prototype. A $500 retail price is substantially harder than a $500 bill of materials (BOM); track both separately. Do not represent a simulation as certification or proof of human-use safety.

Initial objective: create an auditable, executable **digital engineering model** and a sourced, costed concept. Avoid purchase, assembly, or human-load testing until an independent qualified engineer has reviewed the design and a separate controlled hardware-validation plan exists.

## 2. Priorities and non-goals

### Priorities

1. **Safety and controllability**, including safe response to loss of power, loss of sensing, or unexpected user motion.
2. **Smooth, measurable resistance** across both slow and moderately fast repetitions.
3. **Feasibility of 500 lbf peak** and explicitly defined sustained-force envelopes.
4. **Low total product cost** using readily sourced commodity components.
5. **Quiet, apartment-compatible operation**; rigid, independently rated mounting.
6. **Open, reproducible, headless engineering workflow** for autonomous coding agents.
7. **Serviceability**: replaceable cable/wear parts, accessible diagnostics, no mandatory cloud service.

### Non-goals (v0)

- Battery operation, touchscreens, subscriptions, AI coaching, fitness tracking, or mobile apps.
- Full production-ready hardware design or instructions for unreviewed high-force assembly.
- Claiming 500 lbf at every speed, for unlimited time, or under household-outlet power without measurement.
- Human-subject testing, certification claims, or unsupervised operation.
- Custom-designed motor unless off-the-shelf actuator approaches demonstrably fail.

## 3. Requirements and acceptance criteria

| ID | Requirement | Target / acceptance method | Status |
|---|---|---|---|
| R-01 | Peak cable tension | **500 lbf / 2,224 N**, demonstrated in a bounded simulated operating region; duration TBD from thermal model | Hypothesis |
| R-02 | Sustained tension | Derive force-versus-speed-versus-duration envelope; **no unsupported 500 lbf continuous claim** | Required analysis |
| R-03 | Adjustable tension | Proposed nominal working range 5–500 lbf; assess whether fine low-force control is realistic | Stretch |
| R-04 | Dynamic behavior | Evaluate step responses, tracking error, overshoot, oscillation, and reversals across load cases | Simulation metric TBD |
| R-05 | Cable stroke | Parametric target 1.5–2.0 m usable stroke; confirm through use cases and winding geometry | Provisional |
| R-06 | Power | Wall-powered; model AC input, PSU, regeneration/braking/dump load, duty cycle, and circuit limits | Required analysis |
| R-07 | Thermal | Model motor, driver, gearbox, supply, and enclosure temperatures under realistic training duty cycles | Required analysis |
| R-08 | Mechanical integrity | Stress/fatigue checks for cable, terminations, drum, shaft, bearings, mount, enclosure, and fasteners | Independent review required |
| R-09 | Fault handling | Defined fault matrix, fail-safe states, watchdogs, emergency stop concept, and runaway-tension prevention | Independent review required |
| R-10 | Acoustic behavior | Estimate gearbox/motor/fan noise and vibration; bench validation later | Exploratory |
| R-11 | Unit manufacturing BOM | Evaluate supplier-backed cost at prototype, 100-unit, and 1,000-unit volumes | Target TBD |
| R-12 | Retail price | **$500 aspirational**, with explicit margins, freight, taxes/tariffs, assembly, certification, warranty, support, returns, and channel costs | Hypothesis |
| R-13 | Agent reproducibility | Clean environment can regenerate models, run tests, and render reports via CLI | Required |

**Safety invariant:** The design may not assume the controller can always hold or release the load during power loss. Analyze the *actual* fail-state mechanics and energy paths for each architecture. A high-tension emergency release can itself be hazardous.

## 4. Architecture candidates

Evaluate at least three alternatives rather than choosing one by intuition:

| Candidate | Basic concept | Expected upside | Main risks |
|---|---|---|---|
| A — Direct drive | Low-speed high-torque motor directly coupled to cable drum | Smooth, low backlash | Motor/driver mass, cost, thermal demand |
| B — Quasi-direct drive | BLDC/servo with approximately 3:1–10:1 low-backlash reduction | Torque multiplication with potentially good backdrivability | Reflected inertia, friction, gear losses and cost |
| C — Higher reduction | Faster commodity motor with greater gear ratio | Lower required motor torque | Backdrive effort, backlash, noise, dynamic behavior, safety |

Optional alternative: capstan, belt, or alternative drive arrangements. Compare on equal assumptions, especially **output force, cable velocity, low-force smoothness, thermal duty cycle, mechanical backdrivability, and fault behavior**.

## 5. First-principles models

Use SI units internally. Label **lbf (force)** separately from **lb (mass)**.

- Cable force: `F = 500 lbf ≈ 2224 N`.
- Drum torque: `tau_drum = F * r_eff`, where `r_eff` changes with cable winding layer.
- At `r_eff = 0.020 m`, target torque ≈ **44.5 N·m at the drum**.
- Cable mechanical power magnitude: `P = F * v`.
- At **0.1, 0.25, 0.5, 1.0 m/s**, 500 lbf corresponds to approximately **222, 556, 1112, 2224 W** mechanical power magnitude, respectively.
- Geared drive (idealized): `tau_motor ≈ tau_drum / (G * eta)` and `omega_motor ≈ G * v / r_eff` (define efficiency and sign conventions for drive versus regenerative operation).
- Reflected rotor inertia at output approximately scales as `J_motor * G^2` for a simple rigid reduction; include drum, gearbox, and load inertia separately.
- Motor copper losses approximately scale with `I^2 R`; include motor constants, winding temperatures, drive electronics, transient currents, and continuous ratings.
- Track both extension (energy absorbed) and retraction (energy returned to user), including regenerative energy handling when the load drives the motor.

The simulation must address winding-layer variation, cable compliance, friction, backlash (if applicable), motor torque ripple, saturation, thermal derating, and sensor errors; simplifying assumptions must be explicit.

## 6. Proposed repository structure

```text
odrt-500/
├── README.md
├── docs/
│   ├── DESIGN.md                 # This document
│   ├── assumptions.md
│   ├── hazards.md
│   ├── architecture-decisions/
│   └── validation-plan.md
├── requirements/
│   └── requirements.yaml
├── configs/
│   ├── baseline.yaml
│   └── scenarios.yaml
├── models/
│   ├── dynamics/                 # Cable, drum, gearing, actuator, user surrogate
│   ├── electrical/               # Motor, drive, PSU, energy handling
│   ├── thermal/                  # Thermal network and duty cycles
│   ├── structural/               # Loads, interfaces, FEA inputs
│   └── cad/                      # Parametric geometry, STEP exports
├── src/odrt/
│   ├── control/                   # Simulation-only control algorithms
│   ├── optimization/
│   ├── costing/
│   └── reporting/
├── data/
│   ├── components.csv            # Vendor, SKU, rated specs, dated source, quote
│   └── material_properties.csv
├── tests/
├── scripts/
├── reports/                     # Generated plots, trade studies, scorecards
├── pyproject.toml
└── Makefile
```

## 7. Agent-operable tooling

Prefer **text-based, headless, reproducible** interfaces:

- **Python + NumPy/SciPy**: initial physics models, control simulation, thermal estimates, sweeps, optimization, and reporting.
- **CadQuery**: parametric geometry, STEP exports; **FreeCAD** optionally for assembly inspection/CAM exploration.
- **MuJoCo** or a simpler custom multibody model: coupled cable/user-surrogate dynamics after simpler models pass tests.
- **ngspice**: power-electronics or circuit checks as needed.
- **FEMM** (Windows/Lua automation) or **Elmer FEM**: optional electromagnetic work after selecting candidate motors; do not start with bespoke motor design.
- **CalculiX**: structural analysis where appropriate, provided loads, mesh convergence, and boundary conditions are reviewed.

Agent integration policy: all tool invocations must be made through versioned scripts or documented CLI commands; prohibit GUI-click automation in the critical evaluation path. Pin versions, record solver outputs, and fail clearly when optional tools are absent. A programmatic interface is not proof of physical validity.

## 8. Work packages for coding agents

### WP0 — Repository bootstrap and traceability

- Create package, CLI, configs, test harness, CI, and automatic report generation.
- Encode requirements as machine-readable IDs; link every result to assumptions and source data.
- Deliver: `make test`, `make simulate`, `make report` (or equivalent), with reproducible results.

### WP1 — Reference use cases and duty cycles

- Model curls, rows, presses, and slow heavy pulls as abstract one-dimensional cable trajectories, not human-use prescriptions.
- Define cable speed profiles, stroke lengths, acceleration, time under tension, rest periods, and thermal duty cycles.
- Deliver: named scenarios with explicit assumptions and limit cases.

### WP2 — Lumped-parameter electromechanical model

- Build motor/gearbox/drum/cable dynamics including friction, compliance, measured or sourced component limits, regeneration, sensor latency, and thermal derating.
- Simulate tension regulation, speed changes, starts/stops, direction changes, and faults.
- Deliver: plots of force tracking, actual force vs. target, electrical input, stored/dissipated energy, temperatures, and failure transitions.

### WP3 — Architecture and component trade study

- Compare direct drive, quasi-direct, and high-reduction approaches with **the same** performance envelope.
- Use catalog components with dated source URLs and stated price-volume assumptions; never invent verified vendor quotes.
- Deliver: Pareto plots for cost, mass, power, friction, responsiveness, cooling requirement, and risk.

### WP4 — Conceptual CAD and structural models

- Produce a parametric space claim, drum/shaft/bearing layouts, mounting interface, enclosure, and serviceability envelope.
- Model stress and fatigue conservatively; flag cable termination and anchor design for specialist review.
- Deliver: STEP files, exploded assembly views, load-path diagrams, and FEA input decks with mesh-convergence notes.

### WP5 — Safety concept / failure analysis

- Create a hazard log and FMEA/STPA-style review covering stuck-on torque, wrong torque sign, overshoot, encoder failure, overtemperature, cable break, anchor failure, power outage, energy-dissipation failure, controller crash, and user entanglement.
- Distinguish simulation-only protection from independent hardware safety channels.
- Deliver: hazards table with severity, detection, mitigation, residual risk, and validation gaps.
- **No human-loading experiment is authorized by this document.**

### WP6 — Economics and roadmap

- Produce BOM with supplier link, date, MOQ, price tiers, stock uncertainty, substitutions, assembly/test labor, shipping, tariff assumptions, packaging, warranty, certification, retailer margin, and overhead.
- Show $500 **retail** and $500 **manufacturing cost** scenarios separately.
- Deliver: break-even analysis and a candid `GO / REVISE / NO-GO` assessment.

## 9. Required validation cases (simulation phase)

- Zero/low tension stability and fine tension control (especially <20 lbf).
- 500 lbf peak at zero/low speed, with time limit and temperature explicitly stated.
- Force-versus-speed-versus-duration envelope; repeated sets with rest periods.
- Sudden pull, sudden stop, cable reversal, and loss of external load.
- Loss of encoder/load sensor; sensor disagreement; communication timeout.
- Controller reset, power interruption, overvoltage during regenerative operation, and thermal limit.
- Change in effective drum radius as cable winds/unwinds.
- Upper/lower mechanical travel limits and cable routing worst cases.
- Sensitivity analysis for friction, gear efficiency, inertia, motor parameter uncertainty, and supplier tolerances.
- Negative tests: deliberately invalid configurations must fail rather than produce reassuring plots.

For each case: record initial conditions, solver settings, tolerances, numerical convergence, pass/fail criterion, and uncertainty. **Do not invent quantitative safety thresholds**; propose them and flag for review.

## 10. Decision gates

**Gate A — Physics plausibility:** Reproducible analytical calculations and simulation agree within defined tolerances; physically consistent power/energy accounting.

**Gate B — Component reality:** At least one sourced actuator, gearbox (if any), controller, supply, and energy-handling architecture meet a clearly bounded simulated load envelope; identify uncertainties in catalog ratings.

**Gate C — Economics:** Explicit estimated manufacturing and retail cost at stated volumes, including required overhead. If $500 retail fails, report lowest credible retail range instead of manipulating assumptions.

**Gate D — Engineering review:** Qualified independent mechanical/electrical/safety review before any physical high-force prototyping; design verification and compliance plan required before human interaction.

## 11. Instructions to the first coding agent

> You are the lead systems-modeling agent on a simulation-first electromechanical research project. Read `docs/DESIGN.md` in full. Begin with WP0 and WP1, then a transparent analytical baseline for WP2. Do **not** generate a detailed build guide for an unreviewed 500 lbf human-interactive machine. Prefer commodity components and executable models over aesthetic CAD. Treat 500 lbf and $500 retail as hypotheses. Never fabricate prices, torque curves, certifications, or test results. Write unit tests for force/torque/power calculations, model uncertainty explicitly, and cite supplier specifications by URL and access date. Keep all scripts runnable headlessly. Produce a short `reports/STATUS.md` summarizing completed work, assumptions, failed tests, open questions, and the next smallest verifiable milestone.

### First milestone (suggested)

1. Initialize the repository and a repeatable CLI test/report workflow.
2. Implement the basic force–torque–speed–power model with unit-tested SI conversions.
3. Plot a force/speed/duration feasibility envelope for three **clearly labeled illustrative** actuator architectures.
4. Create an uncertainty register and preliminary hazard log.
5. Make no claim of feasibility, safety, or target price without supporting evidence.

## 12. Open engineering questions

- Is **500 lbf peak** valuable, or would two independently controlled 250 lbf units be more practical?
- At what maximum cable speed must the unit produce 500 lbf, and for how long?
- What household power source and electrical jurisdiction are assumed?
- What noise, size, weight, and mounting limits are acceptable?
- Is the product required to provide active cable retraction under load, or mainly resist extension?
- Which additional modes (eccentric overload, isokinetic, adaptive force) are genuinely necessary?
- What objective low-load smoothness metrics correlate with an acceptable exercise feel?
- What independent safety architecture and applicable regulatory/industry standards would qualified reviewers require?

---

**Design philosophy:** Optimize for **honest, verifiable engineering evidence**, not a persuasive render or an impressive peak-force number. When assumptions fail, revise the product targets rather than conceal the failure.
