"""R2 candidate: the R2 CAD, 5:1 belt, TV bank and upstream clamp, full suite.

Run python -m odrt.r2_candidate (JOBS=n to limit worker processes). It joins
the separately screened R2 pieces into one simulated machine: CAD-derived
inertia and routing from r2_package, the ODrive Pro / EPP-500-54 / Regen Clamp
power path from revision_power, and the 20-cell TV bank. Controller gains are
unchanged. The R2 support screen is then repeated at the simulated loads.
Physical failures are retained; numerical convergence is not qualification.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from odrt.buffer_study import candidate_variants
from odrt.config import ConfigError, load_yaml
from odrt.coupled import assess_case, simulate
from odrt.engineering import load_engineering
from odrt.project import load_inputs

BANKS = ('r2_fresh', 'r2_aged')
REFINED = (('r2_fresh', 'single_heavy_full'), ('r2_fresh', 'paired_release_asymmetric'),
           ('r2_aged', 'left_power_loss_buffered_coordinated'), ('r2_aged', 'single_fast_full'))
SENSITIVITIES = (('nominal', {}, {}), ('half_airflow', {'air_to_room_w_k': .5}, {}), ('quarter_airflow', {'air_to_room_w_k': .25}, {}),
                 ('long_routing', {'routing_length_m': .15}, {}), ('low_km', {}, {'km_scale': .34/.53}),
                 ('warm_room', {}, {'ambient_offset_c': 15}), ('extra_inertia', {}, {'inertia_scale': 1.25}))


def r2_fingerprint(root=Path('.')):
    from odrt.r2_package import package_fingerprint
    from odrt.revision_power import revision_fingerprint
    root = Path(root); h = hashlib.sha256((revision_fingerprint(root)+package_fingerprint(root)).encode())
    for rel in ('data/revision_support.yaml', 'data/compact_structure.yaml'):
        h.update(rel.encode()+b'\0'+(root/rel).read_bytes()+b'\0')
    for module in ('r2_candidate.py', 'support_revision.py', 'compact_structure.py'):
        h.update(module.encode()+b'\0'+Path(__file__).with_name(module).read_bytes()+b'\0')
    return h.hexdigest()


def tv_variants(support):
    v = support['cell']['values']
    documented = {k: v[k] for k in ('capacitance_f', 'voltage_rated_v', 'esr_initial_max_ohm', 'capacitance_initial_min_fraction',
                                     'capacitance_end_life_fraction', 'esr_end_life_multiplier', 'mass_kg',
                                     'thermal_resistance_k_per_w', 'current_rms_15k_rise_a', 'case_max_c')}
    documented.update(diameter_max_mm=v['diameter_mm'], length_max_mm=v['length_mm'])
    c = support['cell']['assumptions']['thermal_capacity_j_per_k']
    variants = candidate_variants({'documented': documented,
                                   'assumptions': {'thermal_capacity_j_per_k': c, 'thermal_capacity_bounds_j_per_k': [c/2, 2*c]}})
    return {'r2_fresh': variants['compact_nominal'], 'r2_aged': variants['compact_aged']}


def load_r2(root=Path('.')):
    from odrt.r2_package import build
    from odrt.compact_package import inertia_properties
    from odrt.revision_power import load_revision
    root = Path(root)
    cfg, parts, _, derived, source = load_revision(root)
    support = load_yaml(root/'data/revision_support.yaml'); p = support['revision_proposal']
    objects, _, info = build(root)
    inertia = inertia_properties(objects, info, parts)
    cfg['reference']['ratio'] = p['wheel_teeth']/p['pinion_teeth']
    cfg['reference']['drum_inertia_kg_m2'] = inertia['equivalent_added_drum_inertia_kg_m2']
    cfg['mechanics']['routing_length_m'] = info['layout']['routing_length_m']
    cfg['power']['cell_series'] = p['cells_series']; cfg['power']['cell_parallel'] = 1
    cfg['control']['current_limit_a'] = p['motor_current_limit_a']
    cfg['reference']['capacitor'] = 'r2_cell'
    if abs(p['supply_setpoint_v']-cfg['power']['nominal_v']) > 1e-9:
        raise ConfigError('R2 supply setpoint disagrees with the power revision')
    derived = dict(derived, inertia=inertia, routing_basis=info['layout']['routing_basis'])
    return cfg, parts, tv_variants(support), derived, source, support


def model_factory(cfg):
    """Clamp topology (R2/R3: bank upstream of the one-way clamp) or bank on the drive bus (R4)."""
    from odrt.coupled import build_model
    from odrt.upstream_buffer import build_upstream_model
    base = build_model if cfg.get('power_topology') == 'bidirectional' else build_upstream_model
    if 'dump_monitor' in cfg:
        from odrt.dump_monitor import dump_monitor_factory
        base = dump_monitor_factory(base)
    if 'frame_thermal' in cfg:
        from odrt.frame_thermal import frame_factory
        return frame_factory(base)
    return base


def _job(args):
    """One simulation in a worker process; returns metrics and saves its trace."""
    kind, key, cfg, parts, scenario, defaults, stroke, case, kwargs, criteria, trace = args
    try:
        value = simulate(cfg, parts, scenario, defaults, stroke, case, model_factory=model_factory(cfg), **kwargs)
    except RuntimeError as error:
        return kind, key, {'solver_failure': str(error), 'numerical_valid': False}
    m, s = value['metrics'], value['signals']
    t = s['t']
    for i in range(case['units']):
        p = f'unit_{i}.'
        m[p+'max_capacitor_v'] = float(s[p+'capacitor_v'].max())
        m[p+'capacitor_rms_a'] = float(np.sqrt(np.trapz(s[p+'capacitor_current_a']**2, t)/t[-1]))
        m[p+'capacitor_peak_a'] = float(np.abs(s[p+'capacitor_current_a']).max())
        # Cycle-averaged dump current; the chopper's instantaneous current is bus V / dump resistance.
        m[p+'dump_average_peak_a'] = float((s[p+'dump_w']/np.maximum(s[p+'bus_v'], 1e-9)).max())
        m[p+'supply_peak_a'] = float((s[p+'supply_bus_w']/np.maximum(s[p+'bus_v'], 1e-9)).max())
    m['assessment'] = assess_case(m, cfg, parts, case, criteria)
    m['numerical_valid'] = bool(m['energy_residual_fraction'] <= criteria['energy_residual_fraction_max']['value']
                                and all(np.isfinite(v).all() for v in s.values()))
    if trace:
        np.savez_compressed(trace, **s); m['trace'] = trace
    return kind, key, m


def load_r3(root=Path('.')):
    """R2 plus the conducted motor-to-frame heat path (data/r3_thermal.yaml)."""
    cfg, parts, variants, derived, source, support = load_r2(root)
    spec = load_yaml(Path(root)/'data/r3_thermal.yaml')
    cfg['frame_thermal'] = dict(spec['nominal'])
    power = load_yaml(Path(root)/'data/r3_power.yaml')
    if not power['odrive_pro_dc_voltage']['min_v'] < power['proposal']['undervoltage_v'] < cfg['power']['nominal_v']:
        raise ConfigError('R3 undervoltage trip must lie between the drive minimum and the nominal bus')
    cfg['power']['undervoltage_v'] = power['proposal']['undervoltage_v']
    return cfg, parts, variants, dict(derived, frame_thermal=spec, r3_power=power), source, support


def r3_fingerprint(root=Path('.')):
    root = Path(root); h = hashlib.sha256(r2_fingerprint(root).encode())
    for rel in ('data/r3_thermal.yaml', 'data/r3_power.yaml'):
        h.update(rel.encode()+b'\0'+(root/rel).read_bytes()+b'\0')
    h.update(Path(__file__).with_name('frame_thermal.py').read_bytes())
    return h.hexdigest()


def load_r3c(root=Path('.')):
    """R3 with the controller variant proposed by configs/control_study.yaml."""
    cfg, parts, variants, derived, source, support = load_r3(root)
    study = load_yaml(Path(root)/'configs/control_study.yaml'); name = study['proposed']
    cfg['control'].update(study['variants'][name])
    return cfg, parts, variants, dict(derived, controller={'variant': name, 'changes': study['variants'][name]}), source, support


def r3c_fingerprint(root=Path('.')):
    root = Path(root); h = hashlib.sha256(r3_fingerprint(root).encode())
    h.update((root/'configs/control_study.yaml').read_bytes()+Path(__file__).with_name('coupled.py').read_bytes())
    return h.hexdigest()


def load_r4(root=Path('.')):
    """R3 + C1 with the bank on the drive bus (data/r4_power.yaml)."""
    cfg, parts, variants, derived, source, support = load_r3c(root)
    spec = load_yaml(Path(root)/'data/r4_power.yaml')
    if spec['proposal']['topology'] != 'bidirectional':
        raise ConfigError('R4 proposal must use the bidirectional topology')
    cfg['power_topology'] = 'bidirectional'
    trip = spec['proposal']['trip_v']
    clamp = load_yaml(Path(root)/'data/revision_components.yaml')['regen_clamp']['facts']['voltage_max_v']
    if not cfg['power']['dump_full_v'] < trip < clamp:
        raise ConfigError('R4 overvoltage trip must lie between full dump duty and the Regen Clamp maximum')
    cfg['power']['trip_v'] = trip
    if not cfg['power']['dump_full_v'] < spec['functions']['dump_monitor']['backup_bus_v'] < trip:
        raise ConfigError('R4 dump-monitor backup voltage must lie between full dump duty and the trip')
    cfg['dump_monitor'] = {k: spec['functions']['dump_monitor'][k] for k in ('detection_s', 'min_expected_a', 'measured_fraction', 'reset_s', 'backup_bus_v', 'duty_source')}
    return cfg, parts, variants, dict(derived, r4_power=spec), source, support


def r4_fingerprint(root=Path('.')):
    root = Path(root); h = hashlib.sha256(r3c_fingerprint(root).encode())
    h.update((root/'data/r4_power.yaml').read_bytes()+Path(__file__).with_name('dump_monitor.py').read_bytes())
    return h.hexdigest()


R4M_VARIANT = 'tbm_6'


def load_r4m(root=Path('.')):
    """R4 with the motor-study variant R4M_VARIANT (TBM2G-11526D at 6:1); study, not the R4 candidate."""
    from odrt.motor_study import apply_variant, load_candidates
    cfg, parts, variants, derived, source, support = load_r4(root)
    changes = load_yaml(Path(root)/'configs/motor_study.yaml')['variants'][R4M_VARIANT]
    cfg, parts = apply_variant(cfg, parts, load_candidates(root), changes)
    return cfg, parts, variants, dict(derived, motor_variant={'name': R4M_VARIANT, 'changes': changes}), source, support


def r4m_fingerprint(root=Path('.')):
    from odrt.motor_study import study_fingerprint
    return hashlib.sha256((study_fingerprint(root)+R4M_VARIANT).encode()).hexdigest()


# Controller variants on selected cases, reported with the uncertainties: (name, control changes, cases).
CONTROL_EXTRA = {'r4m': (('realisable_feedforward', {'inertia_feedforward': 0},
                          ('single_fast_full', 'single_stroke_full', 'paired_heavy_full', 'paired_asymmetric')),),
                 'r4': (('realisable_feedforward', {'inertia_feedforward': 0},
                         ('single_fast_full', 'single_stroke_full', 'paired_heavy_full', 'paired_asymmetric')),)}


def power_checks(spec, cases, parts, cfg, variants):
    """Bank-on-bus hardware checks at the simulated envelope (R4)."""
    f = spec['functions']; n = cfg['power']['cell_series']
    done = [m for b in cases.values() for m in b.values() if 'solver_failure' not in m]
    worst = lambda suffix: max(m[k] for m in done for k in m if k.endswith(suffix))
    vmax, rms, supply_a = worst('.max_capacitor_v'), worst('.capacitor_rms_a'), worst('.supply_peak_a')
    # The cell's RMS rating is continuous; one set is a transient. Report both readings.
    rms_rows = sorted(((m[k], bank, case, m[k.replace('capacitor_rms_a', 'max_capacitor_c')], m['duration_s'])
                       for bank, b in cases.items() for case, m in b.items() if 'solver_failure' not in m
                       for k in m if k.endswith('.capacitor_rms_a')), reverse=True)
    top = rms_rows[0]; ambient = cfg['thermal']['ambient_c']
    continuous = {bank: ambient + top[0]**2*variants[bank]['esr_initial_max_ohm']*variants[bank]['thermal_resistance_k_per_w']
                  for bank in BANKS}
    cell = variants['r2_fresh']; rated = cell['voltage_rated_v']; factor = f['cell_voltage']['worst_cell_factor']
    supply = parts[cfg['reference']['supply']]['values']; v0 = cfg['power']['nominal_v']
    limit_a = supply['power_forced_air_w']/v0
    precharge = [{'bank': bank, 'bank_capacitance_f': variants[bank]['capacitance_f']/n,
                  'precharge_s_at_supply_limit': variants[bank]['capacitance_f']/n*v0/limit_a,
                  'precharge_energy_j': .5*variants[bank]['capacitance_f']/n*v0*v0} for bank in BANKS]
    return {'max_bank_v': vmax, 'worst_cell_v': vmax/n*factor, 'cell_rated_v': rated,
            'cell_voltage_pass': vmax/n*factor < rated, 'trip_worst_cell_v': cfg['power']['trip_v']/n*factor,
            'max_bank_rms_a': rms, 'cell_rms_rating_a': cell['current_rms_15k_rise_a'],
            'rms_pass': rms < cell['current_rms_15k_rise_a'], 'rms_worst_case': {'bank': top[1], 'case': top[2],
            'set_duration_s': top[4], 'set_max_cell_c': top[3]},
            'rms_exceeding_cases': sorted({f'{b}/{c}' for a, b, c, _, _ in rms_rows if a >= cell['current_rms_15k_rise_a']}),
            'continuous_repetition_cell_c': continuous, 'cell_case_max_c': cell['case_max_c'], 'supply_peak_a': supply_a, 'supply_limit_a': limit_a,
            'reverse_blocking_loss_w': supply_a**2*f['reverse_blocking']['on_resistance_ohm'],
            'precharge_resistor_min_ohm': v0/limit_a, 'precharge': precharge,
            'enable_threshold_v': f['precharge']['enable_threshold_v']}


STUDIES = {'r2': dict(load=load_r2, fingerprint=r2_fingerprint, title='R2 candidate simulation', extra=()),
           'r3': dict(load=load_r3, fingerprint=r3_fingerprint, title='R3 candidate simulation: conducted motor heat path and 30 V undervoltage trip',
                      extra=(('high_frame_resistance', {}, {}, 'housing_to_frame_k_w', 'high'),
                             ('low_frame_to_room', {}, {}, 'frame_to_room_w_k', 'low'),
                             ('warm_room_low_frame', {}, {'ambient_offset_c': 15}, 'frame_to_room_w_k', 'low'))),
           'r3c': dict(load=load_r3c, fingerprint=r3c_fingerprint,
                       title='R3 with candidate controller C1 (kp 4, 2.5 m/s release limiter, 0.15 m end zone)', extra=()),
           'r4': dict(load=load_r4, fingerprint=r4_fingerprint,
                      title='R4 candidate simulation: bank on the drive bus (bidirectional), R3 + C1', extra=()),
           'r4m': dict(load=load_r4m, fingerprint=r4m_fingerprint,
                       title='R4 with the Kollmorgen TBM2G-11526D at 6:1 (motor study variant tbm_6; study, not adopted)', extra=())}


def run(root=Path('.'), jobs=None, study='r2'):
    from odrt.support_revision import screen
    spec = STUDIES[study]
    root = Path(root); initial = spec['fingerprint'](root)
    inputs = load_inputs(root); cfg, parts, variants, derived, source, support = spec['load'](root)
    criteria = load_engineering(root)[0]; stroke = inputs.envelope.max_usable_stroke_m
    out = root/f'build/engineering/{study}_candidate'; out.mkdir(parents=True, exist_ok=True)

    def setup(bank):
        c, q = copy.deepcopy(cfg), copy.deepcopy(parts); q['r2_cell'] = {'values': variants[bank]}; return c, q

    tasks = []
    for bank in BANKS:
        c, q = setup(bank)
        for case in cfg['cases']:
            tasks.append(('case', (bank, case['name']), c, q, inputs.scenarios[case['scenario']], inputs.defaults, stroke,
                          case, {}, criteria, str((out/f'{bank}__{case["name"]}.npz').relative_to(root))))
    for bank, name in REFINED:
        c, q = setup(bank); case = next(x for x in cfg['cases'] if x['name'] == name)
        for factor in (1, 2, 4):
            tasks.append(('refine', (bank, name, factor), c, q, inputs.scenarios[case['scenario']], inputs.defaults, stroke, case,
                          dict(maximum_step_s=cfg['solver']['maximum_step_s']/factor, tolerance_scale=1/factor**2), criteria, None))
    heavy = next(x for x in cfg['cases'] if x['name'] == 'paired_heavy_full')
    for name, scale, perturbation in SENSITIVITIES:
        c, q = setup('r2_fresh')
        for field, value in scale.items():
            group = 'mechanics' if field == 'routing_length_m' else 'thermal'
            c[group][field] = value if field == 'routing_length_m' else c[group][field]*value
        tasks.append(('sensitivity', (name,), c, q, inputs.scenarios[heavy['scenario']], inputs.defaults, stroke, heavy,
                      perturbation, criteria, None))
    # Study-specific bounds, run on the long slow pull where a heat path actually matters.
    slow = next(x for x in cfg['cases'] if x['name'] == 'single_slow_full')
    for name, _, perturbation, field, end in spec['extra']:
        c, q = setup('r2_fresh'); bounds = derived['frame_thermal']['bounds'][field]
        c['frame_thermal'][field] = bounds[1] if end == 'high' else bounds[0]
        tasks.append(('sensitivity', (name,), c, q, inputs.scenarios[slow['scenario']], inputs.defaults, stroke, slow,
                      perturbation, criteria, None))
    for name, changes, names in CONTROL_EXTRA.get(study, ()):
        for bank in BANKS:
            c, q = setup(bank); c['control'].update(changes)
            for case in (x for x in cfg['cases'] if x['name'] in names):
                tasks.append(('sensitivity', (f'{name}:{bank}:{case["name"]}',), c, q, inputs.scenarios[case['scenario']],
                              inputs.defaults, stroke, case, {}, criteria, None))
    # Longest cases first so the pool is not left waiting on one straggler.
    tasks.sort(key=lambda t: ('endurance' not in t[7]['name'], 'window_s' in t[7]))
    workers = jobs or int(os.environ.get('JOBS', 0)) or os.cpu_count()
    print(f'{study.upper()} candidate: {len(tasks)} simulations on {workers} workers', flush=True)
    cases = {b: {} for b in BANKS}; refine = {}; sensitivity = {}
    with ProcessPoolExecutor(workers) as pool:
        for done, (kind, key, m) in enumerate(pool.map(_job, tasks, chunksize=1), 1):
            if kind == 'case': cases[key[0]][key[1]] = m
            elif kind == 'refine': refine.setdefault(key[:2], {})[key[2]] = m
            else: sensitivity[key[0]] = m
            status = m.get('solver_failure') or (f'tracking {100*m["unit_0.tracking_fraction"]:.2f}%, '
                                                 f'trip {m["unit_0.trip_reason"]}')
            print(f'  [{done}/{len(tasks)}] {kind} {"/".join(map(str, key))}: {status}', flush=True)
    verification = {'refinement': {f'{b}__{n}': convergence(records, next(x for x in cfg['cases'] if x['name'] == n), criteria)
                                   for (b, n), records in refine.items()},
                    'sensitivity': sensitivity}
    verification['pass'] = (all(v['pass'] for v in verification['refinement'].values())
                            and all(m.get('numerical_valid', False) for m in sensitivity.values()))
    # Support screen at the simulated envelope: peak rope force and peak current x Kt, both
    # combined as uncorrelated corners, alongside the deliberately larger comparison corners.
    completed = [m for b in cases.values() for m in b.values() if 'solver_failure' not in m]
    motor = parts[cfg['reference']['motor']]['values']
    force = max(m['worst_peak_tension_n'] for m in completed)
    current = max(m[k] for m in completed for k in m if k.endswith('.max_current_a'))
    torque = current*motor['kt_nm_per_a']
    rows, difference, _ = screen(support, load_yaml(root/'data/compact_structure.yaml')['assumptions'], force, torque)
    if 'r4_power' in derived:
        derived = dict(derived, r4_checks=power_checks(derived['r4_power'], cases, parts, cfg, variants))
    if spec['fingerprint'](root) != initial:
        raise ConfigError(f'{study} inputs changed during run; refusing publication')
    report = {'fingerprint': initial, 'study': study, 'title': spec['title'], 'assessment': 'REVISE', 'hardware_qualified': False,
              'scope': 'all configured normal/fault cases for fresh and aged TV banks, four 3-resolution studies, '
                       'seven paired-heavy uncertainties, support screen at simulated loads',
              'reference': cfg['reference'], 'power': cfg['power'], 'control_current_limit_a': cfg['control']['current_limit_a'],
              'mechanics': cfg['mechanics'], 'thermal': cfg['thermal'],
              'topology': {'kind': cfg.get('power_topology', 'clamp'), **cfg['upstream_buffer']},
              'cell_values': variants, 'derived': derived, 'banks': cases, 'verification': verification,
              'support_at_simulated_loads': {'rope_force_n': force, 'max_current_a': current, 'motor_torque_nm': torque,
                                             'belt_tension_difference_n': difference, 'rows': rows,
                                             'passing_rows': sum(not r['failed_checks'] for r in rows)}}
    (root/f'reports/{study}_candidate.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    write_report(report, root/f'reports/{study}_candidate.md')
    return report


def convergence(records, case, criteria):
    if any('solver_failure' in records[f] for f in (1, 2, 4)):
        return {'pass': False, 'records': records}
    a, b, c = (records[f] for f in (1, 2, 4)); changes = {}
    for field, floor in (('worst_peak_tension_n', 1), ('minimum_bus_v', 1), ('maximum_bus_v', 1),
                         ('max_bar_angle_deg', .1), ('unit_0.tracking_rms_n', 2), ('worst_winding_c', 1)):
        d = max(abs(c[field]), floor); changes[field] = {'coarse_to_medium_fraction': abs(b[field]-a[field])/d,
                                                          'medium_to_fine_fraction': abs(c[field]-b[field])/d}
    mode = len({m['unit_0.trip_reason'] for m in (a, b, c)}) == 1
    times = [m['unit_0.trip_time_s'] for m in (a, b, c)]
    dt = abs(times[2]-times[1]) if all(t is not None for t in times) else None
    limit = criteria['convergence_normal_fraction_max' if case['fault'] == 'none' else 'convergence_fault_fraction_max']['value']
    ok = (mode and all(v['medium_to_fine_fraction'] <= limit for v in changes.values()) and (dt is None or dt <= 1e-4)
          and all(m['energy_residual_fraction'] <= criteria['energy_residual_fraction_max']['value'] for m in (a, b, c)))
    return {'pass': bool(ok), 'changes': changes, 'criterion_fraction': limit, 'trip_mode_consistent': mode,
            'trip_time_medium_to_fine_s': dt}


def failed(m):
    return sorted({f for row in m['assessment'] for f in row['failed_checks']})


def write_report(r, path):
    i = r['derived']['inertia']; s = r['support_at_simulated_loads']; ref = r['reference']
    bidirectional = r.get('topology', {}).get('kind') == 'bidirectional'
    lines = ['# '+r.get('title', 'R2 candidate simulation'), '', f'Fingerprint: `{r["fingerprint"]}`', '',
             '**Assessment: REVISE.** R2 joins the [R2 CAD](r2_package.md), the [power revision](revision_power.md) and the '
             '[support revision](support_revision.md) into one simulated machine: '
             f'{ref["ratio"]:g}:1 belt, drum-referred inertia {i["complete_known_reflected_inertia_kg_m2"]:.6f} kg m² '
             f'(R1: 0.024254), routing {r["mechanics"]["routing_length_m"]} m, {r["power"]["cell_series"]} × TV 3 V cells '
             + ('on the drive bus (bidirectional; one-way supply and dump unchanged)' if bidirectional else 'upstream of a Regen Clamp')
             + f', EPP-500-54 at {r["power"]["nominal_v"]} V, motor current limit {r["control_current_limit_a"]} A. '
             + ('Controller: see below.' if 'controller' in r['derived'] else 'Controller gains are unchanged from the reference.'), '',
             '| Bank / case | Tracking % | Peak N | Bus min–max V | Winding °C | Bar ° | Trip | Failed comparisons |',
             '|---|---:|---:|---:|---:|---:|---|---|']
    for bank, cases in r['banks'].items():
        for case, m in cases.items():
            if 'solver_failure' in m:
                lines.append(f'| {bank} / {case} | — | — | — | — | — | SOLVER FAILURE | unresolved |'); continue
            lines.append(f'| {bank} / {case} | {100*m["unit_0.tracking_fraction"]:.2f} | {m["worst_peak_tension_n"]:.0f} | '
                         f'{m["minimum_bus_v"]:.1f}–{m["maximum_bus_v"]:.1f} | {m["worst_winding_c"]:.1f} | '
                         f'{m["max_bar_angle_deg"]:.1f} | {m["unit_0.trip_reason"] or "none"} | {", ".join(failed(m)) or "none"} |')
    lines += ['', '## Numerical refinement', '', '| Case | Max medium–fine change | Outcome |', '|---|---:|---|']
    for name, v in r['verification']['refinement'].items():
        change = max((x['medium_to_fine_fraction'] for x in v.get('changes', {}).values()), default=float('nan'))
        lines.append(f'| {name} | {change:.3%} | {"pass" if v["pass"] else "FAIL / unresolved"} |')
    if 'frame_thermal' in r['derived']:
        f = r['derived']['frame_thermal']
        lines += ['', '## Conducted heat path', '', f['summary'], '', '| Parameter | Nominal | Bounds | Basis |', '|---|---:|---|---|']
        lines += [f'| {k} | {v} | {f["bounds"][k]} | {f["basis"][k]} |' for k, v in f['nominal'].items()]
    if 'controller' in r['derived']:
        ctl = r['derived']['controller']
        lines += ['', '## Controller', '', f'Variant `{ctl["variant"]}` from the [controller study](control_study.md): '
                  + ', '.join(f'{k}={v}' for k, v in ctl['changes'].items()) + '. All other control values are the reference.']
    if 'r3_power' in r['derived']:
        pw = r['derived']['r3_power']
        lines += ['', '## Undervoltage trip', '', f'Trip lowered to {pw["proposal"]["undervoltage_v"]} V '
                  f'([ODrive Pro]({pw["odrive_pro_dc_voltage"]["source"]}) DC range {pw["odrive_pro_dc_voltage"]["min_v"]}–'
                  f'{pw["odrive_pro_dc_voltage"]["max_v"]} V). ' + pw['proposal']['basis'], '']
        lines += ['- '+v for v in pw['proposal']['open_items']]
    if 'r4_checks' in r['derived']:
        k = r['derived']['r4_checks']; spec = r['derived']['r4_power']; f = spec['functions']
        verdict = lambda ok: 'pass' if ok else 'FAIL'
        lines += ['', '## Bank on the drive bus: hardware checks at the simulated envelope', '', spec['proposal']['basis'], '',
                  '| Check | Simulated | Limit / basis | Outcome |', '|---|---:|---|---|',
                  f'| Worst cell (max bank {k["max_bank_v"]:.2f} V / {r["power"]["cell_series"]} × {f["cell_voltage"]["worst_cell_factor"]}) | '
                  f'{k["worst_cell_v"]:.3f} V | {k["cell_rated_v"]} V rated | {verdict(k["cell_voltage_pass"])} |',
                  f'| Worst cell at the {r["power"]["trip_v"]} V trip | {k["trip_worst_cell_v"]:.3f} V | {k["cell_rated_v"]} V rated | '
                  f'{verdict(k["trip_worst_cell_v"] < k["cell_rated_v"])} |',
                  f'| Bank RMS current over one set, worst ({k["rms_worst_case"]["bank"]} / {k["rms_worst_case"]["case"]}) | '
                  f'{k["max_bank_rms_a"]:.1f} A | {k["cell_rms_rating_a"]} A continuous (15 K rise) | '
                  + ('pass' if k['rms_pass'] else f'exceeds continuous rating in {", ".join(k["rms_exceeding_cases"])}; '
                     f'cells reach {k["rms_worst_case"]["set_max_cell_c"]:.1f} °C over the {k["rms_worst_case"]["set_duration_s"]:.0f} s set') + ' |',
                  f'| Cell temperature if that set repeated continuously (fresh / aged ESR, {r["thermal"]["ambient_c"]} °C) | '
                  f'{k["continuous_repetition_cell_c"]["r2_fresh"]:.0f} / {k["continuous_repetition_cell_c"]["r2_aged"]:.0f} °C | '
                  f'{k["cell_case_max_c"]} °C case maximum | '
                  + ('pass' if max(k['continuous_repetition_cell_c'].values()) < k['cell_case_max_c']
                     else 'FAIL: back-to-back sets of this case need a bank duty limit or cooling') + ' |',
                  f'| Supply peak current | {k["supply_peak_a"]:.1f} A | {k["supply_limit_a"]:.1f} A limit | one-way source assumed |',
                  f'| Reverse-blocking loss at peak | {k["reverse_blocking_loss_w"]:.2f} W | assumed {f["reverse_blocking"]["on_resistance_ohm"]} Ω | no part selected |', '',
                  '| Bank | Capacitance F | Pre-charge at supply limit s | Bank energy at setpoint J |', '|---|---:|---:|---:|']
        lines += [f'| {x["bank"]} | {x["bank_capacitance_f"]:.2f} | {x["precharge_s_at_supply_limit"]:.1f} | {x["precharge_energy_j"]:.0f} |'
                  for x in k['precharge']]
        lines += ['', f'If the supply does not current-limit cleanly into the bank, a pre-charge resistor needs at least '
                  f'{k["precharge_resistor_min_ohm"]:.1f} Ω and must absorb the bank energy as a pulse. Drive enable is interlocked '
                  f'above {k["enable_threshold_v"]} V. ' + f['ripple_current']['note'], '']
        lines += ['- '+v for v in spec['open_items']]
    lines += ['', '## Uncertainties (paired heavy set, fresh bank; heat-path bounds on the slow heavy pull; controller variants as name:bank:case)', '',
              '| Perturbation | Tracking % | Winding °C | Minimum bus V | Trip | Failed comparisons |', '|---|---:|---:|---:|---|---|']
    for name, m in r['verification']['sensitivity'].items():
        if 'solver_failure' in m: lines.append(f'| {name} | — | — | — | SOLVER FAILURE | |'); continue
        lines.append(f'| {name} | {100*m["unit_0.tracking_fraction"]:.2f} | {m["worst_winding_c"]:.1f} | {m["minimum_bus_v"]:.1f} | '
                     f'{m["unit_0.trip_reason"] or "none"} | {", ".join(failed(m)) or "none"} |')
    lines += ['', '## Support screen at simulated R2 loads', '',
              f'Peak rope force {s["rope_force_n"]:.0f} N and peak current {s["max_current_a"]:.1f} A × Kt = '
              f'{s["motor_torque_nm"]:.2f} Nm, combined as uncorrelated corners; belt tension difference '
              f'{s["belt_tension_difference_n"]:.0f} N. {s["passing_rows"]}/{len(s["rows"])} corners pass.', '',
              '| Preload N/span | Rope z mm | Torque sign | Motor C0/P | Drum C0/P | Motor shaft MPa | Drum shaft MPa | Failed screens |',
              '|---:|---:|---:|---:|---:|---:|---:|---|']
    for x in s['rows']:
        lines.append(f'| {x["preload_n"]} | {x["rope_z_mm"]} | {x["torque_direction"]} | {x["motor_bearing_static_factor"]:.2f} | '
                     f'{x["drum_bearing_static_factor"]:.2f} | {x["motor_shaft_stress_mpa"]:.1f} | {x["drum_shaft_stress_mpa"]:.1f} | '
                     f'{", ".join(x["failed_checks"]) or "none"} |')
    lines += ['', '## Limits', '',
              ('- The bank joins the drive bus through its ESR only; wiring inductance, fusing and pre-charge transients are not modelled.'
               if bidirectional else
               '- Clamp is cycle-averaged; switching ripple, delay and peaks are not resolved. Upstream storage cannot absorb regeneration.'),
              '- Thermal resistances/capacities remain reference proposals; the TV cell heat capacity is assumed.',
              '- Ideal radial supports; deck/bridge/side-wall stiffness, joints, fatigue and belt rating are not checked.',
              '- Uncertainty perturbations co-vary plant and feedforward; independent miscalibration is not covered.',
              '- No wiring, tray, retention, isolation or cooling geometry is qualified by the CAD space claim.', '',
              f'Reproduce: `make {r.get("study", "r2")}-candidate` (parallel; `JOBS=n` limits workers).', '']
    path.write_text('\n'.join(lines))


if __name__ == '__main__':
    import sys
    result = run(study=sys.argv[1] if len(sys.argv) > 1 else 'r2')
    if not result['verification']['pass'] or any(not m.get('numerical_valid', False)
                                                 for b in result['banks'].values() for m in b.values()):
        raise SystemExit('R2 candidate numerical verification incomplete; failures retained')
