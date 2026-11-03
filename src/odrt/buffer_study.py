"""Compare a documented compact buffer without silently replacing the reference.

Run: python -m odrt.buffer_study. This is an architecture experiment, not a
qualified capacitor-pack design: balancing, tolerance, protection and packaging
remain separate work. All cases retain the coupled model's physical limits.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import numpy as np
import scipy

from odrt.config import load_yaml
from odrt.coupled import assess_case, fingerprint, load_coupled, simulate
from odrt.engineering import load_engineering
from odrt.project import load_inputs


def candidate_variants(spec):
    """Keep source facts separate from the explicitly assumed thermal capacity."""
    facts = spec['documented']
    fresh = {k: v for k, v in facts.items() if k not in
             ('diameter_max_mm', 'length_max_mm', 'capacitance_initial_min_fraction')}
    fresh['diameter_mm'] = facts['diameter_max_mm']
    fresh['length_mm'] = facts['length_max_mm']
    fresh['thermal_capacity_j_per_k'] = spec['assumptions']['thermal_capacity_j_per_k']
    low_c = facts['capacitance_initial_min_fraction']
    aged_c = low_c * facts['capacitance_end_life_fraction']
    variants = {'compact_nominal': fresh}
    for name, c_scale, esr_scale, heat in (
            ('compact_initial_min', low_c, 1, fresh['thermal_capacity_j_per_k']),
            ('compact_aged', aged_c, facts['esr_end_life_multiplier'], fresh['thermal_capacity_j_per_k']),
            ('compact_aged_low_heat_capacity', aged_c, facts['esr_end_life_multiplier'],
             spec['assumptions']['thermal_capacity_bounds_j_per_k'][0]),
            ('compact_aged_high_heat_capacity', aged_c, facts['esr_end_life_multiplier'],
             spec['assumptions']['thermal_capacity_bounds_j_per_k'][1])):
        values = copy.deepcopy(fresh)
        values['capacitance_f'] *= c_scale
        values['esr_initial_max_ohm'] *= esr_scale
        values['thermal_capacity_j_per_k'] = heat
        variants[name] = values
    return variants


def study_fingerprint(root):
    root = Path(root)
    digest = hashlib.sha256(fingerprint(root).encode())
    digest.update((root/'data/compact_buffer.yaml').read_bytes())
    digest.update(Path(__file__).read_bytes())
    return digest.hexdigest()


def run(root=Path('.')):
    root = Path(root)
    initial_hash = study_fingerprint(root)
    inputs = load_inputs(root)
    cfg, parts = load_coupled(root, inputs.scenarios)
    # Bound work per requested output interval. This does not relax tolerances
    # or change the equations; relay chatter must remain a failed case.
    cfg['solver']['max_steps'] = 2000
    criteria = load_engineering(root)[0]
    spec = load_yaml(root/'data/compact_buffer.yaml')
    selected = {'single_heavy_full', 'paired_heavy_full', 'single_fast_full',
                'single_endurance_full', 'left_power_loss_buffered', 'paired_dump_failure',
                'left_power_loss_buffered_coordinated', 'paired_dump_failure_coordinated'}
    variants = {'reference': parts[cfg['reference']['capacitor']]['values'], **candidate_variants(spec)}
    build = root/'build/engineering/buffer_study'
    build.mkdir(parents=True, exist_ok=True)
    results = {}
    for name, values in variants.items():
        variant_cfg, variant_parts = copy.deepcopy(cfg), copy.deepcopy(parts)
        variant_cfg['reference']['capacitor'] = 'buffer_study_candidate'
        variant_parts['buffer_study_candidate'] = {'values': values}
        series, parallel = cfg['power']['cell_series'], cfg['power']['cell_parallel']
        bank = dict(capacitance_f=values['capacitance_f']*parallel/series,
                    esr_ohm=values['esr_initial_max_ohm']*series/parallel,
                    cell_mass_kg=values['mass_kg']*series*parallel,
                    cell_cylinder_volume_l=np.pi*(values['diameter_mm']/2)**2*values['length_mm']*series*parallel/1e6)
        results[name] = {'bank': bank, 'cell_values_used': values, 'cases': {}}
        for case in cfg['cases']:
            if case['name'] not in selected:
                continue
            print(f'buffer study {name}: {case["name"]}', flush=True)
            try:
                result = simulate(variant_cfg, variant_parts, inputs.scenarios[case['scenario']],
                                  inputs.defaults, inputs.envelope.max_usable_stroke_m, case)
            except RuntimeError as error:
                results[name]['cases'][case['name']] = {
                    'solver_failure': str(error), 'numerical_valid': False,
                    'assessment': 'unresolved; not a physical performance result'}
                print(f'buffer study {name}: {case["name"]}: solver failed; retained', flush=True)
                continue
            metrics, signals = result['metrics'], result['signals']
            metrics['assessment'] = assess_case(metrics, variant_cfg, variant_parts, case, criteria)
            metrics['numerical_valid'] = bool(metrics['energy_residual_fraction'] <= criteria['energy_residual_fraction_max']['value']
                                               and all(np.isfinite(v).all() for v in signals.values()))
            # Integrate over time, rather than over output samples at fault discontinuities.
            for unit in range(case['units']):
                prefix = f'unit_{unit}.'
                current = signals[prefix+'capacitor_current_a']/parallel
                rms = float(np.sqrt(np.trapz(current**2, signals['t'])/signals['t'][-1]))
                metrics[prefix+'cell_current_rms_a'] = rms
                metrics[prefix+'cell_current_peak_a'] = float(np.abs(current).max())
                initial_esr = (parts[cfg['reference']['capacitor']]['values']['esr_initial_max_ohm']
                               if name=='reference' else spec['documented']['esr_initial_max_ohm'])
                # Keep the same resistive heat at increased ESR; not a vendor aging rating.
                rms_comparison = values['current_rms_15k_rise_a']*np.sqrt(initial_esr/values['esr_initial_max_ohm'])
                metrics[prefix+'cell_rms_comparison_limit_a'] = float(rms_comparison)
                metrics[prefix+'cell_rms_open_air_screen_pass'] = bool(rms <= rms_comparison)
            trace = build/f'{name}__{case["name"]}.npz'
            np.savez_compressed(trace, **signals)
            metrics['trace'] = str(trace.relative_to(root))
            results[name]['cases'][case['name']] = metrics
        (build/'checkpoint.json').write_text(json.dumps(results, indent=2, allow_nan=False)+'\n')
    verification = verify_events(inputs,cfg,parts,spec,criteria,build)
    if study_fingerprint(root) != initial_hash:
        raise RuntimeError('buffer study inputs changed during run; refusing to publish')
    report = {'fingerprint': initial_hash, 'source': spec['source'], 'assumptions': spec['assumptions'],
              'scipy_version': scipy.__version__,
              'scope': 'eight selected cases per variant, with four explicit resolution studies; not full operating-envelope qualification',
              'solver_max_steps_per_output_interval': cfg['solver']['max_steps'],
              'assessment': 'REVISE; package and protection unqualified', 'variants': results,
              'verification': verification}
    path = root/'reports/compact_buffer.json'
    path.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    write_report(report, root/'reports/compact_buffer.md')
    return report


def verify_events(inputs,cfg,parts,spec,criteria,build):
    """Refine actual voltage events and normal aged-bank tracking independently."""
    studies = {}
    variants = candidate_variants(spec)
    for variant_name,case_name in (
            ('compact_nominal','left_power_loss_buffered_coordinated'),
            ('compact_nominal','paired_dump_failure_coordinated'),
            ('compact_aged','single_fast_full'),
            ('compact_aged','single_heavy_full')):
        case = next(c for c in cfg['cases'] if c['name']==case_name)
        adjusted_cfg,adjusted_parts = copy.deepcopy(cfg),copy.deepcopy(parts)
        adjusted_cfg['reference']['capacitor']='event_verification'
        adjusted_parts['event_verification']={'values':variants[variant_name]}
        records = []
        errors = []
        name=variant_name+'__'+case_name
        for factor in (1,2,4):
            print(f'buffer refinement {name}: {factor}',flush=True)
            try:
                result=simulate(adjusted_cfg,adjusted_parts,inputs.scenarios[case['scenario']],inputs.defaults,
                                inputs.envelope.max_usable_stroke_m,case,
                                maximum_step_s=cfg['solver']['maximum_step_s']/factor,tolerance_scale=1/factor**2)
            except RuntimeError as error:
                errors.append({'factor':factor,'solver_failure':str(error)})
                continue
            np.savez_compressed(build/f'refinement__{name}__{factor}.npz',**result['signals'])
            records.append(result['metrics'])
        if errors:
            studies[name]={'pass':False,'solver_failures':errors,'metrics':records,'changes':{},
                           'trip_time_medium_to_fine_s':None}
            continue
        changes={}
        for key,floor in (('unit_0.peak_tension_n',1),('minimum_bus_v',1),('maximum_bus_v',1),
                          ('max_bar_angle_deg',.1),('unit_0.tracking_rms_n',2)):
            values=[record[key] for record in records]
            changes[key]={'coarse_to_medium_fraction':abs(values[1]-values[0])/max(abs(values[2]),floor),
                          'medium_to_fine_fraction':abs(values[2]-values[1])/max(abs(values[2]),floor)}
        trips=[record['unit_0.trip_time_s'] for record in records]
        same_mode=len({record['unit_0.trip_reason'] for record in records})==1
        trip_change=abs(trips[2]-trips[1]) if all(value is not None for value in trips) else None
        limit=criteria['convergence_normal_fraction_max' if case['fault']=='none' else 'convergence_fault_fraction_max']['value']
        studies[name]={'metrics':records,'changes':changes,'criterion_fraction':limit,
                       'trip_mode_consistent':same_mode,'trip_time_medium_to_fine_s':trip_change,
                       'trip_time_criterion_s':1e-4,
                       'pass':bool(same_mode and all(v['medium_to_fine_fraction']<=limit for v in changes.values())
                                   and (trip_change is None or trip_change<=1e-4)
                                   and all(m['energy_residual_fraction']<=criteria['energy_residual_fraction_max']['value'] for m in records))}
    return {'pass':all(v['pass'] for v in studies.values()),'studies':studies,
            'scope':'Four selected normal/fault cases; does not establish complete product convergence or physical fidelity'}


def write_report(report, path):
    lines = ['# Compact buffer experiment', '', f'Fingerprint: `{report["fingerprint"]}`', '',
             'This experiment retains the coupled reference mechanics, source, control and thermal network. '
             'It changes the capacitor cell only. No complete enclosure fit or protection circuit is established.', '',
             f'Manufacturer facts: [Eaton HV datasheet]({report["source"]}), accessed 2026-11-02. '
             'Thermal capacity is an assumption: 20 J/K per cell, bracketed at 10 and 40 J/K. '
             'The aging corner combines minimum initial capacitance with a further 30% loss and doubled ESR. '
             'It is not a life prediction. Open-air current ratings do not qualify an enclosed pack.', '',
             '| Variant | Bank F | ESR Ω | Cells kg | Cell bodies L |',
             '|---|---:|---:|---:|---:|']
    for name, result in report['variants'].items():
        b = result['bank']
        lines.append(f'| {name} | {b["capacitance_f"]:.3f} | {b["esr_ohm"]:.4f} | '
                     f'{b["cell_mass_kg"]:.2f} | {b["cell_cylinder_volume_l"]:.3f} |')
    lines += ['', 'Cell-body volume excludes leads, balance/protection boards, insulation, clearances and harness.', '',
              '| Variant / case | Bus min–max V | Winding °C | Cell °C | Cell RMS A | Tracking % | Failed checks |',
              '|---|---:|---:|---:|---:|---:|---|']
    for name, result in report['variants'].items():
        for case, m in result['cases'].items():
            if 'solver_failure' in m:
                lines.append(f'| {name} / {case} | — | — | — | — | — | SOLVER FAILURE; unresolved |')
                continue
            failed = sorted({f for a in m['assessment'] for f in a['failed_checks']})
            lines.append(f'| {name} / {case} | {m["minimum_bus_v"]:.2f}–{m["maximum_bus_v"]:.2f} | '
                         f'{m["worst_winding_c"]:.1f} | {m["unit_0.max_capacitor_c"]:.1f} | '
                         f'{m["unit_0.cell_current_rms_a"]:.2f} | {100*m["unit_0.tracking_fraction"]:.2f} | '
                         f'{", ".join(failed) or "none in evaluated comparisons"} |')
    lines += ['', 'All cases retain software fault injection and the limitations in `reports/coupled.md`. '
              'Current peaks are recorded, but the datasheet’s one-second pulse definition is not an arbitrary '
              'instantaneous current limit. Per-cell imbalance, leakage, balancing and wiring parasitics are not modeled. '
              'The open-air RMS comparison scales by inverse square root of ESR growth to preserve the '
              'initial rated resistive heat; this is an analytical screen, not a vendor aged-cell rating.', '',
              'The experiment caps solver work at 2000 internal steps per output interval, without changing '
              'the reference time-step cap or tolerances. Failure is retained explicitly. Voltage and thermal '
              'zero crossings now latch the affected unit off. Recovery does not rearm it; configured peer '
              'stops follow the recorded trip time plus the assumed peer delay. Hardware detection and '
              'phase-transfer latency remain unvalidated. The earlier non-latching experiment is historical.', '',
              '## Selected resolution verification', '',
              '| Study | Max medium–fine change | Trip-time change s | Outcome |', '|---|---:|---:|---|']
    for name,v in report['verification']['studies'].items():
        maximum=max((c['medium_to_fine_fraction'] for c in v['changes'].values()),default=float('nan'))
        trip='—' if v['trip_time_medium_to_fine_s'] is None else f'{v["trip_time_medium_to_fine_s"]:.3g}'
        lines.append(f'| {name} | {maximum:.3%} | {trip} | {"pass" if v["pass"] else "FAIL / unresolved"} |')
    lines += ['', 'Refinement uses maximum steps 2/1/0.5 ms and relative tolerances 1e-6/2.5e-7/6.25e-8; '
              'the original relative normal/fault criteria apply. Trip modes must agree and medium-to-fine '
              'trip time must change by at most 0.1 ms. This covers four selected cases only.', '',
              'Solver backends and any event-interpolation fallback are recorded per case in the JSON. '
              'SciPy BDF uses the same equations and error tolerances when CVODES returns CV_ILL_INPUT; '
              'an independent analytic decay/event/quadrature test covers the fallback path.', '',
              '## Protective trip records', '', '| Variant / case | Unit | Reason | Time s |', '|---|---:|---|---:|']
    for name,v in report['variants'].items():
        for case,m in v['cases'].items():
            if 'solver_failure' in m: continue
            for unit in (0,1):
                prefix=f'unit_{unit}.'
                if m.get(prefix+'trip_latched'):
                    lines.append(f'| {name} / {case} | {unit} | {m[prefix+"trip_reason"]} | {m[prefix+"trip_time_s"]:.6f} |')
    lines += ['', 'Reproduce: `.venv/bin/python -m odrt.buffer_study`.', '']
    path.write_text('\n'.join(lines))


if __name__ == '__main__':
    result=run()
    if not result['verification']['pass'] or any(
            not m.get('numerical_valid',False) for v in result['variants'].values() for m in v['cases'].values()):
        raise SystemExit('compact buffer numerical verification incomplete; failures retained in reports')
