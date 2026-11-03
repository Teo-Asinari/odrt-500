# Component rating review

Input hash: `35846e129647a9a5e8a83db06e0eb4c9ef95b347b5b1e27bc151fb441ca738ab`

Manufacturer-authored sources rechecked 2026-11-02. Exact SKU stock/lead time and fresh quotes are unknown unless explicitly stated. Values are in `data/engineering_components.yaml`.

## Legacy bus incompatibility

- dump_on_v 56 V reaches/exceeds drive maximum 50.5 V
- overvoltage_v 60 V reaches/exceeds drive maximum 50.5 V

S1 maximum DC voltage is 50.5 V. A simulated bus above that rating fails component compatibility even if it stays below the old model’s 60 V threshold. The 78% published modulation utilization and voltage-dependent peak-current curve also constrain the usable envelope.

## Candidates and unresolved selection

| Candidate | Status / unresolved question | Source |
|---|---|---|
| ro100_standard | Manufacturer product listed; variant stock and ship date not verified. Comparison table explicitly includes Standard resistance/torque. Marketing paragraph contradicts it with RO80 values; retain measurement/convention uncertainty. | [manufacturer source](https://www.cubemars.com/product/ro100-kv55-standard-with-hall-frameless-torque-motor.html) |
| ro100_lite | Manufacturer datasheet available; current stock and price unknown. Variant-specific motor candidate; no integrated Hall/temperature sensing assumed. Thermal paths and current conventions need confirmation. | [manufacturer source](https://img.cubemars.com/products/cubemars-product-parameter/RO100-LITE-KV55.pdf) |
| odrive_s1 | Listed; current stock not verified. Peak current is voltage/temperature dependent; 80 A is not a guaranteed limit at 48 V. No certified STO function inferred from enable input. | [manufacturer source](https://docs.odriverobotics.com/v/latest/hardware/s1-datasheet.html) |
| epp500_48 | Manufacturer datasheet available; current stock unknown. Power is subject to input/temperature derating. Open-frame mains module requires enclosure and isolation design; reverse current must be blocked unless vendor approves. | [manufacturer source](https://www.meanwell.com/Upload/PDF/EPP-500/EPP-500-SPEC.PDF) |
| bcap0350_e270_t11 | Historical manufacturer-authored datasheet; lifecycle stock and replacement approval must be checked. Manufacturer datasheet mirrored by distributor; 22-series bank is 15.9 F not 2 F. Cell voltage balance and protection are additional requirements. | [manufacturer source](https://www.mouser.com/datasheet/2/257/Maxwell_BCSeries_DS_1017105-4-1179684.pdf) |
| dynaone_hs_4 | Manufacturer catalog; current supplier stock and price unknown. Spliced strength is not a cyclic bend or shock rating; fatigue life and termination geometry unqualified. | [manufacturer source](https://gleistein.com/en/applications/stringing/single-product/dynaone-hs/pdf//) |
| dynaone_hs_5 | Manufacturer catalog; current supplier stock and price unknown. Bend-fatigue life unknown for the proposed drums; supplier review required. | [manufacturer source](https://gleistein.com/en/applications/stringing/single-product/dynaone-hs/pdf//) |
| dynaone_hs_6 | Manufacturer catalog; current supplier stock and price unknown. Bend-fatigue life unknown for the proposed drums; supplier review required. | [manufacturer source](https://gleistein.com/en/applications/stringing/single-product/dynaone-hs/pdf//) |

## Supply and buffer consequences

The EPP-500-48 candidate occupies 127 × 76.2 × 40 mm, but its 499.2 W rating requires 25 CFM; natural-convection output is 321.6 W, with input/temperature derating still applicable. A fan, isolation boundary and airflow path consume additional space.

22 × 350 F cells in series yield **15.91 F**, **0.0704 Ω** initial ESR, and **1.32 kg** of cells. The end-life screen is 12.73 F and 0.1408 Ω. The old combination of a 2 F model and large-cell package was not an exact selected bank. Balancing, pre-charge, discharge, reverse-current blocking and fault protection are additional parts.

The new catalog reduces variant ambiguity through primary sources but does not settle measurement conventions, mounting thermal paths, fatigue, live inventory, pricing or qualification. No candidate is certified for this application.
