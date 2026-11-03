# Upstream-buffer numerical refinement

Revision fingerprint: `04cd1d8e999ed5a2e2d8664fedcc395da9cd39e0dd54a2476e75d6306257978d`

| Case | Max medium–fine change | Outcome |
|---|---:|---|
| compact_aged__paired_heavy_full | 0.001% | pass |
| compact_nominal__single_fast_full | 0.000% | pass |
| compact_aged__paired_dump_failure_coordinated | 0.008% | pass |

Steps are 2/1/0.5 ms caps with relative tolerances 1e-6/2.5e-7/6.25e-8. The normal/fault comparison criteria are unchanged. Trip modes must agree and medium-to-fine event time changes must be no greater than 0.1 ms.

These are averaged-model checks. Hysteresis ripple, switching delay, output-capacitor allocation, clamp hotspot/OTP and actual installed cooling remain unverified. The 12 selected study cases do not replace the full candidate suite.

Reproduce: `.venv/bin/python -m odrt.verify_revision_power` after the power study.
