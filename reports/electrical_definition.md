# Preliminary electrical definition

Fingerprint: `655dca75b6c170eddf0d6d1e18c7232ad8decc4b1f1d1f70a045e8f26aaceb3c`

**Functional schematic, not a pin-level or fabrication schematic.** The candidate parts remain from the coupled reference; the compact buffer experiment is separate. Graph edges represent semantic connectivity and bundles, not conductor count or physical routes.

[Open functional schematic](figures/electrical_functional.svg) · [Preliminary harness register](harness_preliminary.csv)

| Function | Candidate / status | Definition |
|---|---|---|
| inlet | unselected | Mains inlet, strain relief and protective earth terminal |
| input_protection | unselected | Mains fuse, two-pole switch and EMI/surge filter |
| supply | epp500_48 | Open-frame isolated AC/DC source; forced-air rating is conditional |
| enclosure | custom; bond joints and continuity unqualified | Bonded conductive chassis, structural base and accessible metal |
| source_block | unselected | Source branch DC fuse and reverse-current blocking stage |
| capacitor | bcap0350_e270_t11 | Series capacitor bank; current reference 22s350F, compact alternative under study |
| bank_protection | unselected; interrupt rating and welded-switch detection unresolved | Bank fuse, precharge path and bidirectional main disconnect |
| balancing | unselected | Per-cell balancing, voltage monitoring and bank temperature sensing |
| bus_storage | unselected | 3mF DC-link capacitance and permanent bleed; ratings/layout unresolved |
| aux_power | unselected; rail voltages and isolation boundaries unresolved | Fused DC/DC logic rails and fan supply |
| drive | odrive_s1 | Motor inverter and braking chopper; exact revision must be selected |
| dump | unselected; model uses 1 ohm, pulse energy and chopper duty unqualified | Braking resistor assembly, thermal cutoff and temperature monitor |
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

All supply, inverter, storage, dump, braking, logic and sensor functions need placement, protection ratings, connectors, wire sizing and thermal review. Every harness row retains TBD for unengineered details; bundles such as phases and cell taps must be expanded into conductors. Selected component labels refer to `data/engineering_components.yaml`, not verified pinouts.

The phase transfer proposes break-before-make braking. It is not implemented or qualified. Its switching delay, contact failure, welded states and interlock must replace the current ideal fault response in simulation. The S1 inhibit input is not claimed to provide certified STO. The supervisor is an independent functional proposal; its power loss, common causes, diagnostics, latching and reset behavior remain unresolved.

A local hardware stop path, bounded peer response, independent sensing plausibility, bank precharge and isolation, cell balance/voltage monitoring, thermal cutoffs, mount state and airflow feedback are explicitly included for subsequent circuit design and costing. Their presence in this graph does not establish effectiveness. The current simulator does not model these circuits or their component failures.

Reproduce: `.venv/bin/python -m odrt.electrical_definition` (requires Graphviz `dot`).
