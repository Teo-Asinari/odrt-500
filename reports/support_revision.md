# Roller-bearing and two-ended-shaft revision screen

Fingerprint: `0e60fb50a834460674564a0b53b9d92379748851fd2d4c3f452556f04eee43fb`

**REVISE: comparison only, not a selected complete design.** The proposed 24/120-tooth stage is 5:1. Motor supports use opposed NJ 202 ECP roller bearings; the drum uses NU205EM floating and NUP205EM locating types on a 25 mm shaft supported at both ends. The side-exit rope force is +Y, and both torque directions are checked.

Load corners: 3000 N rope force and 18 Nm motor torque. Belt tension difference: 1570.8 N. Outer wheel envelope: 116.59 mm. These exceed R1 observed maxima; [r2_candidate.md](r2_candidate.md) repeats the screen at the simulated R2 loads.

| Preload N/span | Rope z mm | Torque sign | Motor C0/P | Drum C0/P | Motor shaft MPa | Drum shaft MPa | Failed screens |
|---:|---:|---:|---:|---:|---:|---:|---|
| 700 | 28.5 | -1 | 2.75 | 5.40 | 85.3 | 29.8 | nonpositive nominal slack tension |
| 700 | 28.5 | 1 | 2.75 | 7.51 | 85.3 | 32.4 | nonpositive nominal slack tension |
| 700 | 53.5 | -1 | 2.75 | 6.66 | 85.3 | 29.0 | nonpositive nominal slack tension |
| 700 | 53.5 | 1 | 2.75 | 4.38 | 85.3 | 34.1 | nonpositive nominal slack tension |
| 850 | 28.5 | -1 | 2.57 | 5.34 | 89.4 | 29.9 | none in these comparisons |
| 850 | 28.5 | 1 | 2.57 | 7.35 | 89.4 | 32.4 | none in these comparisons |
| 850 | 53.5 | -1 | 2.57 | 6.33 | 89.4 | 29.1 | none in these comparisons |
| 850 | 53.5 | 1 | 2.57 | 4.28 | 89.4 | 34.2 | none in these comparisons |
| 1000 | 28.5 | -1 | 2.23 | 5.20 | 99.6 | 29.9 | none in these comparisons |
| 1000 | 28.5 | 1 | 2.23 | 6.63 | 99.6 | 32.4 | none in these comparisons |
| 1000 | 53.5 | -1 | 2.23 | 5.66 | 99.6 | 29.4 | none in these comparisons |
| 1000 | 53.5 | 1 | 2.23 | 4.06 | 99.6 | 34.4 | none in these comparisons |
| 1150 | 28.5 | -1 | 1.96 | 5.05 | 110.2 | 30.0 | motor bearing static factor |
| 1150 | 28.5 | 1 | 1.96 | 5.77 | 110.2 | 32.5 | motor bearing static factor |
| 1150 | 53.5 | -1 | 1.96 | 5.10 | 110.2 | 29.7 | motor bearing static factor |
| 1150 | 53.5 | 1 | 1.96 | 3.83 | 110.2 | 34.7 | motor bearing static factor |

## Primary sources

- [SKF NJ 202 ECP](https://cdn.skfmediahub.skf.com/api/public/0901d196802809de/pdf_preview_medium/0901d196802809de_pdf_preview_medium.pdf), accessed 2026-11-02.
- [NSK NU205EM](https://www.nsk.com/engineering/products/bearings/roller-bearings/cylindrical-roller-bearings/single-row-cylindrical-roller-bearings/nu205em-crb-sr.html), accessed 2026-11-02.
- [NSK NUP205EM](https://www.nsk.com/au-en/engineering/nup205em-crb-sr.html), accessed 2026-11-02.
- [Eaton TV1860-3R0107-R](https://www.eaton.com/us/en-us/skuPage.TV1860-3R0107-R.html), accessed 2026-11-02.

The 20-cell TV-series proposal has 3 V-rated cells with 11 mΩ initial maximum ESR, in the same 18.5 × 60.5 mm maximum body claim. At 52 V, matched cell voltage is 2.6 V and pack rating is 60 V. Individual-cell balance/protection and thermal capacity still need engineering; the 20 J/K thermal capacity is explicitly assumed, not a vendor specification.

## Remaining work

- Ideal radial supports; deck/base/sidewall stiffness and joints are not verified.
- Shaft shoulders, fit stress, axial load, cage/lubrication/minimum load, sealing and fatigue remain open.
- 24/120 pulleys are proposed custom envelopes; no rated belt/teeth/hub design is established.
- The R2 CAD and simulated R2 loads are in r2_package.md and r2_candidate.md; controller calibration is unchanged.

Frame reactions are recorded in JSON. They must be applied to the actual deck/sidewalls/base and fasteners; the old slender posts cannot simply be assumed rigid. No frame or mount qualification is established by improved bearing/shaft numbers.

Reproduce: `.venv/bin/python -m odrt.support_revision`.
