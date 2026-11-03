# Preliminary electrical definition

Fingerprint: `8c56b4a8e8debc9fac648646e684d49349849e854471aab67a3c3fe22986b93e`

**Functional schematic, not a pin-level or fabrication schematic.** The power path follows the R4 candidate (bank on the drive bus behind the Regen Clamp; [sizing](power_path.md)); other candidate parts remain from the coupled reference. Graph edges represent semantic connectivity and bundles, not conductor count or physical routes.

[Open functional schematic](figures/electrical_functional.svg) · [Preliminary harness register](harness_preliminary.csv)

| Function | Candidate / status | Definition |
|---|---|---|
| inlet | unselected | Mains inlet, strain relief and protective earth terminal |
| input_protection | unselected | Mains fuse, two-pole switch and EMI/surge filter |
| supply | epp500_54 | Open-frame isolated AC/DC source at 52 V (R4); forced-air rating is conditional; overload mode into capacitive load unverified |
| enclosure | custom; bond joints and continuity unqualified | Bonded conductive chassis, structural base and accessible metal |
| source_block | regen_clamp; 58 V rating leaves 1 V above the 57 V trip; fuse unselected | In R4, the ODrive Regen Clamp ideal diode (supply reverse block) and brake chopper, plus source branch DC fuse >= 12 A; sized in reports/power_path.md |
| capacitor | eaton_tv1860_3r0107 x20 | Series capacitor bank on the drive bus (R4), 20 x 100 F 3.0 V cells |
| bank_protection | unselected; fuse I2t at the aged-bank fault multiple and welded-switch detection unresolved | Bank time-delay DC fuse, back-to-back MOSFET disconnect, and one pulse resistor (about 6.8 ohm) switched for pre-charge and service discharge; sized in reports/power_path.md |
| balancing | unselected; cell leakage not verified | Passive per-cell balancing (about 260 ohm), per-cell voltage monitor with 2.95 V trip, bank temperature sensing feeding the torque derate |
| bus_storage | unselected | 3 mF DC-link capacitance plus Regen Clamp onboard capacitance and permanent bleed; ratings/layout unresolved |
| aux_power | unselected; rail voltages and isolation boundaries unresolved | Fused DC/DC logic rails and fan supply |
| drive | odrive_pro | Motor inverter (ODrive Pro in R4); braking is done by the Regen Clamp, not the drive |
| dump | unselected; resistor pulse energy and the clamp brake-rating interpretation unverified | Braking resistor assembly (1 ohm in the model), thermal cutoff, temperature monitor and current shunt for dump-path fault detection |
| phase_transfer | unselected; fail states, timing, arcing and interlock must be engineered | Break-before-make transfer between inverter and passive phase brake |
| motor | ro100_lite | Frameless motor; external rotor support, encoder and winding sensor required |
| phase_brake | unselected | Passive phase-brake resistor network; DC-equivalent simulation is not a circuit rating |
| encoder | unselected | Rotor position sensor; protocol, resolution and mechanical coupling unresolved |
| force_sensor | unselected | Cable-force bridge, overload path and independent plausibility channel |
| controller | unselected | Application controller, force ADC and drive communications |
| supervisor | unselected | Independent watchdog and fault supervisor; no safety integrity level claimed |
| guide_actuator | unselected; screw geometry is a concept and actuator/feedback are not placed | Synchronized cable-guide actuator with position/end-stop monitoring and local inhibit |
| stop | unselected | Local stop actuator and hardware stop path; contacts and reset policy unresolved |
| mount | unselected | Mount retention and board-mode sensing |
| peer | unselected; isolation, protocol and fault latency unresolved | Isolated inter-unit communications and peer-stop transport |
| peer_connector | unselected | External peer connector and shield termination |
| fan | unselected | Fan, ducting and airflow feedback; actual supply airflow must be demonstrated |

## Interfaces and unresolved engineering

Mains and protective earth are explicit. DC return has no intentional chassis bond in this proposal; the final grounding, EMC and isolation plan must settle that choice. Semantic domain validation does not calculate creepage, clearance, dielectric strength or leakage.

All supply, inverter, storage, dump, braking, logic and sensor functions need placement, protection ratings, connectors, wire sizing and thermal review. Every harness row retains TBD for unengineered details; bundles such as phases and cell taps must be expanded into conductors. Selected component labels refer to `data/engineering_components.yaml` and, for the R4 power path, `data/revision_components.yaml` and `data/revision_support.yaml`; they are not verified pinouts.

The phase transfer proposes break-before-make braking. It is not implemented or qualified. Its switching delay, contact failure, welded states and interlock must replace the current ideal fault response in simulation. The drive inhibit input is not claimed to provide certified STO. The supervisor is an independent functional proposal; its power loss, common causes, diagnostics, latching and reset behavior remain unresolved.

A local hardware stop path, bounded peer response, independent sensing plausibility, bank precharge and isolation, cell balance/voltage monitoring, thermal cutoffs, mount state and airflow feedback are explicitly included for subsequent circuit design and costing. Their presence in this graph does not establish effectiveness. The current simulator does not model these circuits or their component failures.

Reproduce: `.venv/bin/python -m odrt.electrical_definition` (requires Graphviz `dot`).
