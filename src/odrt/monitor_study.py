"""Dump-monitor measurement study on R4, reported separately (make monitor-study).

Every R4 case, fresh and aged, under measurement-error corners and seeded noise
(configs/monitor_study.yaml). A false trip is a dump_fault latch in any case
without a dump_failure fault; detection is judged on the dump-failure cases.
The R4 candidate uses the gate rule with ideal measurements; the other rules are
kept here as the evidence for that decision.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from odrt.config import ConfigError, load_yaml
from odrt.coupled import simulate
from odrt.project import load_inputs
from odrt.r2_candidate import BANKS, load_r4, model_factory, r4_fingerprint


def study_fingerprint(root=Path('.')):
    root = Path(root); h = hashlib.sha256(r4_fingerprint(root).encode())
    h.update((root/'configs/monitor_study.yaml').read_bytes()+Path(__file__).read_bytes())
    return h.hexdigest()


def corner_config(cfg, spec, corner):
    """Plant tolerances go into cfg['power']; the supervisor keeps the nominal values as its assumptions."""
    c = copy.deepcopy(cfg); p = c['power']
    unknown = set(corner)-{'measurement', 'plant'}
    if unknown: raise ConfigError(f'monitor corner: unknown sections {sorted(unknown)}')
    c['dump_monitor']['assumed'] = {k: p[k] for k in ('dump_start_v', 'dump_full_v', 'dump_resistance_ohm')}
    plant = corner.get('plant', {})
    if set(plant)-{'threshold_offset_v', 'resistance_factor'}: raise ConfigError('monitor corner: unknown plant keys')
    p['dump_start_v'] += plant.get('threshold_offset_v', 0); p['dump_full_v'] += plant.get('threshold_offset_v', 0)
    p['dump_resistance_ohm'] *= plant.get('resistance_factor', 1)
    if 'measurement' in corner:
        m = dict(corner['measurement'])
        if set(m) != {'current_gain', 'current_offset_a', 'voltage_gain', 'voltage_offset_v'}:
            raise ConfigError('monitor corner: measurement needs gain and offset for current and voltage')
        c['dump_monitor']['measurement'] = dict(m, filter_s=spec['filter_s'], noise=dict(spec['noise']))
    if not p['dump_full_v'] < c['dump_monitor']['backup_bus_v'] < p['trip_v']:
        raise ConfigError('monitor corner moves the chopper past the backup threshold')
    return c


def _job(args):
    key, cfg, parts, scenario, defaults, stroke, case = args
    try:
        value = simulate(cfg, parts, scenario, defaults, stroke, case, model_factory=model_factory(cfg))
    except RuntimeError as error:
        return key, {'solver_failure': str(error)}
    m, s = value['metrics'], value['signals']; out = {'energy_residual_fraction': m['energy_residual_fraction'],
                                                    'maximum_bus_v': m['maximum_bus_v'], 'units': []}
    for i in range(case['units']):
        p = f'unit_{i}.'
        err = s[p+'dump_measured_a']-s[p+'dump_true_a']
        out['units'].append({'trip_reason': m[p+'trip_reason'], 'trip_time_s': m[p+'trip_time_s'],
                             'max_timer_s': float(s[p+'dump_timer_s'].max()),
                             'condition_fraction': float(s[p+'dump_monitor_condition'].mean()),
                             'current_error_rms_a': float(np.sqrt(np.mean(err**2))),
                             'bus_error_max_v': float(np.abs(s[p+'bus_measured_v']-s[p+'bus_v']).max())})
    return key, out


def run(root=Path('.'), jobs=None):
    root = Path(root); initial = study_fingerprint(root); spec = load_yaml(root/'configs/monitor_study.yaml')
    inputs = load_inputs(root); cfg, parts, banks, *_ = load_r4(root); stroke = inputs.envelope.max_usable_stroke_m
    tasks = []
    for rule, rule_cfg in spec['rules'].items():
        if set(rule_cfg)-{'duty_source', 'estimate_margin_v'}: raise ConfigError(f'monitor rule {rule}: unknown keys')
        for corner, changes in spec['corners'].items():
            c = corner_config(cfg, spec, changes); c['dump_monitor'].update(rule_cfg)
            for bank in spec['banks']:
                q = copy.deepcopy(parts); q['r2_cell'] = {'values': banks[bank]}
                for case in cfg['cases']:
                    tasks.append(((f'{rule}:{corner}', bank, case['name']), c, q, inputs.scenarios[case['scenario']],
                                  inputs.defaults, stroke, case))
    tasks.sort(key=lambda t: 'endurance' not in t[0][2])
    workers = jobs or int(os.environ.get('JOBS', 0)) or os.cpu_count()
    print(f'monitor study: {len(tasks)} simulations on {workers} workers', flush=True)
    faults = {c['name']: c for c in cfg['cases']}
    results = {f'{rule}:{corner}': {bank: {} for bank in spec['banks']} for rule in spec['rules'] for corner in spec['corners']}
    with ProcessPoolExecutor(workers) as pool:
        for done, ((corner, bank, name), m) in enumerate(pool.map(_job, tasks, chunksize=1), 1):
            results[corner][bank][name] = m
            print(f'  [{done}/{len(tasks)}] {corner}/{bank}/{name}: '
                  f'{m.get("solver_failure") or [u["trip_reason"] for u in m["units"]]}', flush=True)
    summary = {}
    for corner, by_bank in results.items():
        for bank, cases in by_bank.items():
            false, detect, worst = [], {}, (0., None)
            for name, m in cases.items():
                if 'solver_failure' in m: continue
                dump_case = faults[name]['fault'] == 'dump_failure'
                for i, u in enumerate(m['units']):
                    if dump_case and i == 0:
                        detect[name] = {'trip_reason': u['trip_reason'], 'latency_s': None if u['trip_time_s'] is None
                                        else u['trip_time_s']-faults[name]['fault_time_s'], 'bus_max_v': m['maximum_bus_v']}
                    elif u['trip_reason'] == 'dump_fault':
                        false.append(f'{name}/unit_{i}')
                    elif u['max_timer_s'] > worst[0]:
                        worst = (u['max_timer_s'], f'{name}/unit_{i}')
            summary[f'{corner}/{bank}'] = {'false_trips': false, 'detection': detect,
                                            'max_timer_without_trip_s': worst[0], 'max_timer_case': worst[1],
                                            'solver_failures': sorted(n for n, m in cases.items() if 'solver_failure' in m)}
    if study_fingerprint(root) != initial:
        raise ConfigError('monitor study inputs changed during run; refusing publication')
    report = {'fingerprint': initial, 'assessment': 'study only; R4 uses the gate rule (owner decision 2026-11-03)', 'corners': spec['corners'], 'rules': spec['rules'],
              'detection_s': cfg['dump_monitor']['detection_s'], 'summary': summary, 'results': results}
    (root/'reports/monitor_study.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    write_report(report, spec, root/'reports/monitor_study.md')
    return report


def write_report(r, spec, path):
    L = ['# Dump-monitor measurement study (R4)', '', f'Fingerprint: `{r["fingerprint"]}`', '',
         '**Study only. The R4 candidate uses the gate rule with ideal measurements (owner decision 2026-11-03).** ' + spec['purpose'], '',
         '| Rule : corner / bank | False trips | Dump failure: reason, latency s, bus max V | Dump failure (coordinated) | Closest non-trip timer s |',
         '|---|---|---|---|---|']
    d = r['detection_s']
    for key, s in r['summary'].items():
        cell = lambda n: ('—' if n not in s['detection'] else
                          f'{s["detection"][n]["trip_reason"] or "none"}, '
                          f'{"—" if s["detection"][n]["latency_s"] is None else format(s["detection"][n]["latency_s"], ".2f")}, '
                          f'{s["detection"][n]["bus_max_v"]:.2f}')
        false = ', '.join(s['false_trips']) or 'none'
        if s['solver_failures']: false += f' (solver failures: {", ".join(s["solver_failures"])})'
        L.append(f'| {key} | {false} | {cell("paired_dump_failure")} | {cell("paired_dump_failure_coordinated")} | '
                 f'{s["max_timer_without_trip_s"]:.3f} of {d} ({s["max_timer_case"] or "—"}) |')
    L += ['', f'A trip needs the condition held for {d} s. "Closest non-trip timer" is the longest the condition persisted in any case '
          'that did not trip on it (dump-failure units excluded): the margin against nuisance trips.', '', '## Corners', '']
    for name, c in r['corners'].items():
        L.append(f'- **{name}**: ' + ('; '.join(f'{k}: {v}' for k, v in c.items()) or 'ideal measurements, nominal plant'))
    L += [f'- Noise (all non-ideal corners): {spec["noise"]}; filter {spec["filter_s"]} s.', '', '## Rules', '']
    L += [f'- **{name}**: ' + '; '.join(f'{k}: {v}' for k, v in c.items()) for name, c in r['rules'].items()]
    L += ['', '## Notes', '']
    L += ['- '+n for n in spec['notes']] + ['', 'Reproduce: `make monitor-study`.', '']
    path.write_text('\n'.join(L))


if __name__ == '__main__':
    run()
