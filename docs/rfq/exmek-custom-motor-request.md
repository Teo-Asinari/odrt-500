# Request: Exmek (Wuxi Junhong) frameless torque motor, ~110 mm, 48–52 V

Draft, 2026-11-04. **Not sent.** Fill in the bracketed fields and send from the owner's account. Same requirements
as the [CubeMars custom-winding request](cubemars-custom-winding-request.md), which gives the reasons for each
one (from the [motor study](../../reports/motor_study.md)); the minimum Km of 0.7 comes from the Km sweep and is acceptable only if the bank margin is fixed separately.
The repository is private, so the email does not link to it.

Starting point: Exmek's [frameless torque motor listings](https://exmekmade.en.made-in-china.com/product-group/boEmIecJgzhC/Frameless-Torque-Motor-1.html) show 48 V robot-joint frameless motors with 6, 10 and 20 N·m continuous ratings and a price range of US$30–260 (accessed 2026-11-04). The listing shown is the larger MF180 with 26 poles, and the price data looks old, so a smaller, lower-pole-count design and current pricing are the main questions.

---

**To:** [Exmek / Wuxi Junhong Automation contact from their made-in-china.com storefront]
**Subject:** Frameless BLDC torque motor, ~110 mm, 48–52 V: custom part, data and pricing

Hello,

We are developing an open-source, digitally controlled cable resistance trainer. Each machine uses two motors, each driving a cable drum through a 6:1 belt on a 52 V DC bus with field-oriented control (ODrive Pro). Your frameless torque motor range includes 48 V robot-joint motors; the listing we found is the larger MF180. Could you tell us whether a part around 110 mm, standard or custom-wound, can meet the following, and on what terms?

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

1. **Feasibility.** Which standard part in your frameless range comes closest, and what custom options are
   needed to meet the table: winding, stack length, pole count, magnet grade? What is the lowest pole count
   you offer at this diameter?
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
