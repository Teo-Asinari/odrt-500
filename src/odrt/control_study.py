"""Controller study on the R3 machine, reported separately from the candidate.

Run python -m odrt.control_study (JOBS=n limits workers). Each variant changes
only the control configuration; plant, power, thermal and fault policy are R3.
Gains that pass here are proposals: robustness to the human-arm model, cable
stiffness and sensor noise must be shown before any variant replaces the
reference controller. Failures are retained.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from odrt.config import ConfigError, load_yaml
from odrt.coupled import OPTIONAL_KEYS
from odrt.engineering import load_engineering
from odrt.project import load_inputs
from odrt.r2_candidate import _job, load_r3, r3_fingerprint


def study_fingerprint(root=Path('.')):
    root = Path(root); h = hashlib.sha256(r3_fingerprint(root).encode())
    h.update((root/'configs/control_study.yaml').read_bytes()+Path(__file__).read_bytes())
    return h.hexdigest()


def run(root=Path('.'), jobs=None):
    root = Path(root); initial = study_fingerprint(root); spec = load_yaml(root/'configs/control_study.yaml')
    inputs = load_inputs(root); cfg, parts, variants, _, _, _ = load_r3(root)
    criteria = load_engineering(root)[0]; stroke = inputs.envelope.max_usable_stroke_m
    cases = {c['name']: c for c in cfg['cases']}
    unknown = set(spec['cases'])-set(cases)
    if unknown: raise ConfigError(f'control study: unknown cases {sorted(unknown)}')
    tasks = []
    for name, changes in spec['variants'].items():
        unknown = set(changes)-set(cfg['control'])-set(OPTIONAL_KEYS['control'])
        if unknown: raise ConfigError(f'control variant {name}: unknown control keys {sorted(unknown)}')
        c, q = copy.deepcopy(cfg), copy.deepcopy(parts); c['control'].update(changes)
        q['r2_cell'] = {'values': variants[spec['bank']]}
        for case in spec['cases']:
            k = cases[case]
            tasks.append(('case', (name, case), c, q, inputs.scenarios[k['scenario']], inputs.defaults, stroke, k, {}, criteria, None))
    tasks.sort(key=lambda t: 'endurance' not in t[1][1])
    workers = jobs or int(os.environ.get('JOBS', 0)) or os.cpu_count()
    print(f'control study: {len(tasks)} simulations on {workers} workers', flush=True)
    results = {name: {} for name in spec['variants']}
    with ProcessPoolExecutor(workers) as pool:
        for done, (_, (name, case), m) in enumerate(pool.map(_job, tasks, chunksize=1), 1):
            results[name][case] = m
            status = m.get('solver_failure') or f'tracking {100*m["unit_0.tracking_fraction"]:.2f}%'
            print(f'  [{done}/{len(tasks)}] {name}/{case}: {status}', flush=True)
    if study_fingerprint(root) != initial:
        raise ConfigError('control study inputs changed during run; refusing publication')
    report = {'fingerprint': initial, 'assessment': 'study only; reference controller unchanged',
              'bank': spec['bank'], 'variants': spec['variants'], 'results': results}
    (root/'reports/control_study.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    write_report(report, spec, root/'reports/control_study.md')
    return report


def write_report(r, spec, path):
    failed = lambda m: sorted({f for row in m['assessment'] for f in row['failed_checks']})
    lines = ['# Controller study (R3 machine)', '', f'Fingerprint: `{r["fingerprint"]}`', '',
             '**Study only. The reference controller is unchanged.** ' + spec['purpose'], '',
             '| Variant | Changes | ' + ' | '.join(spec['cases']) + ' |', '|---|---|' + '---:|'*len(spec['cases'])]
    for name, cases in r['results'].items():
        cells = []
        for case in spec['cases']:
            m = cases[case]
            if 'solver_failure' in m: cells.append('SOLVER FAILURE'); continue
            flag = '' if not failed(m) else ' ✗'
            trip = f' ({m["unit_0.trip_reason"]})' if m['unit_0.trip_reason'] else ''
            cells.append(f'{100*m["unit_0.tracking_fraction"]:.2f}%{trip}{flag}')
        changes = ', '.join(f'{k}={v}' for k, v in r['variants'][name].items()) or 'reference'
        lines.append(f'| {name} | {changes} | ' + ' | '.join(cells) + ' |')
    lines += ['', 'Cells: settled tracking RMS fraction (trip reason); ✗ marks any failed comparison. '
              'Failed comparisons per cell are in `control_study.json`.', '']
    lines += ['- '+n for n in spec['notes']]
    lines += ['', 'Reproduce: `make control-study`.', '']
    path.write_text('\n'.join(lines))


if __name__ == '__main__':
    run()
