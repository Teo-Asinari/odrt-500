# R2 candidate review — 2026-11-02

**Decision: REVISE. The R2 support fixes hold at the simulated loads, but 5:1 trades heat for speed and the aged bank still trips.**

R2 joins the separately screened [support revision](../../reports/support_revision.md) and
[power revision](../../reports/revision_power.md) into one CAD and one simulated machine:

- [R2 CAD](../../reports/r2_package.md): 56 parts inside 323 × 139 × 100 mm, no unintended solid overlaps, rope and guide sweeps clear. 5:1 belt (24/120 × 3 mm), opposed NJ 202 motor bearings in a wall-attached bridge, NU205/NUP205 drum bearings inside the winding core on a 25 mm shaft held by a base boss and a wall-attached deck, +Y rope exit, EPP-500-54 lying flat in the end bay, ODrive Pro + Regen Clamp on the deck. The 20 TV cells are in three groups (4 under the drum, 12 in the end bay, 4 over the motor).
- [R2 candidate](../../reports/r2_candidate.md): all 27 configured cases for fresh and aged TV banks, four 3-resolution studies (all pass, ≤0.002% medium-to-fine), seven paired-heavy uncertainties, then the support screen repeated at simulated loads. No solver failures. Drum-referred inertia 0.016331 kg m² (R1 0.024254).

## What improved

| Evidence | R1 | R2 |
|---|---|---|
| Paired heavy, fresh bank | 0.74% RMS | 0.18% RMS |
| Paired heavy, aged bank | 72% RMS, undervoltage trip | 17% RMS, undervoltage trip (later) |
| Full stroke | 66% RMS | 36% RMS (still fails, travel-stop engagement) |
| Motor bearing C0/P | 0.36–0.44 | 2.23–2.57 at 850–1000 N preload |
| Spindle / drum shaft stress | 270–316 MPa / bridge 226–610 MPa | ≤99 MPa / ≤20 MPa (175 MPa proposed allowable) |

At the simulated envelope (1522 N peak rope force; 88.6 A peak current, which occurs in the inverted-torque fault while phase-braking), the 850 and 1000 N/span preload corners pass every bearing, shaft and slack-side comparison; 700 N loses slack-side tension and 1150 N drops the motor bearing below C0/P 2.

## What got worse or still fails

- **Winding heat.** 5:1 needs 20% more motor torque for the same rope force, so ~44% more copper loss. Heavy set winding 78.5 → 106 °C; slow heavy pull 96 → 128.5 °C, past the 120 °C derate (tracking 0.09 → 3.45%); endurance 132 °C and 40% tracking error. This is the main R2 regression.
- **Aged bank margin.** Aged paired heavy, aged endurance, aged fast reversal and aged buffered power loss all trip undervoltage. Fresh fast reversal now also trips (68% error).
- **Release asymmetry.** 1% imbalanced release still rotates the bar about 48° in both banks.
- **Uncertainties.** Low Km trips (85% error); a +15 °C room fails the drive ambient rating. Halving or quartering airflow changes nothing in the 6 s paired set, so the air-node coupling to the motor is weak in this window — it is not evidence that cooling is adequate for long duty.

## Next action

The two remaining physical problems pull in opposite directions: the ratio wants to go up for heat and down for speed. Candidates for R3, roughly in order of leverage:

1. **Thermal path, not ratio.** The motor's winding-to-housing-to-air path is still a reference proposal. A conducted path from the stator carrier into the base/side walls (as the custom-motor study found, the thermal path matters as much as Km) is the cheapest way to buy back the 5:1 heat.
2. **Bank energy.** The aged bank trips in every hard case. More cells do not fit in the current layout; reclaiming the end-bay space (taller supply orientation, smaller inlet/fan claim) or a higher-voltage cell string are the options.
3. **Fast reversal / full stroke.** These fail at both ratios, so they are a controller/current-limit/voltage problem, not only an inertia one. Retuning gains is permitted only as an explicit, separately reported change.

Not addressed by R2: wiring/bus bars between the three cell groups, trays and standoffs, positive retention, belt tooth rating and tensioner, deck/bridge/side-wall stiffness and joints, mains isolation and the actual airflow path.
