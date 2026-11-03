# Compact architecture screen

> Analytical rejection and conditional shortlisting only; simulation-only.

Input hash: `35846e129647a9a5e8a83db06e0eb4c9ef95b347b5b1e27bc151fb441ca738ab`

Owner envelope: **323 × 139 × 100 mm (4.4897 L)** or smaller per unit (ADR-003). All three dimensions must fit under one rigid orientation. The earlier 20 L placeholder is superseded.

Evaluated 6912 combinations; 3552 have enough ideal winding capacity; **0 pass the listed comparison checks**. No candidate is physically qualified. Conservative screens are assumption-dependent rejections, not proofs of physical impossibility.

| Rejection reason | Candidates |
|---|---:|
| 40 A current screen | 1936 |
| conservative speed ceiling | 4608 |
| mechanism-only envelope | 6690 |
| motor peak torque | 1256 |
| reference transient rope strength | 2304 |
| stroke capacity | 3360 |

## Method and limits

- Compare direct drive, legacy side-mounted 5 mm-pitch belt and folded 3 mm-pitch belt arrangements with the same force, stroke and speed requirements. All reductions use the same documented motor candidates. A high-ratio single-stage belt is included and can be rejected on dimensions; no imaginary compact gearbox is assumed.
- Layered winding includes dead turns and only occupied layers. Fleet lead uses half drum width / tan(4°). A guided path uses a proposed 90 mm lead; the guide/level-wind must still be designed and qualified.
- Folded geometry is an analyst stack-up proposal. Dimensions are **mechanism-only space claims** including declared bearing/structure/clearance allowances. Electronics, supply, buffer, isolation, cooling and service access still need an actual combined layout. A small mechanism is not a small complete product.
- Speed screen uses the lowest proposed bus voltage and a conservative 78% utilization factor, capped by the vendor rated speed and the S1 recommended electrical frequency. No-load-voltage conventions and loaded curves need validation; passing this comparison screen does not establish a torque-speed operating point.
- Current demand uses published Kt with its stated/uncertain convention. 40 A is the heat-spreader comparison screen; voltage-dependent peak current is not assumed to be 80 A at 48 V.
- Torque, inertia and copper loss use the worst occupied winding radius where relevant. Copper loss is reported both at the published Km and the lower uncertainty case; actual coupled temperature matters.
- The 932 lbf legacy snap result is a conservative reference load, not a prediction for every candidate. It must be replaced by each candidate’s converged transient result. A factor of five on spliced strength is only the retained comparison screen; it does not qualify shock/human-interactive duty.
- D/d, elastic energy and rotor kinetic energy are reported; no bend-fatigue lifetime is claimed. The energy-to-handle-speed value is a worst-case energy-transfer illustration, not a transient simulation.

## Best dimensional screens

Ranked among sufficient-capacity candidates by fewest failed comparison checks, then mechanism volume. Every row still lacks full electronics packaging and physical qualification.

