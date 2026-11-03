# ADR-003: VOLTRA-sized unit envelope (2026-11-02)

Owner decision during the active engineering goal: “20 liters is a huge volume limit”; “take a look at the dimensions of the beyond power voltra”; “we should aim for that or ideally smaller”.

Beyond Power publishes the VOLTRA I body as **323 × 139 × 100 mm**, which gives a bounding volume of **4.4897 L**. Source: [manufacturer technical specifications](https://www.beyond-power.com/pages/voltra-i-technical-specifications), accessed 2026-11-02.

Use those three dimensions, or smaller, as the **per-unit package target**. A volume-only check cannot establish fit: an orientation must fit all three dimensions. The earlier 20 L analyst placeholder is superseded. Smaller packages are desirable; larger packages must be reported as failing this target, not silently accepted.

The manufacturer's 5.8 kg published mass is a comparison benchmark; the owner has not explicitly adopted a mass limit. The engineering screen will use 5.8 kg provisionally and keep this distinction visible.

The size comparison does not demonstrate equivalent performance. ODRT retains 250 lbf per unit and independent mains operation from ADR-002. Required supply, drive, buffer, controls, structure, cooling and internal cable routing must be included. Board and external mounting adapters are separate accessories. Report cable/connector protrusions and installation clearances separately rather than hiding them.

This decision supersedes only the numeric compactness assumption in A-026. The full engineering goal in `docs/engineering/goal.md` remains unchanged.
