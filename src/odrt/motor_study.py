"""Motor study on R4, reported separately (make motor-study).

Runs the R4 plant with candidate motors from data/motor_candidates.yaml across
belt ratios, drive current limits and heat-path bounds (configs/motor_study.yaml).
Results are proposals; the R4 candidate keeps the RO100. Failures are retained.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from odrt.config import ConfigError, load_yaml, number
from odrt.coupled import OPTIONAL_KEYS, assess_case, simulate
from odrt.engineering import load_engineering
from odrt.project import load_inputs
from odrt.r2_candidate import load_r4, model_factory, r4_fingerprint

SECTIONS = {'motor', 'reference', 'control', 'thermal_scale'}
MOTOR_FIELDS = ('kt_nm_per_a', 'km_nm_per_sqrt_w', 'torque_peak_nm', 'inertia_kg_m2', 'pole_pairs')
THERMAL_SCALABLE = ('winding_to_housing_k_w', 'winding_capacity_j_k', 'housing_capacity_j_k')


def study_fingerprint(root=Path('.')):
    root = Path(root); h = hashlib.sha256(r4_fingerprint(root).encode())
    for rel in ('configs/motor_study.yaml', 'data/motor_candidates.yaml'):
        h.update(rel.encode()+b'\0'+(root/rel).read_bytes()+b'\0')
    h.update(Path(__file__).read_bytes())
    return h.hexdigest()


def load_candidates(root=Path('.')):
    data = load_yaml(Path(root)/'data/motor_candidates.yaml')
    for key, part in data.items():
        if not str(part.get('source', '')).startswith('https://'):
            raise ConfigError(f'motor candidate {key}: an https source is required')
        missing = set(MOTOR_FIELDS)-set(part.get('values', {}))
        if missing: raise ConfigError(f'motor candidate {key}: missing model values {sorted(missing)}')
        for field, value in part['values'].items():
            number(value, f'{key}.{field}', minimum=0, exclusive_minimum=True)
    return data


def apply_variant(cfg, parts, candidates, changes):
    """Return (cfg, parts) for one variant; unknown sections and keys fail."""
    cfg = copy.deepcopy(cfg); parts = copy.deepcopy(parts)
    unknown = set(changes)-SECTIONS
    if unknown: raise ConfigError(f'motor variant: unknown sections {sorted(unknown)}')
    if 'motor' in changes:
        key = changes['motor']
        if key not in candidates: raise ConfigError(f'motor variant: unknown motor {key!r}')
        parts[key] = {'values': dict(candidates[key]['values'])}
        cfg['reference']['motor'] = key
    for section in ('reference', 'control'):
        values = changes.get(section, {})
        bad = set(values)-(set(cfg[section]) | set(OPTIONAL_KEYS.get(section, ())))
        if bad: raise ConfigError(f'motor variant: unknown {section} keys {sorted(bad)}')
        cfg[section].update(values)
    for field, scale in changes.get('thermal_scale', {}).items():
        if field not in THERMAL_SCALABLE: raise ConfigError(f'motor variant: thermal_scale cannot change {field}')
        cfg['thermal'][field] *= number(scale, f'thermal_scale.{field}', minimum=0, exclusive_minimum=True)
    return cfg, parts


def _job(args):
    key, cfg, parts, scenario, defaults, stroke, case, criteria = args
    try:
        value = simulate(cfg, parts, scenario, defaults, stroke, case, model_factory=model_factory(cfg))
    except RuntimeError as error:
        return key, {'solver_failure': str(error), 'numerical_valid': False}
    m, s = value['metrics'], value['signals']
    m['assessment'] = assess_case(m, cfg, parts, case, criteria)
    m['numerical_valid'] = bool(m['energy_residual_fraction'] <= criteria['energy_residual_fraction_max']['value'])
    keep = ('assessment', 'numerical_valid', 'energy_residual_fraction', 'maximum_bus_v', 'duration_s')
    out = {k: m[k] for k in keep if k in m}
    for i in range(case['units']):
        p = f'unit_{i}.'
        out.update({k: m[k] for k in m if k.startswith(p)})
    return key, out


def motor_summary(parts, cfg):
    """Static figures for the report: no-load speed at nominal bus and the torque the current limit allows."""
    motor = parts[cfg['reference']['motor']]['values']; drive = parts[cfg['reference']['drive']]['values']
    vmax = drive['modulation_utilization']*cfg['power']['nominal_v']
    limit_a = min(motor['torque_peak_nm']/motor['kt_nm_per_a'], cfg['control']['current_limit_a'])
    g = cfg['reference']['ratio']
    return {'motor': cfg['reference']['motor'], 'ratio': g, 'current_limit_a': cfg['control']['current_limit_a'],
            'motor_torque_limit_nm': limit_a*motor['kt_nm_per_a'], 'drum_torque_limit_nm': limit_a*motor['kt_nm_per_a']*g,
            'model_no_load_motor_rpm': vmax/motor['kt_nm_per_a']*60/(2*math.pi),
            'model_no_load_drum_rpm': vmax/motor['kt_nm_per_a']*60/(2*math.pi)/g,
            'reflected_motor_inertia_kg_m2': g*g*motor['inertia_kg_m2'],
            'winding_to_housing_k_w': cfg['thermal']['winding_to_housing_k_w']}


def run(root=Path('.'), jobs=None):
    root = Path(root); initial = study_fingerprint(root); spec = load_yaml(root/'configs/motor_study.yaml')
    inputs = load_inputs(root); cfg, parts, banks, *_ = load_r4(root); candidates = load_candidates(root)
    criteria = load_engineering(root)[0]; stroke = inputs.envelope.max_usable_stroke_m
    cases = {c['name']: c for c in cfg['cases']}
    unknown = set(spec['cases'])-set(cases)
    if unknown: raise ConfigError(f'motor study: unknown cases {sorted(unknown)}')
    tasks, summaries = [], {}
    for name, changes in spec['variants'].items():
        c, q = apply_variant(cfg, parts, candidates, changes); summaries[name] = motor_summary(q, c)
        for bank in spec['banks']:
            qb = copy.deepcopy(q); qb['r2_cell'] = {'values': banks[bank]}
            for case in spec['cases']:
                k = cases[case]
                tasks.append(((name, bank, case), c, qb, inputs.scenarios[k['scenario']], inputs.defaults, stroke, k, criteria))
    tasks.sort(key=lambda t: 'endurance' not in t[0][2])
    workers = jobs or int(os.environ.get('JOBS', 0)) or os.cpu_count()
    print(f'motor study: {len(tasks)} simulations on {workers} workers', flush=True)
    results = {name: {bank: {} for bank in spec['banks']} for name in spec['variants']}
    with ProcessPoolExecutor(workers) as pool:
        for done, ((name, bank, case), m) in enumerate(pool.map(_job, tasks, chunksize=1), 1):
            results[name][bank][case] = m
            status = m.get('solver_failure') or f'tracking {100*m["unit_0.tracking_fraction"]:.2f}%'
            print(f'  [{done}/{len(tasks)}] {name}/{bank}/{case}: {status}', flush=True)
    if study_fingerprint(root) != initial:
        raise ConfigError('motor study inputs changed during run; refusing publication')
    report = {'fingerprint': initial, 'assessment': 'study only; R4 keeps the RO100', 'variants': spec['variants'],
              'summary': summaries, 'results': results}
    (root/'reports/motor_study.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    write_report(report, spec, root/'reports/motor_study.md')
    return report


def _units(m):
    return range(len(m['assessment']))


def _cell(m):
    if 'solver_failure' in m: return 'SOLVER FAILURE'
    worst = max(_units(m), key=lambda i: m[f'unit_{i}.tracking_fraction'])
    trip = ' trip' if any(m[f'unit_{i}.trip_latched'] for i in _units(m)) else ''
    flag = ' ✗' if any(row['failed_checks'] for row in m['assessment']) else ''
    return f'{100*m[f"unit_{worst}.tracking_fraction"]:.1f}%{trip}{flag}'


def write_report(r, spec, path):
    cases, banks = spec['cases'], spec['banks']
    L = ['# Motor study (R4)', '', f'Fingerprint: `{r["fingerprint"]}`', '',
         '**Study only. The R4 candidate keeps the RO100.** ' + spec['purpose'], '',
         '## Variants at a glance', '',
         '| Variant | Motor | Ratio | Current limit A | Motor / drum torque limit N·m | Model no-load drum rpm at 52 V | Reflected motor inertia kg·m² | Winding–housing K/W |',
         '|---|---|---:|---:|---:|---:|---:|---:|']
    for name, s in r['summary'].items():
        L.append(f'| {name} | {s["motor"]} | {s["ratio"]:g} | {s["current_limit_a"]:g} | {s["motor_torque_limit_nm"]:.1f} / '
                 f'{s["drum_torque_limit_nm"]:.0f} | {s["model_no_load_drum_rpm"]:.0f} | {s["reflected_motor_inertia_kg_m2"]:.4f} | '
                 f'{s["winding_to_housing_k_w"]:.2f} |')
    for bank in banks:
        L += ['', f'## Tracking, {bank} bank', '', '| Variant | ' + ' | '.join(cases) + ' |', '|---|' + '---:|'*len(cases)]
        for name, by_bank in r['results'].items():
            L.append(f'| {name} | ' + ' | '.join(_cell(by_bank[bank][c]) for c in cases) + ' |')
    L += ['', 'Cells: settled tracking RMS fraction of the worst unit; `trip` marks a latched protective trip; '
          '✗ marks any failed comparison (listed below and in `motor_study.json`).', '',
          '## Limits reached, unit 0', '',
          '| Variant | Bank | Case | Voltage-limited time | Max current A | Max winding °C | Max electrical Hz | Min bus V | Failed checks |',
          '|---|---|---|---:|---:|---:|---:|---:|---|']
    for name, by_bank in r['results'].items():
        for bank in banks:
            for case in cases:
                m = by_bank[bank][case]
                if 'solver_failure' in m:
                    L.append(f'| {name} | {bank} | {case} | solver failure | | | | | |'); continue
                u = 'unit_0.'
                failed = sorted({f for row in m['assessment'] for f in row['failed_checks']})
                L.append(f'| {name} | {bank} | {case} | {100*m[u+"voltage_limited_fraction"]:.0f}% | {m[u+"max_current_a"]:.1f} | '
                         f'{m[u+"max_winding_c"]:.1f} | {m[u+"max_electrical_hz"]:.0f} | {m[u+"min_bus_v"]:.1f} | '
                         f'{"; ".join(failed) or "—"} |')
    changes = lambda v: '; '.join(f'{k}: {v[k]}' for k in v) or 'R4 candidate (RO100, 5:1, 50 A)'
    L += ['', '## Variants', ''] + [f'- **{n}**: {changes(v)}' for n, v in r['variants'].items()]
    L += ['', '## Notes', ''] + ['- '+n for n in spec['notes']]
    L += ['', 'Reproduce: `make motor-study`.', '']
    path.write_text('\n'.join(L))


if __name__ == '__main__':
    run()
