# Request for quotation: frameless torque motor for a cable resistance trainer

Historical iteration-2 draft, 2026-11-02. **Superseded sizing: do not send as the modular-unit specification.** Recalculate torque, speed, thermal duty and packaging for ADR-002 before requesting quotes. Numbers come from `reports/custom_motor.md`, `reports/components.md` and `reports/thermal.md`. Fill in the bracketed fields before sending.

---

**Subject:** RFQ: 48 V frameless torque motor, ~105-130 mm OD, prototype + volume pricing

Hello,

We are developing an open-source, digitally controlled cable resistance trainer (fitness equipment, currently at the simulation and prototype-planning stage). We are looking for a frameless (or housed) permanent-magnet torque motor and would appreciate a quotation and datasheet for a standard or custom-wound part that meets the following.

**Option A: geared (preferred).** The motor drives a cable drum through a ~6:1 belt reduction.

| Item | Requirement |
|---|---|
| Supply | 48 V DC bus (operating range 40-56 V), FOC drive |
| Envelope | Stator OD 100-135 mm; stack/height ≤ 70 mm |
| Peak torque | ≥ 12 N·m for ~5 s at a time |
| Duty cycle | Sets of ~25 s at ~10.6 N·m, then 1-3 min rest; occasional 3 s holds at that torque |
| Speed | ≥ 2,000 rpm at 10 N·m on the 48 V bus; ≥ 2,800 rpm at light load |
| Motor constant | Km ≥ 0.6 N·m/√W at 25 °C (0.8 preferred) |
| Rotor inertia | ≤ 1 × 10⁻³ kg·m² |
| Insulation / sensing | Class F or better; winding temperature sensor (PTC, KTY or NTC); Hall sensors or space for an encoder |
| Mounting | Stator bonded into an aluminium housing that acts as the heat sink |

**Option B: direct drive (for comparison).** The motor sits directly on the drum shaft.

| Item | Requirement |
|---|---|
| Supply | Same 48 V bus |
| Envelope | Stator OD 160-260 mm; stack ≤ 70 mm |
| Peak torque | ≥ 65 N·m for ~5 s |
| Duty cycle | Sets of ~25 s at ~60 N·m |
| Speed | ≥ 350 rpm at 60 N·m; ≥ 470 rpm at light load |
| Motor constant | Km ≥ 3.5 N·m/√W at 25 °C |

**Please provide:**

1. The closest standard part number(s). If none fits, the custom-winding options and any NRE or tooling cost.
2. Datasheet values: Kt, Ke, phase resistance and inductance (with convention, e.g. phase-to-phase or per phase, rms or peak), Km, peak and continuous torque with their test conditions, thermal resistance (winding to mount) and thermal time constant, maximum winding temperature, mass and rotor inertia.
3. A torque-speed curve at a 48 V DC bus.
4. Prices for 1-2 prototype units, plus indicative pricing at 100 and 1,000 units/year.
5. Lead time and minimum order quantity.

Happy to share more detail on the duty cycle or the mechanical interface.

Best regards,
[Name]
[Project / company, website]
[Email / phone]

---

## Separate short request to CubeMars (current lead motor, RO100 KV55)

**Subject:** RO100 KV55: datasheet values (Kt, resistance, thermal data)

Hello,

We are evaluating the RO100 KV55 (Standard, with Hall) for a 48 V application with short high-torque peaks. Could you confirm the following for the Standard variant? Your product page lists some of them only under the Lite variant.

1. Torque constant Kt (N·m/A) and its convention (rms or peak, phase or line current)
2. Phase resistance, and whether it is phase-to-phase or phase-to-neutral
3. Thermal resistance from winding to mount (or housing), and the thermal time constant
4. Maximum winding temperature / insulation class, and which temperature sensor is fitted
5. The test conditions behind the 4 N·m rated and 12 N·m peak torque (cooling, duration)

Thank you,
[Name]

---

## Candidate suppliers

These have not been checked for fit or for whether they quote small volumes: Tecnotion (QTR/QTL series, the data source for the sizing study), Kollmorgen (TBM/KBM frameless), Allied Motion (HT frameless), CubeMars (RO/RI series) and T-Motor.
