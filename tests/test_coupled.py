"""Independent conservation, port, symmetry and fault-contract tests."""
import dataclasses
import copy
from pathlib import Path

import numpy as np
import pytest

ca = pytest.importorskip('casadi')

from conftest import REPO, edit_yaml
from odrt.config import ConfigError
from odrt.coupled import UNIT_FIELDS, build_model, load_coupled, simulate, winding_map
from odrt.project import load_inputs
from odrt.scenarios import Scenario, scenario_duration_s


@pytest.fixture(scope='module')
def setup():
    inputs = load_inputs(REPO)
    cfg,parts = load_coupled(REPO,inputs.scenarios)
    scenario = Scenario(name='hold',description='stationary analytical check',kind='limit',requirements=('R-01',),
                        assumptions=('A-016',),start_offset_m=.5,stroke_m=0,
                        extend_s=.1,top_hold_s=.2,retract_s=.1,bottom_hold_s=.2,reps=1,sets=1,rest_s=0,
                        extension_tension_lbf=100,retraction_tension_lbf=100)
    return inputs,cfg,parts,scenario


def test_layer_map_is_continuous_with_consistent_radius(setup):
    _,cfg,parts,_ = setup
    reference=cfg['reference'];diameter=parts[reference['rope']]['values']['diameter_mm']/1000
    s,q,r = winding_map(reference,diameter,2)
    assert s[0]==0 and s[-1]==2
    np.testing.assert_allclose(np.diff(s)/np.diff(q),r,rtol=1e-12)
    np.testing.assert_allclose(r,[.0375,.0325],rtol=1e-12)
    for i in range(1,len(q)-1):
        assert s[i-1]+r[i-1]*(q[i]-q[i-1])==pytest.approx(s[i])


def test_energy_derivative_matches_external_work_and_heat(setup):
    inputs,cfg,parts,scenario = setup
    case=dict(name='probe',units=2,fault='none')
    model=build_model(cfg,parts,scenario,inputs.defaults,2,case)
    x=model['x'];t=model['t'];p=model['p']
    residual=ca.Function('instant_energy',[t,x,p],[ca.jacobian(model['energy'](x),x)@model['ode']-
                                                 (model['quad'][0]+model['quad'][1]-model['quad'][2])])
    state=model['state0'].copy()
    state[1]=.1;state[2]=.01;state[3]=-.03
    for unit in (0,1):
        base=4+unit*len(UNIT_FIELDS)
        state[base+UNIT_FIELDS.index('omega_rad_s')]=2.2
        state[base+UNIT_FIELDS.index('torque_nm')]=.4
        state[base+UNIT_FIELDS.index('winding_c')]=70
        state[base+UNIT_FIELDS.index('housing_c')]=40
        state[base+UNIT_FIELDS.index('capacitor_v')]=48
        state[base+UNIT_FIELDS.index('bus_v')]=47.5
    assert float(residual(.9,state,np.zeros(2)))==pytest.approx(0,abs=1e-6)


def test_capacitor_and_winding_storage_use_actual_component_values(setup):
    inputs,cfg,parts,scenario=setup
    model=build_model(cfg,parts,scenario,inputs.defaults,2,dict(name='probe',units=1,fault='none'))
    x0=model['state0'].copy()
    assert model['capacitance_f']==pytest.approx(350/22)
    assert model['esr_ohm']==pytest.approx(22*.0032)
    cap=4+UNIT_FIELDS.index('capacitor_v')
    x1=x0.copy();x1[cap]+=1
    assert float(model['energy'](x1)-model['energy'](x0))==pytest.approx(.5*(350/22)*(49**2-48**2))
    winding=4+UNIT_FIELDS.index('winding_c')
    x1=x0.copy();x1[winding]+=1
    assert float(model['energy'](x1)-model['energy'](x0))==pytest.approx(48.3)


