"""R4 power-path sizing from the simulated envelope (make power-path).

Reads reports/r4_candidate.json and data/power_path.yaml. It sizes the
reverse-blocking stage, bank fuse and disconnect, the shared pre-charge /
service-discharge resistor, passive balancing and dump-path monitoring.
These are functional ratings derived from the model, not part selections or
manufacturer-rated circuits. Assumptions are reported with every result.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from odrt.config import ConfigError, load_yaml


def fingerprint(root=Path('.')):
    root = Path(root); h = hashlib.sha256()
    for rel in ('data/power_path.yaml', 'data/revision_components.yaml'):
        h.update(rel.encode()+b'\0'+(root/rel).read_bytes()+b'\0')
    h.update(Path(__file__).read_bytes())
    h.update(json.loads((root/'reports/r4_candidate.json').read_text())['fingerprint'].encode())
    return h.hexdigest()


def _envelope(r4):
    rows = [(bank, case, m) for bank, b in r4['banks'].items() for case, m in b.items() if 'solver_failure' not in m]
    if len(rows) != sum(len(b) for b in r4['banks'].values()):
        raise ConfigError('power path: R4 report has solver failures; size from a complete envelope only')

    def worst(suffix, rows=rows):
        value, where = max(((m[k], f'{bank}/{case}') for bank, case, m in rows for k in m if k.endswith(suffix)))
        return value, where
    normal = [x for x in rows if not any(x[2][k] for k in x[2] if k.endswith('.trip_latched'))]
    return {'bank_rms_a': worst('.capacitor_rms_a'), 'bank_peak_a': worst('.capacitor_peak_a'),
            'bank_max_v': worst('.max_capacitor_v'), 'supply_peak_a': worst('.supply_peak_a'),
            'dump_average_peak_a': worst('.dump_average_peak_a'),
            'bus_max_v': max(((m['maximum_bus_v'], f'{b}/{c}') for b, c, m in rows)),
            'bus_min_normal_v': min(((m['minimum_bus_v'], f'{b}/{c}') for b, c, m in normal))}


def size(r4, spec, components):
    d = spec['design']; p = r4['power']; cells = r4['cell_values']; n = p['cell_series']
    mon = r4['derived']['r4_power']['functions']['dump_monitor']
    env = _envelope(r4); v0 = p['nominal_v']; trip = p['trip_v']
    supply = components['epp500_54']['facts']; limit_a = supply['power_forced_air_w']/v0
    esr = {b: cells[b]['esr_initial_max_ohm']*n for b in cells}
    cap = {b: cells[b]['capacitance_f']/n for b in cells}
    out = {'envelope': {k: {'value': v[0], 'case': v[1]} for k, v in env.items()}}

    # The Regen Clamp stays: its ideal diode becomes the supply reverse block, its clamp the dump.
    clamp = components['regen_clamp']['facts']; fwd = env['supply_peak_a'][0]
    i_dump = p['dump_full_v']/p['dump_resistance_ohm']
    out['regen_clamp'] = {
        'voltage_max_v': clamp['voltage_max_v'], 'trip_v': trip, 'bus_max_v': env['bus_max_v'][0],
        'trip_margin_v': clamp['voltage_max_v']-trip, 'voltage_pass': env['bus_max_v'][0] < clamp['voltage_max_v'],
        'margin_required_v': d['clamp_margin_v'], 'margin_pass': clamp['voltage_max_v']-trip >= d['clamp_margin_v'],
        'bus_margin_v': clamp['voltage_max_v']-env['bus_max_v'][0],
        'forward_a': fwd, 'forward_rating_free_air_a': clamp['forward_free_air_a'], 'forward_pass': fwd < clamp['forward_free_air_a'],
        'brake_switched_a': i_dump, 'brake_average_peak_a': env['dump_average_peak_a'][0],
        'brake_continuous_a': clamp['brake_heatspreader_a'], 'brake_peak_3s_a': clamp['brake_peak_3s_a'],
        'brake_continuous_pass': env['dump_average_peak_a'][0] <= clamp['brake_heatspreader_a'],
        'brake_peak_pass': i_dump <= clamp['brake_peak_3s_a'],
        'note': 'The chopper switches the full bus voltage across the 1 Ω dump, so its instantaneous current is bus V / 1 Ω, '
                'inside the 80 A / 3 s peak. The cycle-averaged current is compared with the 40 A heatspreader rating. '
                'Whether that rating is an average or an instantaneous limit, and the chopper ripple, are verification items.'}

    # Reverse blocking on the supply output: blocks whenever the bus is above the setpoint.
    out['reverse_blocking'] = {
        'blocking_v_max': env['bus_max_v'][0]-v0, 'blocking_at_trip_v': trip-v0, 'forward_a': fwd,
        'loss_w': fwd**2*d['ideal_diode_on_resistance_ohm'], 'device_class_v': d['device_voltage_class_v'],
        'source_fuse_min_a': d['fuse_current_factor']*limit_a,
        'note': 'Blocks during every regenerative event, not only at faults: the bus sits at the 54.4 V dump level in normal use.'}

    # Bank fuse and disconnect.
    rms, peak = env['bank_rms_a'][0], env['bank_peak_a'][0]
    prospective = {b: trip/(esr[b]+d['wiring_resistance_ohm']) for b in esr}
    fuse = d['fuse_current_factor']*rms
    out['bank_protection'] = {
        'rms_a': rms, 'peak_a': peak, 'fuse_min_rating_a': fuse, 'peak_to_fuse_rating': peak/fuse,
        'prospective_fault_a': prospective, 'fault_multiple_of_rating': {b: v/fuse for b, v in prospective.items()},
        'disconnect_loss_w': rms**2*d['disconnect_on_resistance_ohm'], 'device_class_v': d['device_voltage_class_v'],
        'note': 'Bank short-circuit current is set by cell ESR, so the aged bank gives the lowest clearing multiple. '
                'Fuse time-current behaviour at that multiple must be checked against the cell and wiring I²t.'}

    # One pulse resistor: pre-charge (bus -> bank) at start, service discharge (bank -> return) at shutdown.
    r = v0/(d['supply_current_margin']*limit_a)
    enable = r4['derived']['r4_power']['functions']['precharge']['enable_threshold_v']
    # Close the bypass only when top-off current through the closed path stays under the supply margin;
    # the drive is enabled after closure (make precharge simulates the same rule).
    close_dv = lambda b: d['supply_current_margin']*limit_a*(esr[b]+d['wiring_resistance_ohm']+d['disconnect_on_resistance_ohm'])
    rows = []
    for b in cap:
        tau = r*cap[b]; dv = close_dv(b); vc = v0-dv
        rows.append({'bank': b, 'bank_capacitance_f': cap[b], 'tau_s': tau,
                     'bypass_close_delta_v': dv, 'time_to_bypass_s': tau*math.log(v0/dv),
                     'time_to_enable_s': max(tau*math.log(v0/dv), tau*math.log(v0/(v0-enable))),
                     'precharge_energy_j': cap[b]*v0*vc-.5*cap[b]*vc*vc,
                     'bypass_inrush_a': dv/(esr[b]+d['wiring_resistance_ohm']),
                     'discharge_time_s': tau*math.log(env['bank_max_v'][0]/d['service_safe_v']),
                     'discharge_energy_j': .5*cap[b]*env['bank_max_v'][0]**2,
                     'bleed_only_tau_h': p['bleed_resistance_ohm']*cap[b]/3600})
    out['precharge_discharge'] = {
        'resistor_ohm': r, 'peak_power_w': v0**2/r, 'supply_current_a': v0/r, 'supply_limit_a': limit_a, 'rows': rows,
        'note': 'The resistor limits supply current itself, so start-up does not depend on the supply overload mode. '
                'The same resistor discharges the bank for service. Pulse-energy rating, not continuous power, sizes it.'}

    # Passive balancing and dynamic imbalance from capacitance spread.
    vcell = v0/n; i_bal = d['balancing_current_ratio']*d['cell_leakage_a']; r_bal = vcell/i_bal
    spread = d['capacitance_spread_fraction']
    dynamic = lambda vbank: v0/n+(vbank-v0)/n/(1-spread)
    rated = cells['r2_fresh']['voltage_rated_v']
    out['balancing'] = {
        'resistor_ohm': r_bal, 'current_a': i_bal, 'loss_per_cell_w': vcell*i_bal, 'loss_bank_w': n*vcell*i_bal,
        'self_discharge_tau_h': r_bal*cells['r2_fresh']['capacitance_f']/3600,
        'worst_cell_at_max_bank_v': dynamic(env['bank_max_v'][0]), 'worst_cell_at_trip_v': dynamic(trip),
        'cell_monitor_trip_v': d['cell_monitor_trip_v'], 'cell_rated_v': rated,
        'normal_below_monitor': dynamic(env['bank_max_v'][0]) < d['cell_monitor_trip_v'],
        'trip_below_rating': dynamic(trip) < rated,
        'note': 'Cells balanced at the setpoint; dynamic excursions above it divide by capacitance, so the lowest-capacitance '
                'cell rises fastest. Leakage-driven drift is held by the passive resistors while the supply holds the setpoint.'}

    # Dump-path monitoring: the bank now hides a failed dump from the overvoltage trip.
    fresh_dump = r4['banks']['r2_fresh'].get('paired_dump_failure', {})
    out['dump_monitor'] = {
        'peak_current_a': i_dump, 'shunt_ohm': d['dump_shunt_ohm'], 'shunt_signal_mv': 1000*i_dump*d['dump_shunt_ohm'],
        'shunt_peak_w': i_dump**2*d['dump_shunt_ohm'], 'detection_s': mon['detection_s'],
        'fresh_dump_failure_bus_max_v': fresh_dump.get('maximum_bus_v'), 'dump_start_v': p['dump_start_v'],
        'rule': f'Expected dump current is commanded duty × bus V / {p["dump_resistance_ohm"]} Ω. Flag a dump-path fault when measured current '
                f'stays below {mon["measured_fraction"]} × expected for {mon["detection_s"]} s while expected exceeds {mon["min_expected_a"]} A, or when the bus '
                f'exceeds {mon["backup_bus_v"]} V for {mon["detection_s"]} s; stop the unit and latch, independent of the overvoltage trip.'}
    out['bank_duty'] = {'derate_start_c': d['bank_derate_start_c'], 'case_max_c': cells['r2_fresh']['case_max_c'],
                        'continuous_fast_reversal_c': r4['derived']['r4_checks']['continuous_repetition_cell_c'],
                        'rule': 'Bank temperature sensing (balancing node) feeds the existing torque derate from '
                                f'{d["bank_derate_start_c"]} °C to the case maximum; this is the duty limit for back-to-back fast work.'}
    return out


def run(root=Path('.')):
    root = Path(root); initial = fingerprint(root)
    r4 = json.loads((root/'reports/r4_candidate.json').read_text())
    spec = load_yaml(root/'data/power_path.yaml'); components = load_yaml(root/'data/revision_components.yaml')
    result = {'fingerprint': initial, 'r4_fingerprint': r4['fingerprint'], 'assumptions': spec['design'],
              'sources_not_read': spec['sources_not_read'], **size(r4, spec, components)}
    if fingerprint(root) != initial:
        raise ConfigError('power path inputs changed during run; refusing publication')
    (root/'reports/power_path.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    write_report(result, root/'reports/power_path.md')
    return result


def write_report(r, path):
    e, rb, bp, pc, bal, dm, duty = (r[k] for k in ('envelope', 'reverse_blocking', 'bank_protection',
                                                   'precharge_discharge', 'balancing', 'dump_monitor', 'bank_duty'))
    a = r['assumptions']; ok = lambda x: 'pass' if x else 'FAIL'
    L = ['# R4 power-path sizing', '', f'Fingerprint: `{r["fingerprint"]}` (R4 `{r["r4_fingerprint"][:12]}`)', '',
         '**Functional sizing only.** Ratings are derived from the [R4 simulated envelope](r4_candidate.md) and cited data already '
         'in the repository. No part is selected; every `assumed` value in `data/power_path.yaml` is a verification item.', '',
         '## Simulated envelope', '', '| Quantity | Value | Worst case |', '|---|---:|---|']
    names = {'bank_rms_a': 'Bank RMS current A', 'bank_peak_a': 'Bank peak current A', 'bank_max_v': 'Bank maximum V',
             'supply_peak_a': 'Supply peak current A', 'bus_max_v': 'Bus maximum V (incl. faults)',
             'bus_min_normal_v': 'Bus minimum V (untripped cases)', 'dump_average_peak_a': 'Dump current, cycle-averaged maximum A'}
    L += [f'| {names[k]} | {v["value"]:.2f} | {v["case"]} |' for k, v in e.items()]
    c = r['regen_clamp']
    L += ['', '## Regen Clamp in R4 (reverse block + dump)', '',
          'R4 keeps the ODrive Regen Clamp but moves the bank to its output (drive) side. Its ideal diode then blocks back-feed into '
          'the supply, and its clamp remains the dump chopper.', '',
          '| Check | Simulated / required | Clamp rating | Outcome |', '|---|---:|---:|---|',
          f'| Bus maximum (incl. faults) | {c["bus_max_v"]:.2f} V | {c["voltage_max_v"]} V | {ok(c["voltage_pass"])} |',
          f'| Clamp maximum minus the {c["trip_v"]:g} V trip | {c["trip_margin_v"]:.1f} V | at least {c["margin_required_v"]} V | {ok(c["margin_pass"])} |',
          f'| Clamp maximum minus the simulated bus maximum | {c["bus_margin_v"]:.2f} V | — | {"pass" if c["bus_margin_v"] > 0 else "FAIL"} |',
          f'| Forward (supply) current | {c["forward_a"]:.1f} A | {c["forward_rating_free_air_a"]} A free air | {ok(c["forward_pass"])} |',
          f'| Brake current, cycle-averaged maximum ({e["dump_average_peak_a"]["case"]}) | {c["brake_average_peak_a"]:.1f} A | '
          f'{c["brake_continuous_a"]} A heatspreader | {ok(c["brake_continuous_pass"])} |',
          f'| Brake current, switched (bus V / dump resistance) | {c["brake_switched_a"]:.1f} A | {c["brake_peak_3s_a"]} A for 3 s | {ok(c["brake_peak_pass"])} |', '',
          c['note'], '',
          '## Reverse blocking (source block)', '',
          f'Provided by the clamp\'s ideal diode, or, if the 58 V rating is rejected, a discrete {rb["device_class_v"]} V-class MOSFET OR-ing stage. It blocks up to '
          f'{rb["blocking_v_max"]:.1f} V in the simulated envelope and {rb["blocking_at_trip_v"]:.1f} V at the trip, carries '
          f'{rb["forward_a"]:.1f} A forward and dissipates about {rb["loss_w"]:.2f} W at {a["ideal_diode_on_resistance_ohm"]} Ω (assumed). '
          f'Source branch DC fuse at least {rb["source_fuse_min_a"]:.1f} A. ' + rb['note'], '',
          '## Bank fuse and disconnect', '',
          f'Bank RMS {bp["rms_a"]:.1f} A and peak {bp["peak_a"]:.1f} A. Fuse at least {bp["fuse_min_rating_a"]:.1f} A '
          f'({a["fuse_current_factor"]} × RMS); the peak is {bp["peak_to_fuse_rating"]:.1f} × that rating, so a time-delay DC fuse is needed. '
          f'Back-to-back MOSFET disconnect, {bp["device_class_v"]} V class, about {bp["disconnect_loss_w"]:.2f} W at '
          f'{a["disconnect_on_resistance_ohm"]} Ω (assumed).', '',
          '| Bank | Prospective bank fault current A | Multiple of fuse rating |', '|---|---:|---:|']
    L += [f'| {b} | {v:.0f} | {bp["fault_multiple_of_rating"][b]:.1f} |' for b, v in bp['prospective_fault_a'].items()]
    L += ['', bp['note'], '', '## Pre-charge and service discharge (one pulse resistor)', '',
          f'{pc["resistor_ohm"]:.1f} Ω holds start-up supply current at {pc["supply_current_a"]:.1f} A against the '
          f'{pc["supply_limit_a"]:.1f} A rating, peak {pc["peak_power_w"]:.0f} W. The bypass closes when the bus-to-bank difference is small enough that top-off current '
          f'stays under the supply margin ({pc["rows"][0]["bypass_close_delta_v"]:.2f} V fresh), and the drive is enabled only after closure '
          '([sequence simulation](precharge.md)). '
          + pc['note'], '',
          '| Bank | C F | τ s | To bypass = drive enable s | Pre-charge energy J | Bypass inrush A | Service discharge to '
          f'{a["service_safe_v"]} V s | Discharge energy J | Bleed-only τ h |', '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    L += [f'| {x["bank"]} | {x["bank_capacitance_f"]:.2f} | {x["tau_s"]:.0f} | {x["time_to_enable_s"]:.0f} | '
          f'{x["precharge_energy_j"]:.0f} | {x["bypass_inrush_a"]:.1f} | {x["discharge_time_s"]:.0f} | {x["discharge_energy_j"]:.0f} | '
          f'{x["bleed_only_tau_h"]:.1f} |' for x in pc['rows']]
    L += ['', 'Without an active discharge the 10 kΩ bleed alone leaves the bank charged for hours; service discharge is required.', '',
          '## Cell balancing', '',
          f'Passive balancing: {bal["resistor_ohm"]:.0f} Ω per cell ({1000*bal["current_a"]:.0f} mA = {a["balancing_current_ratio"]} × an '
          f'assumed {1000*a["cell_leakage_a"]:.1f} mA leakage spread), {bal["loss_bank_w"]:.2f} W for the bank, self-discharge τ '
          f'{bal["self_discharge_tau_h"]:.1f} h. ' + bal['note'], '',
          '| Check | Worst cell V | Limit V | Outcome |', '|---|---:|---:|---|',
          f'| Simulated maximum bank voltage | {bal["worst_cell_at_max_bank_v"]:.3f} | {bal["cell_monitor_trip_v"]} cell monitor trip | {ok(bal["normal_below_monitor"])} |',
          f'| At the bus trip | {bal["worst_cell_at_trip_v"]:.3f} | {bal["cell_rated_v"]} rated | {ok(bal["trip_below_rating"])} |', '',
          f'Capacitance spread {100*a["capacitance_spread_fraction"]:.0f}% below the string mean (the documented initial minimum). '
          'This replaces the earlier 1.05 worst-cell factor.', '',
          '## Dump-path monitoring', '',
          f'Peak dump current {dm["peak_current_a"]:.1f} A; a {dm["shunt_ohm"]*1000:.0f} mΩ shunt gives {dm["shunt_signal_mv"]:.0f} mV and '
          f'{dm["shunt_peak_w"]:.1f} W peak. In the fresh-bank dump-failure case the bus reached {dm["fresh_dump_failure_bus_max_v"]:.1f} V '
          f'without a trip. Rule: {dm["rule"]}', '',
          '## Bank duty limit', '',
          f'If aged-cell fast reversal repeated continuously, the cells would reach about {duty["continuous_fast_reversal_c"]["r2_aged"]:.0f} °C '
          f'(case maximum {duty["case_max_c"]} °C). {duty["rule"]}', '',
          '## Sources not read', '']
    L += [f'- {s["item"]}: {s["status"]} ({s["source"]})' for s in r['sources_not_read']]
    L += ['', 'Reproduce: `make power-path` (after `make r4-candidate`).', '']
    path.write_text('\n'.join(L))


if __name__ == '__main__':
    run()
