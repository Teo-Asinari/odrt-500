# ADR-001: Iteration 2 targets (2026-11-02)

Decided by the project owner after the first simulation pass (see `reports/STATUS.md`, first iteration).

| Question | Decision | Consequence |
|---|---|---|
| Peak force | Keep 500 lbf from one unit | Cost and inertia must be addressed through drivetrain and electronics |
| How long 500 lbf must last | Seconds per rep (heavy reps at normal tempo, with rests) | Peak torque and short-term heating drive sizing, not continuous torque. `peak_tension_hold_limit` becomes a short-hold case |
| Mounting | Floor platform: the user stands on the unit | Pull loads react through the user's weight on the deck, cable exits upward through the deck, and the anchor hazard (H-10) mostly turns into platform stiffness and tipping checks |
| Energy buffer | Supercapacitors allowed (still no battery operation) | Smaller supply sized near session-mean power. Adds stored-energy hazard H-13 |

Status: accepted. Supersedes the open questions in the first-iteration status report.