def test_esr_current_and_heat_follow_ohms_law(setup):
    inputs,cfg,parts,scenario=setup
    model=build_model(cfg,parts,scenario,inputs.defaults,2,dict(name='probe',units=1,fault='none'))
    state=model['state0'].copy()
    state[4+UNIT_FIELDS.index('capacitor_v')]=48
    state[4+UNIT_FIELDS.index('bus_v')]=47
    obs=dict(zip(model['observable_names'],np.array(model['observables'](0,state,[0])).ravel()))
    assert obs['unit_0.capacitor_current_a']==pytest.approx(1/(22*.0032))
    assert obs['unit_0.esr_w']==pytest.approx(1/(22*.0032))
    assert obs['unit_0.gear_w']>=-1e-9


def test_paired_normal_is_symmetric_and_conserves_energy(setup):
    inputs,cfg,parts,scenario=setup
    case=dict(name='pair',units=2,fault='none')
    res=simulate(cfg,parts,scenario,inputs.defaults,2,case)
    sig=res['signals']
    assert sig['t'][-1]==pytest.approx(scenario_duration_s(scenario,inputs.defaults))
    assert res['metrics']['energy_residual_fraction']<1e-5
    assert res['metrics']['max_bar_angle_deg']<1e-3
    np.testing.assert_allclose(sig['unit_0.tension_n'],sig['unit_1.tension_n'],atol=.02)
    assert sig['unit_0.tension_n'].min()>=0
    assert sig['unit_0.esr_w'].min()>=0
    assert sig['unit_0.gear_w'].min()>=-1e-8
    assert sig['unit_0.cable_damping_w'].min()>=-1e-8


def test_peer_stop_reduces_bar_rotation_without_changing_local_stop(setup):
    inputs,cfg,parts,_=setup
    scenario=inputs.scenarios['heavy_tempo_limit']
    common=dict(name='loss',scenario=scenario.name,units=2,fault='mains_loss_braked',fault_time_s=2.6,window_s=4)
    off=simulate(cfg,parts,scenario,inputs.defaults,2,dict(common,peer_stop=False))
    on=simulate(cfg,parts,scenario,inputs.defaults,2,dict(common,peer_stop=True))
    assert on['metrics']['max_bar_angle_deg']<off['metrics']['max_bar_angle_deg']
    for r in (off,on):
        t=r['signals']['t'];after=t>2.6
        assert np.all(r['signals']['unit_0.local_stop'][after])
        assert r['metrics']['energy_residual_fraction']<1e-5
    assert not off['signals']['unit_1.local_stop'].any()
    assert on['signals']['unit_1.local_stop'].any()


def test_frozen_command_latches_actual_controller_output(setup):
    inputs,cfg,parts,_=setup
    case=next(c for c in cfg['cases'] if c['name']=='left_torque_frozen')
    r=simulate(cfg,parts,inputs.scenarios[case['scenario']],inputs.defaults,2,case)
    s=r['signals'];t=s['t'];after=t>case['fault_time_s']
    values=s['unit_0.target_torque_nm'][after]
    assert np.ptp(values)<1e-10
    before=np.flatnonzero(t<=case['fault_time_s'])[-1]
    assert values[0]==pytest.approx(s['unit_0.target_torque_nm'][before],abs=1e-8)
    assert r['metrics']['energy_residual_fraction']<1e-5


@pytest.mark.parametrize('group,key,value',[
    ('power','trip_v',60),('power','cell_series',1),('power','supply_droop_ohm',0),
    ('reference','efficiency',1.1),('reference','motor','imaginary'),
    ('control','force_filter_s',0),('thermal','winding_capacity_j_k',-1),
    ('solver','relative_tolerance',float('nan')),
])
def test_invalid_coupled_inputs_fail(repo_copy,group,key,value):
    edit_yaml(repo_copy/'configs/coupled.yaml',lambda d:d[group].__setitem__(key,value))
    with pytest.raises(ConfigError):
        load_coupled(repo_copy)


def test_symmetric_release_is_not_seeded_by_separate_unit_roundoff(setup):
    inputs,cfg,parts,_=setup
    case=next(c for c in cfg['cases'] if c['name']=='paired_release')
    r=simulate(cfg,parts,inputs.scenarios[case['scenario']],inputs.defaults,2,case)
    assert r['metrics']['max_bar_angle_deg']<.01
    assert r['metrics']['energy_residual_fraction']<1e-5


