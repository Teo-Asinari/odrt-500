# Data request: CubeMars RO100 (KV55, Lite)

Draft, 2026-11-02. Supersedes the short CubeMars request at the end of [frameless-motor-rfq.md](frameless-motor-rfq.md).
**Not sent.** Fill in the bracketed fields and send from the owner's account. Nothing confidential is included;
the project is open-source (MIT) but the repository is currently private, so the email does not link to it.

Why this matters: endurance in the [R3 review](../engineering/r3-review.md) is limited by the motor's own
winding-to-housing path, and the motor constant (A-022) and thermal model (A-015) are rated low confidence.
Our current values: Kt 0.2 N·m/A and 0.143 Ω phase-to-phase from the
[RO100-LITE-KV55 datasheet](https://img.cubemars.com/products/cubemars-product-parameter/RO100-LITE-KV55.pdf),
giving Km 0.53 N·m/√W. A comparable 105 mm frameless motor (Tecnotion QTR-A-105-34) has about 0.34. If the
RO100 is nearer 0.34, copper loss is about 2.4× our estimate and the single-motor unit fails thermally.
The thermal network (winding→housing 0.28 K/W, housing→air 1.12 K/W) is backed out from the 4 N·m rated torque
and calibrated to the Tecnotion part, not to RO100 data. Questions 1–4 settle this; 5–8 settle speed and integration.

---

**To:** [CubeMars sales / technical support address from cubemars.com]
**Subject:** RO100 KV55 Lite: motor constant, thermal and speed data for a 48 V conduction-cooled application

Hello,

We are designing an open-source, digitally controlled cable resistance trainer and are evaluating the
RO100 KV55 Lite as the drive motor. It drives a cable drum through a 5:1 belt on a 52 V DC bus (30–57 V
operating range) with field-oriented control. The datasheet values are a good start; to size the design
we need a few more details, and we would value your view on whether the RO100 suits the duty below.

**Operating points (per motor):**

| Item | Value |
|---|---|
| Typical working torque | 8–9 N·m during ~25 s sets, 1–3 min rest between sets |
| Peak torque | ~10 N·m (drive current limit 50 A), occasionally up to ~12 N·m for < 1 s |
| Longest session | ~14 min of repeated 4.5 s cycles at 8–9 N·m with 0.5 s pauses |
| Maximum speed | ~2,400 rpm in short bursts (about 800 Hz electrical with 21 pole pairs) |
| Cooling | Stator/carrier bolted to a 2 mm aluminium base and enclosure (conduction), plus ~25 CFM internal airflow; ambient up to 40 °C |

**Questions:**

1. **Torque constant and resistance.** Please confirm Kt = 0.2 N·m/A and the phase resistance of 0.143 Ω,
   with their conventions: Kt per rms or peak phase current (or per DC/q-axis current), and resistance
   phase-to-phase or phase-to-neutral, at what temperature. Is the motor constant Km (N·m/√W) available?
   Are these values the same for the Standard and Lite variants?
2. **Thermal data.** Thermal resistance from winding to the motor's mounting face or housing, the thermal
   time constant of the winding, and the heat capacity or mass split between stator and rotor if known.
3. **Ratings and their conditions.** The test conditions behind the 4 N·m continuous and 12 N·m peak
   ratings: mounting (heat sink size or free air), airflow, ambient, winding temperature reached, and peak
   duration. Is there a continuous-torque figure for a conduction-cooled (heat-sunk) mount?
4. **Temperature limits and sensing.** Insulation class and maximum winding temperature; whether a winding
   temperature sensor is fitted or can be (type: NTC, PTC, KTY), and its location.
5. **Speed and losses.** Maximum permitted mechanical speed and electrical frequency, any guidance on
   driving at ~800 Hz electrical, and a no-load loss (iron + friction) versus speed curve or values.
6. **Torque–speed and efficiency.** A torque–speed curve or efficiency map at 48–52 V if available.
7. **Heat path.** Which face of the motor is intended as the thermal and mechanical mounting interface, its
   flat contact area, and whether the stator is potted or bonded to that face. Is a potted or
   higher-fill winding option available for better winding-to-housing heat transfer?
8. **Mechanical.** Rotor inertia (datasheet: 0.000529 kg·m²) and mass confirmed; the recommended interface
   for an output shaft or adapter on the rotor, with allowable radial and axial loads if the motor's own
   bearings carry any load.

**Commercial:** price and lead time for 2 prototype units, indicative pricing at 100 and 1,000 units per
year, and whether custom windings (for example a different KV for a 52 V bus) are offered.

If a measured test report or 3D model is available, that would be very helpful.

Thank you,
[Name]
[Project name / website]
[Email]

---

## What each answer changes in the repo

| Answer | Where it goes | Effect |
|---|---|---|
| Kt / R conventions, Km | `data/engineering_components.yaml` (`ro100_lite`), A-022 | Copper loss everywhere; low-Km sensitivity becomes nominal or is retired |
| Winding-to-mount resistance, time constant | `configs/coupled.yaml` thermal, A-015 | Endurance and slow-pull winding temperatures; whether R3's heat path is enough |
| Rating conditions, conduction-cooled continuous torque | A-015, `reports/thermal.md` | Cross-check for the backed-out thermal network |
| Max electrical frequency | drive/motor screens (`recommended_electrical_frequency_hz`) | Replaces the provisional 700 Hz screen that fast reversal and full stroke fail |
| No-load losses | coupled plant (not modelled today) | Adds speed-dependent heat at 2,400 rpm |
| Potted/higher-fill option | custom-motor study, endurance options | A cheaper route than a custom motor if the RO100 alone is short |
| Price, lead time | `data/preliminary_costs.yaml` | Replaces the unquoted motor allowance |