| Motor / rope | Layout / routing | G | Core / turns / layers | Mechanism mm | L | Effective kg | Torque Nm | A | RPM need / ceiling | Failed comparison checks |
|---|---|---:|---|---|---:|---:|---:|---:|---|---|
| ro100_lite / dynaone_hs_5 | folded_3m / guided | 6 | 15 / 6 / 3 | 307 × 124 × 99 | 3.78 | 63.2 | 5.4 | 27 | 3110 / 1658 | conservative speed ceiling |
| ro100_lite / dynaone_hs_5 | folded_3m / guided | 4 | 20 / 6 / 3 | 314 × 124 × 99 | 3.87 | 17.3 | 9.5 | 48 | 1613 / 1658 | 40 A current screen |
| ro100_lite / dynaone_hs_5 | folded_3m / guided | 6 | 20 / 6 / 3 | 314 × 124 × 99 | 3.87 | 38.2 | 6.3 | 32 | 2419 / 1658 | conservative speed ceiling |
| ro100_standard / dynaone_hs_5 | folded_3m / guided | 6 | 15 / 6 / 3 | 312 × 130 × 99 | 4.01 | 103.2 | 5.4 | 27 | 3110 / 1658 | conservative speed ceiling |
| ro100_standard / dynaone_hs_5 | folded_3m / guided | 4 | 20 / 6 / 3 | 320 × 130 × 99 | 4.10 | 28.1 | 9.5 | 48 | 1613 / 1658 | 40 A current screen |
| ro100_standard / dynaone_hs_5 | folded_3m / guided | 6 | 20 / 6 / 3 | 320 × 130 × 99 | 4.10 | 62.5 | 6.3 | 32 | 2419 / 1658 | conservative speed ceiling |
| ro100_lite / dynaone_hs_5 | folded_3m / guided | 4 | 20 / 18 / 1 | 294 × 124 × 159 | 5.82 | 17.3 | 6.6 | 33 | 1613 / 1658 | mechanism-only envelope |
| ro100_lite / dynaone_hs_5 | folded_3m / guided | 4 | 20 / 18 / 2 | 294 × 124 × 159 | 5.82 | 17.3 | 6.6 | 33 | 1613 / 1658 | mechanism-only envelope |
| ro100_lite / dynaone_hs_5 | folded_3m / guided | 4 | 20 / 18 / 3 | 294 × 124 × 159 | 5.82 | 17.3 | 6.6 | 33 | 1613 / 1658 | mechanism-only envelope |
| ro100_standard / dynaone_hs_5 | folded_3m / guided | 4 | 20 / 18 / 1 | 300 × 130 × 159 | 6.17 | 28.1 | 6.6 | 33 | 1613 / 1658 | mechanism-only envelope |
| ro100_standard / dynaone_hs_5 | folded_3m / guided | 4 | 20 / 18 / 2 | 300 × 130 × 159 | 6.17 | 28.1 | 6.6 | 33 | 1613 / 1658 | mechanism-only envelope |
| ro100_standard / dynaone_hs_5 | folded_3m / guided | 4 | 20 / 18 / 3 | 300 × 130 × 159 | 6.17 | 28.1 | 6.6 | 33 | 1613 / 1658 | mechanism-only envelope |
| ro100_lite / dynaone_hs_5 | folded_3m / guided | 6 | 35 / 18 / 1 | 324 × 124 × 159 | 6.41 | 13.8 | 7.3 | 37 | 1451 / 1658 | mechanism-only envelope |
| ro100_lite / dynaone_hs_5 | folded_3m / guided | 6 | 35 / 18 / 2 | 324 × 124 × 159 | 6.41 | 13.8 | 7.3 | 37 | 1451 / 1658 | mechanism-only envelope |
| ro100_lite / dynaone_hs_5 | folded_3m / guided | 6 | 35 / 18 / 3 | 324 × 124 × 159 | 6.41 | 13.8 | 7.3 | 37 | 1451 / 1658 | mechanism-only envelope |
| ro100_lite / dynaone_hs_6 | folded_3m / guided | 4 | 20 / 18 / 1 | 296 × 124 × 177 | 6.52 | 16.6 | 6.7 | 34 | 1578 / 1658 | mechanism-only envelope |
| ro100_lite / dynaone_hs_6 | folded_3m / guided | 4 | 20 / 18 / 2 | 296 × 124 × 177 | 6.52 | 16.6 | 6.7 | 34 | 1578 / 1658 | mechanism-only envelope |
| ro100_lite / dynaone_hs_6 | folded_3m / guided | 4 | 20 / 18 / 3 | 296 × 124 × 177 | 6.52 | 16.6 | 6.7 | 34 | 1578 / 1658 | mechanism-only envelope |
| ro100_standard / dynaone_hs_5 | folded_3m / guided | 6 | 35 / 18 / 1 | 330 × 130 × 159 | 6.78 | 22.5 | 7.3 | 37 | 1451 / 1658 | mechanism-only envelope |
| ro100_standard / dynaone_hs_5 | folded_3m / guided | 6 | 35 / 18 / 2 | 330 × 130 × 159 | 6.78 | 22.5 | 7.3 | 37 | 1451 / 1658 | mechanism-only envelope |

## Decision

**REVISE.** The published VOLTRA envelope is an owner requirement. The existing 104 L package is rejected. Use the machine-readable sweep to identify which torque, speed, winding, routing and package assumptions must change. Do not select a candidate from low volume alone. The next steps are coupled candidate dynamics, real belt/guide/fatigue checks and a complete co-located electrical/mechanical layout.
