"""Resolution checks for the source-backed upstream-buffer experiment."""
from pathlib import Path
import copy
import hashlib
import json

from odrt.config import ConfigError
from odrt.coupled import simulate
from odrt.engineering import load_engineering
from odrt.project import load_inputs
from odrt.revision_power import load_revision,revision_fingerprint
from odrt.upstream_buffer import build_upstream_model


def run(root=Path('.')):
    root=Path(root);report_path=root/'reports/revision_power.json'
    original=json.loads(report_path.read_text());current_hash=revision_fingerprint(root)
    if original['fingerprint']!=current_hash:raise ConfigError('power revision report is stale')
    inputs=load_inputs(root);cfg,parts,variants,_,_=load_revision(root);criteria=load_engineering(root)[0]
    studies={}
    for bank,name in (('compact_aged','paired_heavy_full'),('compact_nominal','single_fast_full'),
                       ('compact_aged','paired_dump_failure_coordinated')):
        selected_cfg,selected_parts=copy.deepcopy(cfg),copy.deepcopy(parts)
        selected_cfg['reference']['capacitor']='cell';selected_parts['cell']={'values':variants[bank]}
        case=next(c for c in cfg['cases'] if c['name']==name);records=[];errors=[]
        for factor in (1,2,4):
            print(f'upstream refinement {bank}/{name}: {factor}',flush=True)
            try:
                value=simulate(selected_cfg,selected_parts,inputs.scenarios[case['scenario']],inputs.defaults,2,case,
                    maximum_step_s=cfg['solver']['maximum_step_s']/factor,tolerance_scale=1/factor**2,
                    model_factory=build_upstream_model)
                records.append(value['metrics'])
            except RuntimeError as error:errors.append({'factor':factor,'error':str(error)})
        key=bank+'__'+name
        if errors:studies[key]={'pass':False,'errors':errors};continue
        changes={}
        for field,floor in (('worst_peak_tension_n',1),('minimum_bus_v',1),('maximum_bus_v',1),
                            ('worst_winding_c',1),('max_bar_angle_deg',.1),('unit_0.tracking_rms_n',2)):
            a,b,c=(r[field] for r in records);denominator=max(abs(c),floor)
            changes[field]={'coarse_to_medium_fraction':abs(b-a)/denominator,'medium_to_fine_fraction':abs(c-b)/denominator}
        limit=criteria['convergence_normal_fraction_max' if case['fault']=='none' else 'convergence_fault_fraction_max']['value']
        same_mode=len({r['unit_0.trip_reason'] for r in records})==1
        trip_times=[r['unit_0.trip_time_s'] for r in records]
        trip_change=abs(trip_times[2]-trip_times[1]) if all(t is not None for t in trip_times) else None
        studies[key]={'pass':bool(same_mode and all(v['medium_to_fine_fraction']<=limit for v in changes.values())
            and (trip_change is None or trip_change<=1e-4)
            and all(r['energy_residual_fraction']<=criteria['energy_residual_fraction_max']['value'] for r in records)),
            'metrics':records,'changes':changes,'criterion_fraction':limit,'trip_time_medium_to_fine_s':trip_change}
    if revision_fingerprint(root)!=current_hash:raise ConfigError('power model changed during refinement')
    result={'revision_fingerprint':current_hash,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'pass':all(v['pass'] for v in studies.values()),'studies':studies,
            'scope':'Averaged model numerical resolution only; does not validate actual switching or hardware'}
    (root/'reports/revision_power_verification.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    lines=['# Upstream-buffer numerical refinement','',f'Revision fingerprint: `{current_hash}`','',
           '| Case | Max medium–fine change | Outcome |','|---|---:|---|']
    for name,v in studies.items():
        change=max((x['medium_to_fine_fraction'] for x in v.get('changes',{}).values()),default=float('nan'))
        lines.append(f'| {name} | {change:.3%} | {"pass" if v["pass"] else "FAIL / unresolved"} |')
    lines+=['','Steps are 2/1/0.5 ms caps with relative tolerances 1e-6/2.5e-7/6.25e-8. '
        'The normal/fault comparison criteria are unchanged. Trip modes must agree and '
        'medium-to-fine event time changes must be no greater than 0.1 ms.','',
        'These are averaged-model checks. Hysteresis ripple, switching delay, output-capacitor allocation, '
        'clamp hotspot/OTP and actual installed cooling remain unverified. The 12 selected study cases '
        'do not replace the full candidate suite.','',
        'Reproduce: `.venv/bin/python -m odrt.verify_revision_power` after the power study.','']
    (root/'reports/revision_power_verification.md').write_text('\n'.join(lines));return result


if __name__=='__main__':
    if not run()['pass']:raise SystemExit('upstream-buffer numerical refinement failed')