def test_coupled_fingerprint_is_input_location_independent(repo_copy):
    from odrt.coupled import fingerprint
    assert fingerprint(repo_copy)==fingerprint(REPO)
    old=fingerprint(repo_copy)
    edit_yaml(repo_copy/'configs/coupled.yaml',lambda d:d['power'].__setitem__('cell_parallel',2))
    assert fingerprint(repo_copy)!=old


def test_trip_transition_changes_no_energy_bearing_state_and_is_permanent(setup):
    inputs,cfg,parts,scenario=setup
    model=build_model(cfg,parts,scenario,inputs.defaults,2,dict(name='probe',units=2,fault='none'))
    before=model['state0'].copy()
    before[4+UNIT_FIELDS.index('bus_v')]=cfg['power']['undervoltage_v']
    after=np.array(model['transition'](0,2.3,before)).ravel()
    assert float(model['energy'](after)-model['energy'](before))==pytest.approx(0,abs=1e-10)
    assert after[4+UNIT_FIELDS.index('trip_latched')]==1
    assert after[4+UNIT_FIELDS.index('trip_time_s')]==2.3
    assert after[4+UNIT_FIELDS.index('trip_reason')]==1
    # Restore nominal bus: the event state and inhibit must persist.
    after[4+UNIT_FIELDS.index('bus_v')]=48
    obs=dict(zip(model['observable_names'],np.array(model['observables'](3,after,[0,0])).ravel()))
    assert not obs['unit_0.drive_enabled']
    assert obs['unit_1.drive_enabled']
    np.testing.assert_array_equal(np.array(model['transition'](0,3,after)).ravel(),after)


def test_simultaneous_paired_trip_does_not_create_artificial_asymmetry(setup):
    inputs,cfg,parts,scenario=setup
    model=build_model(cfg,parts,scenario,inputs.defaults,2,dict(name='probe',units=2,fault='none'))
    before=model['state0'].copy()
    for unit in range(2):
        before[4+unit*len(UNIT_FIELDS)+UNIT_FIELDS.index('bus_v')]=50
    after=np.array(model['transition'](1,1.2,before)).ravel()
    np.testing.assert_array_equal(after[4:4+len(UNIT_FIELDS)],after[4+len(UNIT_FIELDS):])
    assert after[4+UNIT_FIELDS.index('trip_reason')]==2


@pytest.mark.parametrize('case_name,reason',[
    ('left_power_loss_buffered_coordinated','undervoltage'),
    ('paired_dump_failure_coordinated','overvoltage')])
def test_compact_bank_crossing_latches_and_stops_peer_after_delay(setup,case_name,reason):
    from odrt.buffer_study import candidate_variants
    from odrt.config import load_yaml
    inputs,cfg,parts,_=setup
    cfg,parts=copy.deepcopy(cfg),copy.deepcopy(parts)
    parts['compact']={'values':candidate_variants(load_yaml(REPO/'data/compact_buffer.yaml'))['compact_nominal']}
    cfg['reference']['capacitor']='compact'
    cfg['solver']['max_steps']=2000
    case=next(c for c in cfg['cases'] if c['name']==case_name)
    result=simulate(cfg,parts,inputs.scenarios[case['scenario']],inputs.defaults,2,case)
    metrics,signals=result['metrics'],result['signals']
    assert metrics['unit_0.trip_reason']==reason
    assert metrics['energy_residual_fraction']<1e-5
    trip_time=metrics['unit_0.trip_time_s']
    latched=signals['unit_0.trip_latched']>.5
    assert latched.any() and np.all(np.diff(latched.astype(int))>=0)
    assert not signals['unit_0.drive_enabled'][latched].any()
    before=signals['t']<trip_time
    peer_before=signals['t']<trip_time+cfg['control']['peer_stop_delay_s']
    peer_after=signals['t']>trip_time+cfg['control']['peer_stop_delay_s']+1e-7
    assert signals['unit_0.drive_enabled'][before].all()
    assert signals['unit_1.drive_enabled'][peer_before].all()
    assert not signals['unit_1.drive_enabled'][peer_after].any()


