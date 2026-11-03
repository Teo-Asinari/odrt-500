# R4 pre-charge and service-discharge sequences

Fingerprint: `9467e51e7e5e6568c3d73b021368a0aa994d954732766292ed2b31971198ff80` (R4 `75697c0bbd11`)

**Sequence simulation of the sized power path, not a circuit qualification.** Separate electrical model: supply with 0.2 Ω droop and a 9.6 A constant-current limit, 3 mF drive bus, 6.8 Ω pre-charge resistor, bypass closes at 1.88 V difference (the largest that keeps top-off current under the supply margin), drive enabled only after bypass closure and bank ≥ 45 V, 10 W auxiliary load above 15 V (assumed).

| Bank / sequence | Bypass s | Enable s | Charged s | Supply peak A | At limit s | Bank peak A | Resistor J | Resistor rise K | Outcome |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| r2_fresh/A_supply_cc | — | 24 | 31 | 9.62 | 25.6 | 9.6 | 0 | 0 | charged; relies on supply constant-current mode |
| r2_fresh/B_resistor | 120 | 120 | 123 | 7.42 | 0.0 | 7.2 | 6337 | 34 | charged; supply stays under its limit |
| r2_fresh/B_bypass_welded | — | 24 | 31 | 9.62 | 25.6 | 9.6 | 0 | 0 | charged; relies on supply constant-current mode |
| r2_fresh/B_bypass_open | — | — | — | 7.42 | 0.0 | 7.2 | 6345 | 34 | bypass timeout at 168 s; drive stays disabled |
| r2_fresh/B_mains_loss_midway | — | — | — | 7.42 | 0.0 | 7.2 | 5214 | 32 | drive never enabled; bank 24.2 V |
| r2_aged/A_supply_cc | — | 15 | 21 | 9.62 | 15.4 | 9.6 | 0 | 0 | charged; relies on supply constant-current mode |
| r2_aged/B_resistor | 62 | 62 | 67 | 7.21 | 0.0 | 7.0 | 3859 | 22 | charged; supply stays under its limit |
| r2_aged/B_bypass_welded | — | 15 | 21 | 9.62 | 15.4 | 9.6 | 0 | 0 | charged; relies on supply constant-current mode |
| r2_aged/B_bypass_open | — | — | — | 7.21 | 0.0 | 7.0 | 3876 | 22 | bypass timeout at 86 s; drive stays disabled |
| r2_aged/B_mains_loss_midway | — | — | — | 7.21 | 0.0 | 7.0 | 3618 | 22 | drive never enabled; bank 31.4 V |

"Charged" means the bank within 0.5 V of the setpoint. Resistor rise uses an assumed 150 J/K and 1.5 K/W. The bypass-open fault times out at 1.5 × the expected bypass time. Mains loss is at 30 s.

## Service discharge

| Bank | Start V | To safe voltage s | Resistor J | Resistor rise K | Bus below auxiliary minimum s |
|---|---:|---:|---:|---:|---:|
| r2_fresh | 53.68 | 83 | 6887 | 37 | 0.40 |
| r2_aged | 53.68 | 54 | 4206 | 24 | 0.40 |

With the bank disconnected, the drive bus and auxiliary rails collapse almost at once, so the supervisor cannot hold the discharge switch on. The discharge path must be normally closed (fail-to-discharge) and opened only by an energised supervisor.

Reproduce: `make precharge` (after `make power-path`).
