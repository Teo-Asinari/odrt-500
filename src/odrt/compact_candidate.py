"""Simulate the CAD-derived compact candidate across the complete case suite.

Keep this experiment distinct from the baseline and capacitor-only comparison.
No enclosure, hardware stopping or thermal qualification is inferred.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import numpy as np

from odrt.buffer_study import candidate_variants
from odrt.compact_package import build, inertia_properties
from odrt.config import ConfigError, check_keys, integer, load_yaml, number
from odrt.coupled import assess_case, fingerprint, load_coupled, simulate
from odrt.engineering import load_engineering
from odrt.project import load_inputs


def candidate_fingerprint(root):
    root=Path(root);h=hashlib.sha256(fingerprint(root).encode())
    for path in ('configs/compact_package.yaml','configs/compact_candidate.yaml','data/compact_buffer.yaml',
                 'src/odrt/compact_package.py','src/odrt/buffer_study.py','src/odrt/compact_candidate.py'):
        source=Path(__file__).with_name(Path(path).name) if path.startswith('src/') else root/path
        h.update(path.encode()+b'\0'+source.read_bytes()+b'\0')
    return h.hexdigest()


def load_candidate(root=Path('.')):
    root=Path(root);spec=load_yaml(root/'configs/compact_candidate.yaml')
    check_keys(spec,'compact candidate',['bank_variants','routing_length_m','routing_basis','air_density_kg_m3',
               'air_specific_heat_j_kg_k','airflow_cfm','airflow_basis','air_capacity_basis','solver_work_bound','notes'])
    for field in ('routing_length_m','air_density_kg_m3','air_specific_heat_j_kg_k','airflow_cfm'):
        number(spec[field],field,minimum=0,exclusive_minimum=True)
    integer(spec['solver_work_bound'],'solver_work_bound',minimum=1)
    cfg,parts=load_coupled(root)
    variants=candidate_variants(load_yaml(root/'data/compact_buffer.yaml'))
    if (not isinstance(spec['bank_variants'],list) or not spec['bank_variants']
            or len(set(spec['bank_variants']))!=len(spec['bank_variants'])
            or any(name not in variants for name in spec['bank_variants'])):
        raise ConfigError('compact candidate requires unique known bank variants')
    objects,_,info=build(root)
    inertia=inertia_properties(objects,info,parts)
    cfg['reference']['drum_inertia_kg_m2']=inertia['equivalent_added_drum_inertia_kg_m2']
    cfg['mechanics']['routing_length_m']=spec['routing_length_m']
    volume_m3=float(np.prod(info['layout']['envelope_mm']))/1e9
    cfg['thermal']['air_capacity_j_k']=volume_m3*spec['air_density_kg_m3']*spec['air_specific_heat_j_kg_k']
    cfg['thermal']['air_to_room_w_k']=spec['airflow_cfm']*.028316846592/60*spec['air_density_kg_m3']*spec['air_specific_heat_j_kg_k']
    cfg['solver']['max_steps']=spec['solver_work_bound']
    return spec,cfg,parts,variants,dict(inertia=inertia,air_volume_upper_bound_m3=volume_m3,
                                      air_capacity_j_k=cfg['thermal']['air_capacity_j_k'],
                                      air_to_room_w_k=cfg['thermal']['air_to_room_w_k'])


def evaluate(result,cfg,parts,case,criteria):
    metrics=result['metrics'];signals=result['signals']
    metrics['assessment']=assess_case(metrics,cfg,parts,case,criteria)
    metrics['numerical_valid']=bool(metrics['energy_residual_fraction']<=criteria['energy_residual_fraction_max']['value']
                                   and all(np.isfinite(value).all() for value in signals.values()))
    return metrics


def run(root=Path('.')):
    root=Path(root);initial_hash=candidate_fingerprint(root)
    inputs=load_inputs(root);spec,cfg,parts,variants,derived=load_candidate(root)
    criteria=load_engineering(root)[0]
    output=root/'build/engineering/compact_candidate';output.mkdir(parents=True,exist_ok=True)
    results={}
    for name in spec['bank_variants']:
        selected_cfg,selected_parts=copy.deepcopy(cfg),copy.deepcopy(parts)
        selected_cfg['reference']['capacitor']='compact_candidate_cell'
        selected_parts['compact_candidate_cell']={'values':variants[name]}
        cases={};results[name]={'reference':selected_cfg['reference'],'power':selected_cfg['power'],
                             'mechanics':selected_cfg['mechanics'],'thermal':selected_cfg['thermal'],
                             'cell_values_used':variants[name],'cases':cases}
        for case in selected_cfg['cases']:
            print(f'compact candidate {name}: {case["name"]}',flush=True)
            try:
                value=simulate(selected_cfg,selected_parts,inputs.scenarios[case['scenario']],inputs.defaults,
                               inputs.envelope.max_usable_stroke_m,case)
            except RuntimeError as error:
                cases[case['name']]={'solver_failure':str(error),'numerical_valid':False}
                continue
            metrics=evaluate(value,selected_cfg,selected_parts,case,criteria)
            trace=output/f'{name}__{case["name"]}.npz';np.savez_compressed(trace,**value['signals'])
            metrics['trace']=str(trace.relative_to(root));cases[case['name']]=metrics
            print(f'  tracking {100*metrics["unit_0.tracking_fraction"]:.2f}%; '
                  f'peak {metrics["worst_peak_tension_n"]:.1f} N; '
                  f'trip {metrics["unit_0.trip_reason"]}; energy {metrics["energy_residual_fraction"]:.3g}',flush=True)
        (output/'checkpoint.json').write_text(json.dumps(results,indent=2,allow_nan=False)+'\n')
    verification=verify(inputs,cfg,parts,variants,spec,criteria,output)
    if candidate_fingerprint(root)!=initial_hash:
        raise ConfigError('compact candidate source/inputs changed during run; refusing publication')
    report={'fingerprint':initial_hash,'scope':'all configured normal/fault cases for each stated bank variant',
            'configured_cases_per_variant':len(cfg['cases']),'specification':spec,'derived':derived,
            'variants':results,'verification':verification,'assessment':'REVISE','hardware_qualified':False}
    (root/'reports/compact_candidate.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    write_report(report,root/'reports/compact_candidate.md')
    return report


def verify(inputs,cfg,parts,variants,spec,criteria,output):
    refinements={}
    for variant,case_name in (('compact_nominal','single_heavy_full'),('compact_nominal','paired_release_asymmetric'),
                              ('compact_aged','left_power_loss_buffered_coordinated'),('compact_aged','single_fast_full')):
        if variant not in spec['bank_variants']:continue
        selected_cfg,selected_parts=copy.deepcopy(cfg),copy.deepcopy(parts)
        selected_cfg['reference']['capacitor']='compact_candidate_cell'
        selected_parts['compact_candidate_cell']={'values':variants[variant]}
        case=next(c for c in cfg['cases'] if c['name']==case_name);records=[];errors=[]
        for factor in (1,2,4):
            print(f'candidate refinement {variant}/{case_name}: {factor}',flush=True)
            try:
                value=simulate(selected_cfg,selected_parts,inputs.scenarios[case['scenario']],inputs.defaults,
                               inputs.envelope.max_usable_stroke_m,case,
                               maximum_step_s=cfg['solver']['maximum_step_s']/factor,tolerance_scale=1/factor**2)
                records.append(value['metrics'])
            except RuntimeError as error:errors.append({'factor':factor,'solver_failure':str(error)})
        key=variant+'__'+case_name
        if errors:
            refinements[key]={'pass':False,'solver_failures':errors,'metrics':records};continue
        changes={}
        for field,floor in (('worst_peak_tension_n',1),('minimum_bus_v',1),('maximum_bus_v',1),
                            ('max_bar_angle_deg',.1),('unit_0.tracking_rms_n',2),('worst_winding_c',1)):
            a,b,c=(m[field] for m in records);denom=max(abs(c),floor)
            changes[field]={'coarse_to_medium_fraction':abs(b-a)/denom,'medium_to_fine_fraction':abs(c-b)/denom}
        mode=len({m['unit_0.trip_reason'] for m in records})==1
        times=[m['unit_0.trip_time_s'] for m in records]
        time_change=abs(times[2]-times[1]) if all(t is not None for t in times) else None
        limit=criteria['convergence_normal_fraction_max' if case['fault']=='none' else 'convergence_fault_fraction_max']['value']
        passed=(mode and all(v['medium_to_fine_fraction']<=limit for v in changes.values())
                and (time_change is None or time_change<=1e-4)
                and all(m['energy_residual_fraction']<=criteria['energy_residual_fraction_max']['value'] for m in records))
        refinements[key]={'pass':bool(passed),'metrics':records,'changes':changes,'criterion_fraction':limit,
                          'trip_mode_consistent':mode,'trip_time_medium_to_fine_s':time_change}
    # These uncertainties change actual candidate assumptions, not just capacitor values.
    sensitivity={};case=next(c for c in cfg['cases'] if c['name']=='paired_heavy_full')
    for name,modification,perturbation in (
            ('nominal',{},{}),('half_airflow',{'air_to_room_w_k':cfg['thermal']['air_to_room_w_k']/2},{}),
            ('quarter_airflow',{'air_to_room_w_k':cfg['thermal']['air_to_room_w_k']/4},{}),
            ('short_routing',{'routing_length_m':.12},{}),('long_routing',{'routing_length_m':.25},{}),
            ('low_km',{}, {'km_scale':.34/.53}),('warm_room',{}, {'ambient_offset_c':15}),
            ('extra_inertia',{}, {'inertia_scale':1.25})):
        selected_cfg,selected_parts=copy.deepcopy(cfg),copy.deepcopy(parts)
        selected_cfg['reference']['capacitor']='compact_candidate_cell'
        selected_parts['compact_candidate_cell']={'values':variants['compact_nominal']}
        for field,value in modification.items():
            selected_cfg['mechanics' if field=='routing_length_m' else 'thermal'][field]=value
        print(f'candidate sensitivity {name}',flush=True)
        try:
            value=simulate(selected_cfg,selected_parts,inputs.scenarios[case['scenario']],inputs.defaults,
                           inputs.envelope.max_usable_stroke_m,case,**perturbation)
            sensitivity[name]={'configuration_changes':modification,'parameter_changes':perturbation,
                               'metrics':evaluate(value,selected_cfg,selected_parts,case,criteria)}
        except RuntimeError as error:sensitivity[name]={'solver_failure':str(error)}
    return {'pass':all(v['pass'] for v in refinements.values()) and all(
                v.get('metrics',{}).get('numerical_valid',False) for v in sensitivity.values()),
            'refinement':refinements,'sensitivity':sensitivity,
            'scope':'Selected resolution and physical uncertainty checks; not hardware validation'}


def write_report(r,path):
    d=r['derived'];lines=['# CAD-derived compact candidate simulation','',f'Fingerprint: `{r["fingerprint"]}`','',
        '**Assessment: REVISE.** This study evaluates the compact geometry candidate, not a complete qualified product. '
        'It retains all configured normal and fault scenarios and does not retune controller gains.','',
        f'Total known drum-referred inertia: {d["inertia"]["complete_known_reflected_inertia_kg_m2"]:.8f} kg m². '
        f'The equivalent additional drum term is {d["inertia"]["equivalent_added_drum_inertia_kg_m2"]:.8f}; '
        'the catalog motor rotor is then added exactly once by the coupled plant.','',
        f'Nominal routing length: {r["specification"]["routing_length_m"]} m. '+r['specification']['routing_basis'],'',
        f'Air-node capacity: {d["air_capacity_j_k"]:.3f} J/K; flow conductance {d["air_to_room_w_k"]:.3f} W/K. '
        +r['specification']['air_capacity_basis']+' '+r['specification']['airflow_basis'],'',
        '| Bank / case | Tracking % | Peak N | Bus min–max V | Winding °C | Bar angle ° | Trip | Failed comparisons |',
        '|---|---:|---:|---:|---:|---:|---|---|']
    for name,v in r['variants'].items():
        for case,m in v['cases'].items():
            if 'solver_failure' in m:
                lines.append(f'| {name} / {case} | — | — | — | — | — | SOLVER FAILURE | unresolved |');continue
            failed=sorted({f for a in m['assessment'] for f in a['failed_checks']})
            lines.append(f'| {name} / {case} | {100*m["unit_0.tracking_fraction"]:.2f} | {m["worst_peak_tension_n"]:.1f} | '
                f'{m["minimum_bus_v"]:.2f}–{m["maximum_bus_v"]:.2f} | {m["worst_winding_c"]:.1f} | {m["max_bar_angle_deg"]:.2f} | '
                f'{m["unit_0.trip_reason"] or "none"} | {", ".join(failed) or "none in listed screens"} |')
    lines += ['','## Numerical refinement','','| Case | Max medium–fine change | Outcome |','|---|---:|---|']
    for name,v in r['verification']['refinement'].items():
        change=max((x['medium_to_fine_fraction'] for x in v.get('changes',{}).values()),default=float('nan'))
        lines.append(f'| {name} | {change:.3%} | {"pass" if v["pass"] else "FAIL / unresolved"} |')
    lines += ['','## Candidate uncertainties','','| Perturbation | Tracking % | Winding °C | Minimum bus V | Failed comparisons |','|---|---:|---:|---:|---|']
    for name,v in r['verification']['sensitivity'].items():
        if 'metrics' not in v:lines.append(f'| {name} | — | — | — | SOLVER FAILURE |');continue
        m=v['metrics'];failed=sorted({f for a in m['assessment'] for f in a['failed_checks']})
        lines.append(f'| {name} | {100*m["unit_0.tracking_fraction"]:.2f} | {m["worst_winding_c"]:.1f} | '
                     f'{m["minimum_bus_v"]:.2f} | {", ".join(failed) or "none in listed screens"} |')
    lines += ['','## Remaining limits','']+['- '+note for note in r['specification']['notes']]
    lines += ['','The full compact CAD still lacks engineered wiring, connectors, positive retention, sensors, '
              'guide actuation detail, cooling and electrical clearances. The conditional airflow is not a '
              'demonstrated installed capability. No qualified force/speed/duty or fault envelope follows '
              'from numerical convergence. Read `compact_package.md`, `coupled.md` and the validation plan.','',
              'Reproduce: `.venv/bin/python -m odrt.compact_candidate`.','']
    path.write_text('\n'.join(lines))


if __name__=='__main__':
    result=run()
    if not result['verification']['pass'] or any(not m.get('numerical_valid',False)
        for v in result['variants'].values() for m in v['cases'].values()):
        raise SystemExit('compact candidate numerical verification incomplete; failures retained')
