# R4 pre-charge and service-discharge sequences

Fingerprint: `b63f5acce6074dc5a82aa62b0adcc6a9176351d1c351782d9328a506adee46fb` (R4 `0d0df70a4358`)

**Adopted start-up: sequence A, direct supply charging** (owner decision 2026-11-03). It depends on the EPP-500-54 current-limiting continuously into the bank, which is unverified; sequence B is the fallback. 

**Sequence simulation of the sized power path, not a circuit qualification.** Separate electrical model: supply with 0.2 Ω droop and a 9.6 A constant-current limit, 3 mF drive bus, 6.8 Ω pre-charge resistor, bypass closes at 1.88 V difference (the largest that keeps top-off current under the supply margin), drive enabled only after bypass closure and bank ≥ 45 V, 10 W auxiliary load above 15 V (assumed).

| Bank / sequence | Auxiliary up s | Bypass s | Enable s | Charged s | Supply peak A | At limit s | Bank peak A | Resistor J | Resistor rise K | Outcome |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| r2_fresh/A_supply_cc | 6.6 | — | 24 | 31 | 9.62 | 25.6 | 9.6 | 0 | 0 | charged; relies on supply constant-current mode |
| r2_fresh/A_disconnect_open | 0.0 | — | — | — | 0.20 | 0.0 | 0.0 | 0 | 0 | start-up timeout at 35 s; drive stays disabled |
| r2_fresh/A_mains_loss_midway | 6.6 | — | — | — | 9.62 | 10.0 | 9.6 | 0 | 0 | drive never enabled; bank 15.0 V |
| r2_fresh/B_resistor | 0.0 | 120 | 120 | 123 | 7.42 | 0.0 | 7.2 | 6337 | 34 | charged; supply stays under its limit |
| r2_fresh/B_bypass_welded | 6.6 | — | 24 | 31 | 9.62 | 25.6 | 9.6 | 0 | 0 | charged; relies on supply constant-current mode |
| r2_fresh/B_bypass_open | 0.0 | — | — | — | 7.42 | 0.0 | 7.2 | 6345 | 34 | start-up timeout at 168 s; drive stays disabled |
| r2_fresh/B_mains_loss_midway | 0.0 | — | — | — | 7.42 | 0.0 | 7.2 | 5214 | 32 | drive never enabled; bank 24.2 V |
| r2_aged/A_supply_cc | 3.5 | — | 15 | 21 | 9.62 | 15.4 | 9.6 | 0 | 0 | charged; relies on supply constant-current mode |
| r2_aged/A_disconnect_open | 0.0 | — | — | — | 0.20 | 0.0 | 0.0 | 0 | 0 | start-up timeout at 22 s; drive stays disabled |
| r2_aged/A_mains_loss_midway | 3.5 | — | — | — | 9.62 | 10.0 | 9.6 | 0 | 0 | drive never enabled; bank 22.0 V |
| r2_aged/B_resistor | 0.0 | 62 | 62 | 67 | 7.21 | 0.0 | 7.0 | 3859 | 22 | charged; supply stays under its limit |
| r2_aged/B_bypass_welded | 3.5 | — | 15 | 21 | 9.62 | 15.4 | 9.6 | 0 | 0 | charged; relies on supply constant-current mode |
| r2_aged/B_bypass_open | 0.0 | — | — | — | 7.21 | 0.0 | 7.0 | 3876 | 22 | start-up timeout at 86 s; drive stays disabled |
| r2_aged/B_mains_loss_midway | 0.0 | — | — | — | 7.21 | 0.0 | 7.0 | 3618 | 22 | drive never enabled; bank 31.4 V |

"Charged" means the bank within 0.5 V of the setpoint. Resistor rise uses an assumed 150 J/K and 1.5 K/W. The bypass-open fault times out at 1.5 × the expected bypass time (B) or 1.5 × the expected constant-current charge time to the enable threshold (A). Mains loss is at 10 s (A) or 30 s (B).

In sequence A the drive bus follows the bank from 0 V, so the auxiliary rail and supervisor only start once the bank passes 15 V ("Auxiliary up"). The bank disconnect therefore cannot wait for the supervisor: it must close by default at power-on (normally closed, or closed by a hardware circuit), and the supervisor may only open it. In sequence B the supply brings the bus up at once, so the supervisor is alive before it switches anything.

## Service discharge

| Bank | Start V | To safe voltage s | Resistor J | Resistor rise K | Bus below auxiliary minimum s |
|---|---:|---:|---:|---:|---:|
| r2_fresh | 53.68 | 83 | 6887 | 37 | 0.40 |
| r2_aged | 53.68 | 54 | 4206 | 24 | 0.40 |

With the bank disconnected, the drive bus and auxiliary rails collapse almost at once, so the supervisor cannot hold the discharge switch on. The discharge path must be normally closed (fail-to-discharge) and opened only by an energised supervisor.

Reproduce: `make precharge` (after `make power-path`).
