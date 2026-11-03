"""Fast-motion study on R3 with controller C1, reported separately.

Run python -m odrt.fast_motion_study (JOBS=n limits workers). It attributes
tracking error to back-EMF/bus voltage saturation and tests feedforward,
bank-ESR, ratio and storage-topology levers. Results are proposals; nothing
here changes the reference or the R3/C1 candidate. Failures are retained.
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
from odrt.coupled import OPTIONAL_KEYS, assess_case, build_model, simulate
from odrt.engineering import load_engineering
from odrt.project import load_inputs
from odrt.r2_candidate import load_r3c, r3c_fingerprint

TOPOLOGIES = ('clamp', 'bidirectional')
SENSITIVITIES = ('esr_scale', 'capacitance_scale', 'km_scale', 'inertia_scale')


def study_fingerprint(root=Path('.')):
    root = Path(root); h = hashlib.sha256(r3c_fingerprint(root).encode())
    h.update((root/'configs/fast_motion_study.yaml').read_bytes()+Path(__file__).read_bytes())
    return h.hexdigest()


def apply_variant(cfg, parts, changes):
    """Return (cfg, parts, sensitivity, topology) for one variant; unknown keys fail."""
    cfg = copy.deepcopy(cfg); parts = copy.deepcopy(parts)
    unknown = set(changes)-{'control', 'reference', 'power', 'sensitivity', 'topology'}
    if unknown: raise ConfigError(f'fast-motion variant: unknown sections {sorted(unknown)}')
    for section in ('control', 'reference', 'power'):
        values = changes.get(section, {})
        allowed = set(cfg[section]) | set(OPTIONAL_KEYS.get(section, ()))
        bad = set(values)-allowed
        if bad: raise ConfigError(f'fast-motion variant: unknown {section} keys {sorted(bad)}')
        cfg[section].update(values)
    sensitivity = dict(changes.get('sensitivity', {}))
    bad = set(sensitivity)-set(SENSITIVITIES)
    if bad: raise ConfigError(f'fast-motion variant: unknown sensitivity keys {sorted(bad)}')
    topology = changes.get('topology', 'clamp')
    if topology not in TOPOLOGIES: raise ConfigError(f'fast-motion variant: unknown topology {topology!r}')
    return cfg, parts, sensitivity, topology


def factory(topology):
    from odrt.frame_thermal import frame_factory
    from odrt.upstream_buffer import build_upstream_model
    return frame_factory(build_upstream_model if topology == 'clamp' else build_model)


def _job(args):
    key, cfg, parts, topology, scenario, defaults, stroke, case, sensitivity, criteria = args
    try:
        value = simulate(cfg, parts, scenario, defaults, stroke, case, model_factory=factory(topology), **sensitivity)
    except RuntimeError as error:
        return key, {'solver_failure': str(error), 'numerical_valid': False}
    m, s = value['metrics'], value['signals']; t = s['t']
    for i in range(case['units']):
        p = f'unit_{i}.'
        m[p+'dump_mean_w'] = float(np.trapz(s[p+'dump_w'], t)/t[-1])
        m[p+'min_capacitor_v'] = float(s[p+'capacitor_v'].min())
    m['assessment'] = assess_case(m, cfg, parts, case, criteria)
    m['numerical_valid'] = bool(m['energy_residual_fraction'] <= criteria['energy_residual_fraction_max']['value']
                                and all(np.isfinite(v).all() for v in s.values()))
    return key, m


def run(root=Path('.'), jobs=None):
    root = Path(root); initial = study_fingerprint(root); spec = load_yaml(root/'configs/fast_motion_study.yaml')
    inputs = load_inputs(root); cfg, parts, banks, derived, _, _ = load_r3c(root)
    criteria = load_engineering(root)[0]; stroke = inputs.envelope.max_usable_stroke_m
    cases = {c['name']: c for c in cfg['cases']}
    unknown = set(spec['cases'])-set(cases)
    if unknown: raise ConfigError(f'fast-motion study: unknown cases {sorted(unknown)}')
    tasks = []
    for name, changes in spec['variants'].items():
        c, q, sensitivity, topology = apply_variant(cfg, parts, changes)
        for bank in spec['banks']:
            qb = copy.deepcopy(q); qb['r2_cell'] = {'values': banks[bank]}
            for case in spec['cases']:
                k = cases[case]
                tasks.append(((name, bank, case), c, qb, topology, inputs.scenarios[k['scenario']],
                              inputs.defaults, stroke, k, sensitivity, criteria))
    tasks.sort(key=lambda t: 'endurance' not in t[0][2])
    workers = jobs or int(os.environ.get('JOBS', 0)) or os.cpu_count()
    print(f'fast-motion study: {len(tasks)} simulations on {workers} workers', flush=True)
    results = {name: {bank: {} for bank in spec['banks']} for name in spec['variants']}
    with ProcessPoolExecutor(workers) as pool:
        for done, ((name, bank, case), m) in enumerate(pool.map(_job, tasks, chunksize=1), 1):
            results[name][bank][case] = m
            status = m.get('solver_failure') or f'tracking {100*m["unit_0.tracking_fraction"]:.2f}%'
            print(f'  [{done}/{len(tasks)}] {name}/{bank}/{case}: {status}', flush=True)
    if study_fingerprint(root) != initial:
        raise ConfigError('fast-motion study inputs changed during run; refusing publication')
    report = {'fingerprint': initial, 'assessment': 'study only; reference and R3/C1 unchanged',
              'controller': derived['controller'], 'variants': spec['variants'], 'results': results}
    (root/'reports/fast_motion_study.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    write_report(report, spec, root/'reports/fast_motion_study.md')
    return report


def _cell(m):
    if 'solver_failure' in m: return 'SOLVER FAILURE'
    worst = max(range(len(m['assessment'])), key=lambda i: m[f'unit_{i}.tracking_fraction'])
    u = f'unit_{worst}.'
    trip = ' trip' if any(m[f'unit_{i}.trip_latched'] for i in range(len(m['assessment']))) else ''
    flag = ' ✗' if any(row['failed_checks'] for row in m['assessment']) else ''
    return f'{100*m[u+"tracking_fraction"]:.1f}%{trip}{flag}'


def write_report(r, spec, path):
    cases, banks = spec['cases'], spec['banks']
    lines = ['# Fast-motion study (R3 + C1)', '', f'Fingerprint: `{r["fingerprint"]}`', '',
             '**Study only. The reference controller and the R3/C1 candidate are unchanged.** ' + spec['purpose'], '']
    for bank in banks:
        lines += [f'## Tracking, {bank} bank', '', '| Variant | ' + ' | '.join(cases) + ' |',
                  '|---|' + '---:|'*len(cases)]
        for name, by_bank in r['results'].items():
            lines.append(f'| {name} | ' + ' | '.join(_cell(by_bank[bank][c]) for c in cases) + ' |')
        lines += ['', 'Cells: settled tracking RMS fraction of the worst unit; `trip` marks a latched protective trip; '
                  '✗ marks any failed comparison (details in `fast_motion_study.json`).', '']
    lines += ['## Voltage saturation and energy, unit 0', '',
              '| Variant | Bank | Case | Voltage-limited time | Voltage-limited error share | Min bus V | Mean dump W | Max winding °C | Max electrical Hz |',
              '|---|---|---|---:|---:|---:|---:|---:|---:|']
    for name, by_bank in r['results'].items():
        for bank in banks:
            for case in ('single_fast_full', 'single_stroke_full'):
                m = by_bank[bank].get(case)
                if m is None or 'solver_failure' in m: continue
                u = 'unit_0.'
                share = m[u+'voltage_limited_error_share']
                lines.append(f'| {name} | {bank} | {case} | {100*m[u+"voltage_limited_fraction"]:.0f}% | '
                             f'{"–" if share is None else f"{100*share:.0f}%"} | {m[u+"min_bus_v"]:.1f} | '
                             f'{m[u+"dump_mean_w"]:.0f} | {m[u+"max_winding_c"]:.1f} | {m[u+"max_electrical_hz"]:.0f} |')
    changes = lambda v: '; '.join(f'{k}: {v[k]}' for k in v) or 'R3 + C1'
    lines += ['', '## Variants', ''] + [f'- **{n}**: {changes(v)}' for n, v in r['variants'].items()]
    lines += ['', '## Notes', ''] + ['- '+n for n in spec['notes']]
    lines += ['', 'Reproduce: `make fast-study`.', '']
    path.write_text('\n'.join(lines))


if __name__ == '__main__':
    run()
