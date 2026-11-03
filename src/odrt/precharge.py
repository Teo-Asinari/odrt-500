"""Start-up pre-charge and service-discharge sequences for the R4 power path.

The drive bus is quasi-static (its milliseconds-scale capacitance is neglected against
the bank's tens of seconds); only the bank, resistor energy and resistor temperature
are integrated.

Run python -m odrt.precharge (make precharge, after make power-path). A small
electrical model, separate from the coupled machine model:

    supply (CV setpoint, droop, one-way, constant-current limit)
      -> drive bus (C_bus, 10 kOhm bleed, auxiliary load, drive idle when enabled)
      -> path (pre-charge resistor | bypass switch | open | discharge) -> bank (C, ESR, balancing)

The supervisor logic is discrete: it closes the bypass when the bus-to-bank
difference falls below a threshold and enables the drive only after the bypass
is confirmed closed and the bank is above the enable threshold. Sequences:

  A  supply_cc    bank connected directly; relies on the supply's constant-current limit
  B  resistor     pre-charge resistor, bypass threshold chosen so the supply never reaches its limit

and fault variants of B. The supply's real overload mode (constant current vs
hiccup) is not verified; sequence A and the B-with-welded-bypass fault are
only valid if it is constant current. Normal R4 operation already relies on it.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from odrt.config import ConfigError, load_yaml


def fingerprint(root=Path('.')):
    root = Path(root); h = hashlib.sha256()
    for rel in ('data/power_path.yaml', 'data/revision_components.yaml'):
        h.update(rel.encode()+b'\0'+(root/rel).read_bytes()+b'\0')
    h.update(Path(__file__).read_bytes())
    h.update(json.loads((root/'reports/r4_candidate.json').read_text())['fingerprint'].encode())
    return h.hexdigest()


def parameters(r4, spec, components, bank):
    p = r4['power']; cell = r4['cell_values'][bank]; n = p['cell_series']; d = spec['design']; s = spec['sequence']
    supply = components['epp500_54']['facts']
    v0 = p['nominal_v']; limit = supply['power_forced_air_w']/v0
    esr = cell['esr_initial_max_ohm']*n; loop = esr+d['wiring_resistance_ohm']
    r_pre = v0/(d['supply_current_margin']*limit)
    # Largest bypass difference that keeps top-off current under the supply margin.
    close_dv = d['supply_current_margin']*limit*(loop+d['disconnect_on_resistance_ohm'])
    return dict(v0=v0, limit=limit, droop=p['supply_droop_ohm'], c_bus=p['bus_capacitance_f'],
                bleed=p['bleed_resistance_ohm'], c_bank=cell['capacitance_f']/n, esr=esr, wiring=d['wiring_resistance_ohm'],
                r_switch=d['disconnect_on_resistance_ohm'], r_pre=r_pre, close_dv=close_dv,
                r_balance=v0/(d['balancing_current_ratio']*d['cell_leakage_a']),  # whole string of per-cell resistors
                enable_v=r4['derived']['r4_power']['functions']['precharge']['enable_threshold_v'],
                aux_w=s['aux_load_w'], aux_min_v=s['aux_min_input_v'], idle_w=p['drive_idle_w'],
                charged_dv=s['charged_within_v'], timeout_factor=s['bypass_timeout_factor'],
                res_c=s['resistor_heat_capacity_j_k'], res_r=s['resistor_to_air_k_w'], safe_v=d['service_safe_v'])


R_PATH = {'precharge': 'r_pre', 'discharge': 'r_pre', 'bypass': 'r_switch'}


def _path_r(q, path):
    return None if path not in R_PATH else q[R_PATH[path]]+q['esr']+q['wiring']


def _bus(q, vc, path, supply_on, enabled):
    """Quasi-static drive bus: solve supply = loads + bank-path current. The bus capacitance
    (milliseconds against a bank time constant of tens of seconds) is neglected here."""
    from scipy.optimize import brentq
    r = _path_r(q, path)
    if path == 'discharge' or (r is None and not supply_on):
        return 0.                                    # bus isolated from the bank and unpowered
    def balance(vb):
        i_sup = min(max((q['v0']-vb)/q['droop'], 0.), q['limit']) if supply_on else 0.
        load = vb/q['bleed'] + (q['aux_w']/vb if vb > q['aux_min_v'] else 0.) + (q['idle_w']/vb if enabled and vb > 1 else 0.)
        return i_sup-load-(0. if r is None else (vb-vc)/r)
    return brentq(balance, 1e-6, q['v0']+5, xtol=1e-9)


def _state(q, vc, path, supply_on, enabled):
    vb = _bus(q, vc, path, supply_on, enabled); r = _path_r(q, path)
    i_bank = 0. if r is None else ((0. if path == 'discharge' else vb)-vc)/r
    i_sup = min(max((q['v0']-vb)/q['droop'], 0.), q['limit']) if supply_on else 0.
    return vb, i_bank, i_sup


def _rhs(q, path, supply_on, enabled):
    def f(t, y):
        vc, energy, temp = y
        _, i_bank, _ = _state(q, vc, path, supply_on, enabled)
        p_res = i_bank**2*q['r_pre'] if path in ('precharge', 'discharge') else 0.
        return [(i_bank-vc/q['r_balance'])/q['c_bank'], p_res, (p_res-temp/q['res_r'])/q['res_c']]
    return f


def run_sequence(q, mode, fault=None, horizon_s=600.):
    """Integrate one start-up; returns timing and peaks."""
    from scipy.integrate import solve_ivp
    y = [0., 0., 0.]; t0 = 0.; path = 'bypass' if mode == 'supply_cc' or fault == 'bypass_welded' else 'precharge'
    supply_on, enabled, log = True, False, {}
    rows = []
    deadline_s = q['timeout_factor']*q['r_pre']*q['c_bank']*np.log(q['v0']/q['close_dv'])
    if 'mains_loss_s' in q: horizon_s = q['mains_loss_s']+60
    while t0 < horizon_s:
        def gap(t, y): return (_bus(q, y[0], path, supply_on, enabled)-y[0])-q['close_dv']
        def close(t, y): return gap(t, y) if path == 'precharge' and fault != 'bypass_open' and supply_on else 1.
        def enable(t, y): return y[0]-q['enable_v'] if not enabled and path == 'bypass' else -1.
        def charged(t, y): return (q['v0']-y[0])-q['charged_dv'] if enabled else 1.
        def mains(t, y): return t-q.get('mains_loss_s', 1e9) if supply_on else -1.
        def deadline(t, y): return t-deadline_s if path == 'precharge' and supply_on else -1.
        evs = [close, enable, charged, mains, deadline]
        for e in evs: e.terminal = True
        close.direction = charged.direction = -1; enable.direction = mains.direction = deadline.direction = 1
        sol = solve_ivp(_rhs(q, path, supply_on, enabled), (t0, horizon_s), y, method='LSODA', events=evs,
                        max_step=0.25, rtol=1e-8, atol=1e-9)
        if not sol.success: raise RuntimeError(sol.message)
        for t, yy in zip(sol.t, sol.y.T):
            vb, i_bank, i_sup = _state(q, yy[0], path, supply_on, enabled)
            rows.append((t, vb, yy[0], i_bank, i_sup, yy[1], yy[2], enabled))
        y = list(sol.y[:, -1]); t0 = sol.t[-1]
        hit = [k for k, e in enumerate(sol.t_events) if e.size]
        if not hit: break
        k = hit[0]
        if k == 0: path = 'bypass'; log['bypass_s'] = t0
        elif k == 1: enabled = True; log['enable_s'] = t0
        elif k == 2: log['charged_s'] = t0; break
        elif k == 3: supply_on = False; log['mains_loss_s'] = t0
        elif k == 4: log['bypass_timeout_s'] = t0; break
        # Level conditions already true at a switching instant act at once (no crossing follows).
        if not enabled and path == 'bypass' and y[0] >= q['enable_v']:
            enabled = True; log['enable_s'] = t0
        # The step right after a switching event carries the transient peak (e.g. bypass inrush).
        vb, i_bank, i_sup = _state(q, y[0], path, supply_on, enabled)
        rows.append((t0, vb, y[0], i_bank, i_sup, y[1], y[2], enabled))
        if enabled and q['v0']-y[0] <= q['charged_dv']:
            log['charged_s'] = t0; break
    t, vb, vc, ib, isup, energy, temp, en = (np.array(c, dtype=float) for c in zip(*rows))
    return {**log, 'end_s': float(t[-1]), 'final_bank_v': float(vc[-1]), 'drive_enabled': 'enable_s' in log,
            'supply_peak_a': float(isup.max()), 'supply_limit_a': q['limit'],
            'supply_at_limit_s': float(np.trapz((isup >= .999*q['limit']).astype(float), t)),
            'bank_peak_a': float(np.abs(ib).max()), 'resistor_energy_j': float(energy[-1]), 'resistor_rise_k': float(temp.max()),
            'min_bus_after_enable_v': float(vb[en > .5].min()) if en.any() else None}


def run_discharge(q, start_v):
    """Mains off, disconnect open, bank -> resistor -> return; the switch is assumed normally closed."""
    from scipy.integrate import solve_ivp
    def safe(t, y): return y[0]-q['safe_v']
    safe.terminal = True; safe.direction = -1
    sol = solve_ivp(_rhs(q, 'discharge', False, False), (0, 3600), [start_v, 0., 0.], method='LSODA',
                    events=[safe], max_step=1., rtol=1e-8, atol=1e-9)
    if not sol.success or not sol.t_events[0].size: raise RuntimeError('service discharge did not reach the safe voltage')
    # Isolated drive bus: its capacitance alone feeds the auxiliary load until the converter drops out.
    aux_s = q['c_bus']*(start_v**2-q['aux_min_v']**2)/(2*q['aux_w'])
    return {'start_v': start_v, 'safe_s': float(sol.t_events[0][0]), 'resistor_energy_j': float(sol.y[1, -1]),
            'resistor_rise_k': float(sol.y[2].max()), 'bus_below_aux_minimum_s': aux_s}


CASES = (('A_supply_cc', 'supply_cc', None), ('B_resistor', 'resistor', None),
         ('B_bypass_welded', 'resistor', 'bypass_welded'), ('B_bypass_open', 'resistor', 'bypass_open'),
         ('B_mains_loss_midway', 'resistor', 'mains_loss'))


def run(root=Path('.')):
    root = Path(root); initial = fingerprint(root)
    r4 = json.loads((root/'reports/r4_candidate.json').read_text())
    spec = load_yaml(root/'data/power_path.yaml'); components = load_yaml(root/'data/revision_components.yaml')
    results, discharge, params = {}, {}, {}
    for bank in ('r2_fresh', 'r2_aged'):
        q = parameters(r4, spec, components, bank); params[bank] = q
        for name, mode, fault in CASES:
            qq = dict(q, mains_loss_s=spec['sequence']['mains_loss_at_s']) if fault == 'mains_loss' else q
            res = run_sequence(qq, mode, fault)
            results[f'{bank}/{name}'] = res
        bank_max = max(m[k] for b in r4['banks'].values() for m in b.values() for k in m if k.endswith('.max_capacitor_v'))
        discharge[bank] = run_discharge(q, bank_max)
    if fingerprint(root) != initial:
        raise ConfigError('pre-charge inputs changed during run; refusing publication')
    report = {'fingerprint': initial, 'r4_fingerprint': r4['fingerprint'], 'sequence_assumptions': spec['sequence'],
              'parameters': params, 'startup': results, 'discharge': discharge}
    (root/'reports/precharge.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    write_report(report, root/'reports/precharge.md')
    return report


def write_report(r, path):
    s = r['sequence_assumptions']; f = lambda v, fmt='.1f': '—' if v is None else format(v, fmt)
    q = r['parameters']['r2_fresh']
    L = ['# R4 pre-charge and service-discharge sequences', '', f'Fingerprint: `{r["fingerprint"]}` (R4 `{r["r4_fingerprint"][:12]}`)', '',
         '**Sequence simulation of the sized power path, not a circuit qualification.** Separate electrical model: supply with '
         f'{q["droop"]} Ω droop and a {q["limit"]:.1f} A constant-current limit, {1000*q["c_bus"]:.0f} mF drive bus, '
         f'{q["r_pre"]:.1f} Ω pre-charge resistor, bypass closes at {q["close_dv"]:.2f} V difference (the largest that keeps top-off '
         f'current under the supply margin), drive enabled only after bypass closure and bank ≥ {q["enable_v"]} V, '
         f'{s["aux_load_w"]} W auxiliary load above {s["aux_min_input_v"]} V (assumed).', '',
         '| Bank / sequence | Bypass s | Enable s | Charged s | Supply peak A | At limit s | Bank peak A | Resistor J | Resistor rise K | Outcome |',
         '|---|---:|---:|---:|---:|---:|---:|---:|---:|---|']
    for name, x in r['startup'].items():
        if x.get('bypass_timeout_s') is not None: outcome = f'bypass timeout at {x["bypass_timeout_s"]:.0f} s; drive stays disabled'
        elif not x['drive_enabled']: outcome = f'drive never enabled; bank {x["final_bank_v"]:.1f} V'
        elif x['supply_at_limit_s'] > 0: outcome = 'charged; relies on supply constant-current mode'
        else: outcome = 'charged; supply stays under its limit'
        lines = (f'| {name} | {f(x.get("bypass_s"), ".0f")} | {f(x.get("enable_s"), ".0f")} | {f(x.get("charged_s"), ".0f")} | '
                 f'{x["supply_peak_a"]:.2f} | {x["supply_at_limit_s"]:.1f} | {x["bank_peak_a"]:.1f} | {x["resistor_energy_j"]:.0f} | '
                 f'{x["resistor_rise_k"]:.0f} | {outcome} |')
        L.append(lines)
    L += ['', f'"Charged" means the bank within {s["charged_within_v"]} V of the setpoint. Resistor rise uses an assumed '
          f'{s["resistor_heat_capacity_j_k"]} J/K and {s["resistor_to_air_k_w"]} K/W. The bypass-open fault times out at '
          f'{s["bypass_timeout_factor"]} × the expected bypass time. Mains loss is at {s["mains_loss_at_s"]} s.', '',
          '## Service discharge', '', '| Bank | Start V | To safe voltage s | Resistor J | Resistor rise K | Bus below auxiliary minimum s |',
          '|---|---:|---:|---:|---:|---:|']
    for bank, x in r['discharge'].items():
        L.append(f'| {bank} | {x["start_v"]:.2f} | {x["safe_s"]:.0f} | {x["resistor_energy_j"]:.0f} | {x["resistor_rise_k"]:.0f} | '
                 f'{f(x["bus_below_aux_minimum_s"], ".2f")} |')
    L += ['', 'With the bank disconnected, the drive bus and auxiliary rails collapse almost at once, so the supervisor cannot hold '
          'the discharge switch on. The discharge path must be normally closed (fail-to-discharge) and opened only by an energised supervisor.', '',
          'Reproduce: `make precharge` (after `make power-path`).', '']
    path.write_text('\n'.join(L))


if __name__ == '__main__':
    run()
