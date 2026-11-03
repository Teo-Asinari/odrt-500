"""Source-backed power revision experiment; not a revised complete package."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import numpy as np

from odrt.compact_candidate import candidate_fingerprint,load_candidate
from odrt.config import ConfigError,load_yaml
from odrt.coupled import assess_case,simulate
from odrt.engineering import load_engineering
from odrt.project import load_inputs
from odrt.upstream_buffer import build_upstream_model


def load_revision(root=Path('.')):
    root=Path(root);_,cfg,parts,variants,derived=load_candidate(root)
    source=load_yaml(root/'data/revision_components.yaml');assumptions=source['assumptions']
    pro=source['odrive_pro']['facts'];supply=source['epp500_54']['facts'];clamp=source['regen_clamp']['facts']
    cfg['reference']['drive']='revision_pro';cfg['reference']['supply']='revision_supply'
    parts['revision_pro']={'values':dict(voltage_absolute_max_v=pro['voltage_max_v'],
        modulation_utilization=assumptions['modulation_utilization'],
        recommended_electrical_frequency_hz=assumptions['electrical_frequency_comparison_hz'],
        ambient_max_c_for_ratings=assumptions['ambient_max_c_for_ratings'])}
    parts['revision_supply']={'values':dict(supply)}
    cfg['power'].update(nominal_v=52,dump_start_v=54.35,dump_full_v=54.5,trip_v=57)
    if not supply['adjustment_min_v']<=52<=supply['adjustment_max_v']:
        raise ConfigError('revision source setpoint outside documented adjustment range')
    cfg['upstream_buffer']={key:assumptions[key] for key in ('input_capacitance_f','output_added_capacitance_f',
                                                          'diode_resistance_ohm','diode_offset_v')}
    cfg['upstream_buffer'].update(on_delta_v=clamp['activation_over_input_typ_v'],off_delta_v=clamp['deactivation_over_input_typ_v'])
    return cfg,parts,variants,derived,source


def revision_fingerprint(root):
    root=Path(root);h=hashlib.sha256(candidate_fingerprint(root).encode())
    for file in ('data/revision_components.yaml','src/odrt/upstream_buffer.py','src/odrt/revision_power.py'):
        source=Path(__file__).with_name(Path(file).name) if file.startswith('src/') else root/file
        h.update(file.encode()+b'\0'+source.read_bytes())
    return h.hexdigest()


def run(root=Path('.')):
    root=Path(root);initial_hash=revision_fingerprint(root);inputs=load_inputs(root)
    cfg,parts,variants,derived,source=load_revision(root);criteria=load_engineering(root)[0]
    output=root/'build/engineering/revision_power';output.mkdir(parents=True,exist_ok=True)
    selected={'single_heavy_full','paired_heavy_full','single_fast_full','single_endurance_full',
              'left_power_loss_buffered_coordinated','paired_dump_failure_coordinated'}
    results={}
    for bank in ('compact_nominal','compact_aged'):
        selected_cfg,selected_parts=copy.deepcopy(cfg),copy.deepcopy(parts)
        selected_cfg['reference']['capacitor']='revision_cell';selected_parts['revision_cell']={'values':variants[bank]}
        results[bank]={}
        for case in cfg['cases']:
            if case['name'] not in selected:continue
            print(f'power revision {bank}: {case["name"]}',flush=True)
            try:
                value=simulate(selected_cfg,selected_parts,inputs.scenarios[case['scenario']],inputs.defaults,2,case,
                               model_factory=build_upstream_model)
            except RuntimeError as error:
                results[bank][case['name']]={'solver_failure':str(error),'numerical_valid':False};continue
            m,s=value['metrics'],value['signals'];time=s['t'];duration=time[-1]
            m['assessment']=assess_case(m,selected_cfg,selected_parts,case,criteria)
            m['numerical_valid']=bool(m['energy_residual_fraction']<=criteria['energy_residual_fraction_max']['value']
                                     and all(np.isfinite(v).all() for v in s.values()))
            for unit in range(case['units']):
                p=f'unit_{unit}.';on_current=s[p+'bus_v']/cfg['power']['dump_resistance_ohm']
                m[p+'clamp_brake_rms_a']=float(np.sqrt(np.trapz(s[p+'clamp_duty_average']*on_current**2,time)/duration))
                m[p+'clamp_forward_max_a']=float(s[p+'clamp_forward_a'].max())
                m[p+'clamp_static_activation_bound_v']=float(s[p+'input_bus_v'].max()+source['regen_clamp']['facts']['activation_over_input_max_v'])
                m[p+'dump_energy_j']=float(np.trapz(s[p+'dump_w'],time))
            trace=output/f'{bank}__{case["name"]}.npz';np.savez_compressed(trace,**s)
            m['trace']=str(trace.relative_to(root));results[bank][case['name']]=m
            print(f'  tracking {100*m["unit_0.tracking_fraction"]:.2f}%; trip {m["unit_0.trip_reason"]}; '
                  f'energy residual {m["energy_residual_fraction"]:.3g}',flush=True)
    if revision_fingerprint(root)!=initial_hash:raise ConfigError('power revision inputs changed during study')
    result={'fingerprint':initial_hash,'scope':'six selected cases per bank; no independent resolution verification yet',
            'assessment':'REVISE; power topology experiment only','reference':cfg['reference'],'power':cfg['power'],
            'topology':cfg['upstream_buffer'],'component_sources':source,'inertia':derived['inertia'],'banks':results,
            'limits':['Upstream storage cannot recover motor regeneration; reverse flow is blocked and energy is dumped.',
                'The clamp is cycle-averaged across hysteresis endpoints. Switching ripple/delay/15kHz limit and peaks are not resolved.',
                'Clamp conduction heat is added to the existing drive thermal node; separate board hotspot/OTP is unvalidated.',
                'Extra clamp board and input capacitance are not fitted into the CAD; R1 failed supports are unchanged.',
                'Pro voltage utilization/frequency screens and thermal paths remain stated model assumptions; phase conventions need calibration.']}
    (root/'reports/revision_power.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    lines=['# Higher-voltage upstream-buffer power experiment','',f'Fingerprint: `{initial_hash}`','',
           '**REVISE: this is a topology experiment, not a selected complete machine.** '
           'The bank is upstream of a reverse-blocking Regen Clamp and cannot receive regenerated motor energy. '
           'A separate input-link state, one-way forward drop, clamp loss and relative-input averaged dump '
           'replace the bidirectional bank/DC-link path. Source, capacitor and dump thermal powers and '
           'stored energy are updated in the same plant.','',
           'Candidates: [ODrive Pro]('+source['odrive_pro']['source']+'), '
           '[EPP-500-54]('+source['epp500_54']['source']+') adjusted within its documented range to 52 V, and '
           '[Regen Clamp]('+source['regen_clamp']['source']+'). Accessed 2026-11-02; availability/prices unverified. '
           'The original EPP-500-48 cannot provide 52 V within its 45.6–50.4 V documented range.','',
           '| Bank / case | Tracking % | Bus min–max V (averaged) | Trip | Brake RMS A | Dump J | Energy residual | Failed checks |',
           '|---|---:|---:|---|---:|---:|---:|---|']
    for bank,cases in results.items():
        for case,m in cases.items():
            if 'solver_failure' in m:lines.append(f'| {bank} / {case} | — | — | solver failure | — | — | — | unresolved |');continue
            failed=sorted({f for row in m['assessment'] for f in row['failed_checks']})
            lines.append(f'| {bank} / {case} | {100*m["unit_0.tracking_fraction"]:.2f} | '
                f'{m["minimum_bus_v"]:.2f}–{m["maximum_bus_v"]:.2f} | {m["unit_0.trip_reason"] or "none"} | '
                f'{m["unit_0.clamp_brake_rms_a"]:.2f} | {m["unit_0.dump_energy_j"]:.1f} | '
                f'{m["energy_residual_fraction"]:.3g} | {", ".join(failed) or "none in listed screens"} |')
    lines+=['','## Limits','']+['- '+v for v in result['limits']]
    lines+=['','Capacitance placement and diode drop are explicit proposals in `data/revision_components.yaml`. '
            'Averaged voltages and current screens cannot establish switching-peak compliance. No physical '
            'braking/resistor/thermal qualification follows from this experiment. Selected convergence and '
            'the complete suite are still required before adoption.','',
            'Reproduce: `.venv/bin/python -m odrt.revision_power`.','']
    (root/'reports/revision_power.md').write_text('\n'.join(lines))
    return result


if __name__=='__main__':
    result=run()
    if any(not m.get('numerical_valid',False) for cases in result['banks'].values() for m in cases.values()):
        raise SystemExit('power revision has unresolved numerical cases')