def test_initial_overtemperature_is_latched_without_waiting_for_crossing(setup):
    inputs,cfg,parts,scenario=setup
    model=build_model(cfg,parts,scenario,inputs.defaults,2,dict(name='hot',units=1,fault='none'),ambient_offset_c=45)
    state=model['state0']
    assert state[4+UNIT_FIELDS.index('trip_latched')]==1
    assert state[4+UNIT_FIELDS.index('trip_reason')]==5
    obs=dict(zip(model['observable_names'],np.array(model['observables'](0,state,[0])).ravel()))
    assert not obs['unit_0.drive_enabled']


def test_independent_bdf_event_fallback_matches_analytic_decay_and_quadrature(monkeypatch):
    from odrt.coupled import _integrate_segment
    t=ca.SX.sym('t');x=ca.SX.sym('x',2);p=ca.SX.sym('p',0)
    index=ca.SX.sym('index');z=ca.SX.sym('z',0);u=ca.SX.sym('u',0)
    dae=dict(t=t,x=x,p=p,ode=ca.vertcat(ca.if_else(x[1]>.5,0,-x[0]),0),
             quad=ca.vertcat(x[0],0,0),zero=ca.if_else(x[1]>.5,1,x[0]-.5))
    transition=ca.Function('analytic_transition',[index,t,x,z,p,u],
                           [ca.vertcat(x[0],1),z],ca.event_in(),ca.event_out())
    class FailingBackend:
        def __call__(self,**kwargs):raise RuntimeError('CV_ILL_INPUT: injected interpolation failure')
    monkeypatch.setattr(ca,'integrator',lambda *args,**kwargs:FailingBackend())
    grid=np.linspace(0,1.5,301)
    states,work,stats,metadata=_integrate_segment('analytic',dae,0,grid,
        dict(transition=transition,max_events=2,reltol=1e-8,abstol=1e-10,max_step_size=.002),
        np.array([1.,0]),np.array([]))
    crossing=np.log(2)
    np.testing.assert_allclose(states[0],np.maximum(np.exp(-grid),.5),atol=2e-7)
    np.testing.assert_allclose(work[0],np.where(grid<=crossing,1-np.exp(-grid),.5+.5*(grid-crossing)),atol=2e-7)
    assert np.all(states[1,grid>crossing]==1)
    assert metadata['backend']=='SciPy BDF'
    assert 'CV_ILL_INPUT' in metadata['fallback_reason']


def test_bdf_fallback_handles_two_events_between_output_samples(monkeypatch):
    from odrt.coupled import _integrate_segment
    t=ca.SX.sym('t');x=ca.SX.sym('x',4);p=ca.SX.sym('p',0)
    index=ca.SX.sym('index');z=ca.SX.sym('z',0);u=ca.SX.sym('u',0)
    dae=dict(t=t,x=x,p=p,ode=ca.vertcat(ca.if_else(x[1]>.5,0,-x[0]),0,
                                      ca.if_else(x[3]>.5,0,-x[2]),0),quad=ca.SX.zeros(3),
             zero=ca.vertcat(ca.if_else(x[1]>.5,1,x[0]-.5),ca.if_else(x[3]>.5,1,x[2]-.49995)))
    post=ca.vertcat(x[0],ca.if_else(index==0,1,x[1]),x[2],ca.if_else(index==1,1,x[3]))
    transition=ca.Function('adjacent_transition',[index,t,x,z,p,u],[post,z],ca.event_in(),ca.event_out())
    class FailingBackend:
        def __call__(self,**kwargs):raise RuntimeError('CV_ILL_INPUT: injected interpolation failure')
    monkeypatch.setattr(ca,'integrator',lambda *args,**kwargs:FailingBackend())
    grid=np.arange(0,1.005,.005)
    states,_,_,_=_integrate_segment('adjacent',dae,0,grid,
        dict(transition=transition,max_events=3,reltol=1e-8,abstol=1e-10,max_step_size=.002),
        np.array([1.,0,1.,0]),np.array([]))
    assert states[0,-1]==pytest.approx(.5,abs=2e-7)
    assert states[2,-1]==pytest.approx(.49995,abs=2e-7)
    assert states[1,-1]==states[3,-1]==1
