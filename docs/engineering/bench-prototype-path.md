# Path to a bench prototype

Draft, 2026-11-04. **A plan for getting to measured evidence, not a build guide.** It follows the
[validation plan](validation-plan.md) and DESIGN.md Gate D: physical high-force work needs a qualified
independent mechanical/electrical/safety review first, and no stage here involves a person on the cable.
Force, current and abort limits for each stage are for the reviewer to set, not this document.

## Why build now

On paper the design is close. With the Kollmorgen TBM2G-11526D at 6:1, the full R4 suite fails 5 of 54 cases
([r4m candidate](../../reports/r4m_candidate.md), [motor study](../../reports/motor_study.md)). The inputs
that decide the remaining margins are estimates that more simulation cannot settle:

| Estimate the result depends on | Current value | Why it matters |
|---|---|---|
| Motor winding-to-housing heat path | 0.28 K/W (RO100 guess) | Endurance: 74 °C at 0.28, 105 °C at 0.7; derate starts at 120 °C |
| Drive current-limit convention | ODrive 80 A taken as phase amplitude | Heavy sets at 6:1 need about 56 A DC-equivalent of the 69.3 A allowed |
| Aged-bank capacitance and ESR | Datasheet end-of-life corners | Aged fast reversal bottoms 0.9 V above the 30 V trip |
| Supply overload and constant-current mode | Unverified EPP-500-54 behaviour | Start-up (direct charging) and bus sag |
| Friction, inertia, cogging | Placeholders | Low-force tracking and fast reversal |

## Before ordering (desk work, about 1–2 weeks)

1. **Owner decisions:** accept the TBM2G cost (about CHF 1,094 per motor, two per machine), and accept that
   the open items above will be resolved by measurement rather than more studies.
2. **CAD fit check:** TBM2G (about 128 mm OD housed, 44 mm long) and 6:1 pulleys in the R2 package; rerun
   inertia, belt, bearing and support screens. This can rule the motor out, so it comes before buying.
3. **Kollmorgen request:** a Hall-sensor D-winding part number, quote and lead time (about 9 weeks at the
   distributor), and the winding-to-housing thermal data.
4. **Engage a reviewer** for Stages 1–2 (electrical) now; mechanical/containment review is needed before Stage 3.

## Stages

Each stage replaces specific model estimates with measurements and has a clear way to fail.

| Stage | Hardware | Measures (validation-plan IDs) | Kills or changes the design if |
|---|---|---|---|
| **1. Motor and drive** (no rope, no bank) | One TBM2G in a representative aluminium carrier, ODrive Pro, encoder, lab supply, torque-arm load cell | Kt/Ke and current convention (V-01, V-04); winding-to-housing-to-mount heat path under a heavy-set duty (V-03); cogging and friction (V-02) | Heat path much above 0.7 K/W (endurance fails again); usable torque at the drive limit below about 9 N·m |
| **2. Power path** (no rope) | Add EPP-500-54, Regen Clamp, 20-cell bank with fuse/disconnect/discharge and balancing; motor driven back-to-back against a load machine | Supply overload/CC mode (V-05); bank capacitance, ESR, ripple heating, pre-charge and discharge (V-06); bus sag on the fast-reversal profile | Bus sag or bank ESR worse than the aged corner (fast reversal trips); cell heating above rating at the measured ripple |
| **3. Drum and rope** (after Gate D review) | Add drum, 6:1 belt, rope and force sensing; rope anchored to a fixed load cell in a containment fixture, reviewer-set force ceiling | Closed-loop force tracking against the model trajectory; rope stiffness/damping and drum inertia (V-02, V-07 start); fault-stop timing (V-10) | Tracking or stop timing outside the model's bounds by more than measurement uncertainty |

After each stage, fit the measured parameters into the model, rerun the full R4/r4m suite and record what changed.
A second unit, the bar and paired operation (V-11) come after Stage 3.

## Rough parts cost (one unit)

Repo planning allowances (USD, unquoted, [preliminary costs](../../reports/preliminary_costs.md)) plus the one
sourced motor price. Instrumentation, lab supply, load machine, containment fixture and reviewer fees are not included.

| Stage | Adds | Parts |
|---|---|---|
| 1 | TBM2G; inverter; encoder; rotor carrier, bearings, stator mount | CHF 1,094 + $255–$600 |
| 2 | Supply; bank; Regen Clamp and fuse; bank disconnect/discharge; balancing | $295–$820 |
| 3 | Drum bearings and shaft; belt and pulleys; rope and terminations; force sensing | $280–$970 |

Total parts for one unit through Stage 3: CHF 1,094 + roughly $830–$2,390. Lead time is set by the motor (about 9 weeks).

## Not covered

Enclosure, guide/traverse, mounts and board, the second unit, human-interaction testing (needs a separate
verification and compliance plan), and any claim that these stages make the machine safe to use.
