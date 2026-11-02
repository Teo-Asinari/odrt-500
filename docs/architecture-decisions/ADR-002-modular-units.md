# ADR-002: Two modular units on a common board (2026-11-02)

Decided by the project owner. Supersedes the single-unit floor platform in ADR-001 (mounting and force split only). The seconds-per-rep duty and the supercapacitor buffer still apply.

| Question | Decision | Consequence |
|---|---|---|
| Form factor | Two identical, compact, self-contained cable units, Voltra-like, that mount to the sides of a common board (Vitruvian-like modularity). Black, minimalist, metallic look. | The mechanism, electronics and cable exit all live in one small unit. The board becomes an accessory. |
| Force | 250 lbf per unit, 500 lbf combined when both pull one bar | Unit-level scenarios use per-unit tension (half of the combined value). Copper loss per unit is ~1/4 of the 500 lbf single-unit design. |
| Power | Mains, one cable per unit, each with its own supply and buffer | Smaller supply per unit. Battery operation stays a non-goal. |
| Mounting | Each unit works standalone: board, wall, rack or door anchor, through one universal mounting interface | New load cases for the interface and each mount. The board must hold both units down through the user's weight. |
