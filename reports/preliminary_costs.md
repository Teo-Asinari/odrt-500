# Complete-function preliminary cost allowances

Fingerprint: `7f3323668486c49f3e4123031641dc85d11abca43f81b4302931accf0fc01916`

**Planning estimates, not supplier quotes.** Analyst planning ranges, 2026-11-02, R4 power path revised 2026-11-03; no supplier volume discounts verified. Custom parts depend on unresolved geometry and process.

These allowances include every function in the preliminary electrical definition, plus mechanics, cable routing, arrestor, harness, retention, assembly, calibration, test, board and adapters. They supersede the historical priced-floor interpretation for planning, but are not a validated BOM for a compact machine. No volume quotation has been obtained. All costs are USD.

| Line / scope | Prototype parts | 100-unit parts | 1000-unit parts |
|---|---:|---:|---:|
| Motor set excluding separate rotor support / unit | $160–$220 | $140–$200 | $110–$180 |
| Inverter with chopper; exact revision unselected / unit | $150–$250 | $120–$220 | $90–$180 |
| Internal mains supply / unit | $80–$150 | $65–$120 | $50–$100 |
| Complete 20-cell TV bank on the drive bus (R4); cell price not yet sourced / unit | $100–$350 | $75–$280 | $55–$220 |
| Mains inlet cord and strain relief / unit | $12–$30 | $8–$22 | $6–$18 |
| Fuse two-pole switch and filter/surge network / unit | $20–$60 | $12–$45 | $8–$30 |
| Regen Clamp (ideal diode and brake chopper) and source branch fuse; clamp price not sourced / unit | $40–$100 | $30–$80 | $22–$60 |
| Time-delay bank fuse with back-to-back MOSFET disconnect and pulse pre-charge/discharge resistor with switches and feedback / unit | $45–$130 | $32–$100 | $22–$75 |
| Passive cell balancing with per-cell voltage monitor and bank temperature sensing / unit | $35–$100 | $20–$70 | $12–$50 |
| DC-link capacitors and bleed / unit | $12–$35 | $8–$25 | $5–$18 |
| Fused auxiliary converters and rails / unit | $15–$45 | $10–$30 | $6–$22 |
| Pulse resistor cutoff mounting temperature and current-shunt sensing / unit | $30–$95 | $22–$72 | $15–$50 |
| Interlocked phase transfer hardware and feedback / unit | $40–$140 | $30–$110 | $20–$80 |
| Passive braking network and thermal sensing / unit | $20–$65 | $12–$45 | $8–$30 |
| Encoder coupling and mounting / unit | $25–$100 | $18–$70 | $12–$50 |
| Force bridge ADC and plausibility channel / unit | $50–$180 | $35–$130 | $25–$90 |
| Application controller PCB and local UI / unit | $40–$140 | $25–$90 | $15–$60 |
| Independent supervisory hardware / unit | $30–$100 | $18–$70 | $12–$50 |
| Local stop actuator and contacts / unit | $15–$50 | $10–$35 | $7–$25 |
| Mount retention and board-mode sensing / unit | $10–$35 | $6–$25 | $4–$18 |
| Isolated peer interface connector and cable allowance / unit | $20–$65 | $12–$45 | $8–$30 |
| Fan ducts thermal interface and airflow feedback / unit | $25–$90 | $18–$65 | $12–$45 |
| Enclosure base lid seals vents and earth bonds / unit | $150–$500 | $70–$220 | $35–$120 |
| Rotor carrier bearings shaft and stator mount / unit | $80–$250 | $40–$140 | $20–$80 |
| Belt pulleys hubs tensioning and guards / unit | $90–$300 | $45–$160 | $25–$90 |
| Drum bearings dead shaft and flange assembly / unit | $100–$350 | $50–$180 | $25–$100 |
| Guide actuator drive feedback traverse mechanism sheaves and exit assembly / unit | $100–$350 | $50–$180 | $25–$100 |
| Rope qualified terminations handle and end fitting / unit | $40–$140 | $25–$90 | $18–$65 |
| Mechanical travel/release energy management allowance; design unresolved / unit | $60–$250 | $30–$150 | $20–$100 |
| Internal wiring connectors shielding insulation clips and fasteners / unit | $50–$180 | $30–$110 | $20–$70 |
| Structural mounting interface and independent retention / unit | $60–$220 | $30–$120 | $18–$70 |
| Unit packaging labels and documentation / unit | $15–$50 | $10–$35 | $7–$25 |
| Common board stiffeners feet two latches retention and bar accessory / board | $250–$800 | $130–$450 | $80–$280 |
| One wall adapter with retention; substrate-specific installation excluded / wall | $80–$280 | $40–$150 | $25–$90 |
| One rack adapter clamps pads and retention / rack | $100–$350 | $50–$180 | $30–$110 |
| One door adapter allowance; no high-force capability established / door | $80–$300 | $40–$160 | $25–$100 |

## System totals

| Procurement volume (units) | One unit factory | Two units + board factory | Unit retail before NRE | Pair + board retail before NRE |
|---|---:|---:|---:|---:|
| prototype | $2,392–$11,313 | $5,153–$24,660 | $4,349–$75,420 | $9,370–$164,398 |
| 100 | $1,440–$6,569 | $3,071–$14,234 | $2,619–$43,790 | $5,585–$94,889 |
| 1000 | $932–$4,292 | $1,978–$9,283 | $1,696–$28,611 | $3,597–$61,882 |

A paired system has two units and one board, or two separate mounting adapters. Adapter alternatives are not all charged together. The JSON includes bare pairs and wall/rack/door pairs. The door allowance does not establish door compatibility or load capability.

Factory cost = (parts + assembly/calibration/test labor) / yield × (1 + factory overhead) × (1 + warranty allowance). Retail = factory cost / (1 − distribution share − gross-margin share). Assembly labor is [[10, 25], [4, 10], [2, 5]] hours by volume; labor rate $35–$80/hour. Yield is 90–98%, factory overhead 10–30%, warranty 3–10%, distribution 15–35% of retail and gross margin 30–50% of retail. Bounds combine favorable or adverse assumptions; they are not statistical confidence limits.

## Development and uncertainty

NRE allowance: $160,000–$1,400,000. Unquoted allowance for engineering tooling fixtures EMC/electrical/mechanical qualification and documentation. Not an approved budget; commercial-scale engineering scope remains uncertain. Procurement volumes count modules, not pairs; NRE amortization therefore divides by modules. Prototype amortization assigns the whole development allowance to one unit and is not its marginal build cost.

| Volume | NRE per unit | Unit retail with NRE amortization |
|---|---:|---:|
| prototype | $160,000–$1,400,000 | $295,258–$9,408,753 |
| 100 | $1,600–$14,000 | $5,528–$137,124 |
| 1000 | $160–$1,400 | $1,987–$37,944 |

Listing context only: [CubeMars RO100 listing](https://store.cubemars.com/products/ro100) showed $156.90 and sold-out text on 2026-11-02; exact variant and stock remain unconfirmed. No quote from that page is counted in these totals.

Excluded: Taxes freight import duties site installation subscriptions financing recall liability and jurisdiction-specific certification scope beyond the NRE allowance. Any missing required function requires a new line; no blank price is counted as zero.

**Assessment: REVISE.** A $500 retail unit is unsupported. Replacing the planning ranges with part-specific quotes, production drawings, supplier process feedback and measured assembly/test time is required before a commercial feasibility decision. Geometry, fault-response circuitry and thermal redesign can move these ranges materially.

Reproduce: `.venv/bin/python -m odrt.preliminary_costs`.
