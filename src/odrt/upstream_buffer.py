"""Energy-consistent upstream storage and reverse-blocking clamp extension.

The bulk bank and source feed an input DC link. An ideal-diode approximation
feeds the drive link; regeneration cannot flow back to storage. The external
clamp uses an averaged relative-input voltage characteristic, not switching-
level emulation. Retain that distinction when interpreting peaks or protection.
"""
from __future__ import annotations

import numpy as np

from odrt.coupled import GLOBAL_FIELDS,UNIT_FIELDS,build_model


def build_upstream_model(cfg,parts,scenario,defaults,stroke_m,case,**perturbations):
    import casadi as ca
    original=build_model(cfg,parts,scenario,defaults,stroke_m,case,**perturbations)
    topology=cfg['upstream_buffer'];n=case['units'];old_size=len(UNIT_FIELDS)
    fields=UNIT_FIELDS+('input_bus_v',);size=len(fields)
    x=ca.SX.sym('upstream_state',4+n*size);t=original['t'];parameter=original['p']
    projected=ca.vertcat(x[:4],*[x[4+i*size:4+i*size+old_size] for i in range(n)])
    substitute=lambda expr:ca.substitute(expr,original['x'],projected)
    old_ode=substitute(original['ode']);quad=substitute(original['quad'])
    old_obs=original['observables'](t,projected,parameter)
    observables=dict(zip(original['observable_names'],ca.vertsplit(old_obs)))
    energy=original['energy'](projected);rhs=list(ca.vertsplit(old_ode[:4]));initial=list(original['state0'][:4])
    cold=cfg['power']['bus_capacitance_f'];cin=topology['input_capacitance_f']
    cout=cold+topology['output_added_capacitance_f'];cap_c=original['capacitance_f'];cap_r=original['esr_ohm']
    cell=parts[cfg['reference']['capacitor']]['values']
    cap_heat_c=cell['thermal_capacity_j_per_k']*cfg['power']['cell_series']*cfg['power']['cell_parallel']
    efficiency=parts[cfg['reference']['supply']]['values']['efficiency_nominal']
    for i in range(n):
        base=4+i*size;old_base=4+i*old_size;prefix=f'unit_{i}.'
        get=lambda field:x[base+UNIT_FIELDS.index(field)]
        vb,vc,vi=get('bus_v'),get('capacitor_v'),x[base+old_size]
        old_source=observables[prefix+'supply_bus_w']
        old_source_i=old_source/ca.fmax(vb,1e-9)
        new_source=ca.substitute(old_source,vb,vi)
        new_source_i=new_source/ca.fmax(vi,1e-9)
        cap_current=(vc-vi)/cap_r
        forward=ca.fmax((vi-vb-topology['diode_offset_v'])/topology['diode_resistance_ohm'],0)
        diode_loss=forward*(topology['diode_offset_v']+topology['diode_resistance_ohm']*forward)
        duty=ca.fmin(ca.fmax((vb-vi-topology['off_delta_v'])/(topology['on_delta_v']-topology['off_delta_v']),0),1)
        if i==0 and case['fault']=='dump_failure':
            duty=ca.if_else(t>case['fault_time_s'],0,duty)
        dump=duty*vb*vb/cfg['power']['dump_resistance_ohm']
        old_dump=observables[prefix+'dump_w'];old_cap=observables[prefix+'capacitor_current_a']
        # Recover unchanged drive+bleed consumption from the original bus balance.
        old_bus_dot=old_ode[old_base+UNIT_FIELDS.index('bus_v')]
        consumption=old_cap+old_source_i-old_dump/ca.fmax(vb,1e-9)-cold*old_bus_dot
        local=list(ca.vertsplit(old_ode[old_base:old_base+old_size]))
        local[UNIT_FIELDS.index('capacitor_v')]=-cap_current/cap_c
        local[UNIT_FIELDS.index('bus_v')]=(forward-consumption-dump/ca.fmax(vb,1e-9))/cout
        local[UNIT_FIELDS.index('capacitor_c')]+=(cap_current**2*cap_r-observables[prefix+'esr_w'])/cap_heat_c
        local[UNIT_FIELDS.index('supply_c')]+=(new_source-old_source)*(1/efficiency-1)/cfg['thermal']['supply_capacity_j_k']
        local[UNIT_FIELDS.index('drive_c')]+=diode_loss/cfg['thermal']['drive_capacity_j_k']
        local[UNIT_FIELDS.index('dump_c')]+=(dump-old_dump)/cfg['thermal']['dump_capacity_j_k']
        rhs+=local+[(cap_current+new_source_i-forward)/cin]
        quad[1]+=(new_source-old_source)/efficiency
        energy+=.5*cin*vi*vi+.5*(cout-cold)*vb*vb
        initial+=list(original['state0'][old_base:old_base+old_size])+[cfg['power']['nominal_v']]
        observables[prefix+'capacitor_current_a']=cap_current
        observables[prefix+'esr_w']=cap_current**2*cap_r
        observables[prefix+'supply_bus_w']=new_source
        observables[prefix+'dump_w']=dump
        observables[prefix+'clamp_forward_a']=forward
        observables[prefix+'clamp_loss_w']=diode_loss
        observables[prefix+'clamp_duty_average']=duty
        observables[prefix+'input_supply_current_a']=new_source_i
    event_index=ca.SX.sym('event_index')
    physical_post=original['transition'](event_index,t,projected)
    post=ca.vertcat(physical_post[:4],*[ca.vertcat(physical_post[4+i*old_size:4+(i+1)*old_size],x[4+i*size+old_size]) for i in range(n)])
    ode=ca.vertcat(*rhs)
    model=dict(original)
    model.update(x=x,ode=ode,quad=quad,energy=ca.Function('upstream_energy',[x],[energy]),
        observables=ca.Function('upstream_observables',[t,x,parameter],[ca.vertcat(*observables.values())]),
        observable_names=list(observables),state_names=list(GLOBAL_FIELDS)+[f'unit_{i}.{f}' for i in range(n) for f in fields],
        state0=np.array(initial),unit_fields=fields,zero=substitute(original['zero']),
        transition=ca.Function('upstream_transition',[event_index,t,x],[post]),
        normal_targets=ca.Function('upstream_targets',[t,x],[original['normal_targets'](t,projected)]),
        rhs=ca.Function('upstream_rhs',[t,x,parameter],[ode,quad]))
    return model
