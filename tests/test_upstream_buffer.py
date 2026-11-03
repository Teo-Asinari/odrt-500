"""Independent port/storage checks for the upstream reverse-blocking topology."""
import numpy as np
import pytest

ca=pytest.importorskip('casadi')
pytest.importorskip('cadquery')

from conftest import REPO
from odrt.coupled import UNIT_FIELDS
from odrt.project import load_inputs
from odrt.revision_power import load_revision
from odrt.upstream_buffer import build_upstream_model


@pytest.fixture(scope='module')
def model():
    cfg,parts,variants,_,_=load_revision(REPO);inputs=load_inputs(REPO)
    cfg['reference']['capacitor']='cell';parts['cell']={'values':variants['compact_aged']}
    return build_upstream_model(cfg,parts,inputs.scenarios['heavy_tempo_limit'],inputs.defaults,2,
                                dict(name='probe',units=2,fault='none'))


def test_upstream_port_obeys_full_instantaneous_energy_identity(model):
    x=model['x'];residual=ca.Function('residual',[model['t'],x,model['p']],
        [ca.jacobian(model['energy'](x),x)@model['ode']-(model['quad'][0]+model['quad'][1]-model['quad'][2])])
    state=model['state0'].copy();size=len(model['unit_fields'])
    for i in range(2):
        base=4+i*size
        state[base+UNIT_FIELDS.index('bus_v')]=51.98
        state[base+UNIT_FIELDS.index('omega_rad_s')]=3
        state[base+UNIT_FIELDS.index('torque_nm')]=2
        state[base+UNIT_FIELDS.index('capacitor_v')]=52.5
    assert float(residual(1.4,state,[0,0]))==pytest.approx(0,abs=2e-6)


def test_reverse_blocking_prevents_bus_regeneration_entering_bank(model):
    state=model['state0'].copy();size=len(model['unit_fields'])
    for i in range(2):state[4+i*size+UNIT_FIELDS.index('bus_v')]=54
    obs=dict(zip(model['observable_names'],np.array(model['observables'](1,state,[0,0])).ravel()))
    assert obs['unit_0.clamp_forward_a']==0
    assert obs['unit_0.capacitor_current_a']==0
    assert obs['unit_0.dump_w']>0
    assert obs['unit_0.clamp_loss_w']==0


def test_input_link_storage_is_real_and_separate_from_drive_bus(model):
    before=model['state0'].copy();after=before.copy()
    after[4+model['unit_fields'].index('input_bus_v')]=53
    delta=float(model['energy'](after)-model['energy'](before))
    assert delta==pytest.approx(.5*.003*(53**2-52**2),abs=1e-9)
