# Request: CubeMars custom-wound torque motor (RO100 / RI100 class)

Draft, 2026-11-04. **Not sent.** Fill in the bracketed fields and send from the owner's account. The minimum Km
(0.7) comes from the Km sweep in the [motor study](../../reports/motor_study.md): 0.7 is enough for heat, but with the
current bank aged fast reversal needs 0.8, so 0.7 is acceptable only if the bank margin is fixed separately. The repository is
private, so the email does not link to it. This complements, and does not replace, the
[RO100 data request](cubemars-ro100-data-request.md).

Why this request: the [motor study](../../reports/motor_study.md) shows that a motor in the RO100's size
(about 110 mm) works on the R4 plant only if it has, together:

- **a higher motor constant** (Km about 0.8 N·m/√W). An RO100 rewound to Kv 80 keeps Km 0.53 and still runs
  endurance at 127 °C, in derate; the Kollmorgen TBM2G-11526D (Km 0.80) runs it at 74 °C;
- **fewer pole pairs** (12 or fewer). With 21 pole pairs every candidate runs fast reversal at 950–1,130 Hz
  electrical, past our 700 Hz screen; the TBM2G (10 pole pairs) runs it at about 480 Hz;
- **a winding fast enough for 6:1 on 52 V** (Kv about 70–75 rpm/V);
- **low rotor inertia** (the reflected inertia at 6:1 dominates fast reversal).

The TBM2G meets this at about CHF 1,094 per motor, two per machine. The aim is the same performance at a cost
that fits a consumer product. Numbers below are per motor and come from the motor study (variant `tbm_6`).

---

**To:** [CubeMars sales / technical support address from cubemars.com]
**Subject:** Custom-wound frameless torque motor, ~110 mm, 48–52 V: feasibility, data and pricing

Hello,

We are developing an open-source, digitally controlled cable resistance trainer. Each machine uses two motors,
each driving a cable drum through a 6:1 belt on a 52 V DC bus with field-oriented control (ODrive Pro). We are
currently evaluating your RO100 KV55, and our simulations show we need a different winding and magnetic design
in a similar size. Could you tell us whether a standard or custom-wound part from your range can meet the
following, and on what terms?

**Requirements (per motor):**

| Item | Requirement |
|---|---|
| Supply | 52 V DC bus nominal, 30–56 V operating range, FOC drive |
| Envelope | Outer diameter ≤ 115 mm (frameless stator OD, or housed OD if supplied housed); axial length ≤ 45 mm |
| Motor constant Km | ≥ 0.8 N·m/√W at 25 °C (minimum acceptable 0.7) |
| Speed constant | Kv about 70–75 rpm/V; at least 2,900 rpm at light load on a 48 V bus |
| Peak torque | ≥ 9 N·m for 5 s at ≤ 80 A peak phase current |
| Working torque | About 7.5 N·m in sets of about 25 s with 1–3 min rest; occasional 14 min sessions of repeated 4.5 s cycles |
| Pole pairs | 12 or fewer (we run up to about 3,000 rpm; we want to stay under about 700 Hz electrical) |
| Rotor inertia | ≤ 5 × 10⁻⁴ kg·m² |
| Cooling | Stator bonded or potted into an aluminium carrier conducting to the enclosure; ambient up to 40 °C |
| Sensing | Winding temperature sensor (NTC, PTC or KTY); Hall sensors or space for an absolute encoder |
| Insulation | Class F or better |

**Questions:**

1. **Feasibility.** Which standard part comes closest (for example an RO100 or RI100 variant, or a longer
   stack), and what custom options are needed to meet the table: winding, stack length, pole count,
   magnet grade? If the pole count cannot change, what is the lowest pole count you offer at this diameter?
2. **Datasheet values for the proposed design:** Kt and Ke with their conventions (per rms or peak phase
   current; line-line or phase voltage), line-line resistance and inductance at 25 °C, Km, peak and continuous
   torque with their test conditions, rotor inertia and mass.
3. **Thermal data:** winding-to-housing (or winding-to-mounting-face) thermal resistance, winding thermal time
   constant, maximum winding temperature.
4. **Torque–speed curve** at a 48 V and a 52 V DC bus.
5. **Pricing:** 2 prototype units, and indicative prices at 100 and 1,000 units per year; any NRE, tooling or
   minimum order quantity for a custom winding.
6. **Lead time** for prototypes and for production quantities.

We are happy to share more detail on the duty cycle or the mechanical interface.

Best regards,
[Name]
[Project / company, website]
[Email / phone]
