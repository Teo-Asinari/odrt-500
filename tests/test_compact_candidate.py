"""Cross-check the CAD/coupled interface through independent stored energy."""
import numpy as np
import pytest

pytest.importorskip('cadquery')
pytest.importorskip('casadi')

from conftest import REPO
from odrt.compact_candidate import load_candidate
from odrt.coupled import UNIT_FIELDS,build_model
from odrt.project import load_inputs


@pytest.fixture(scope='module')
def candidate():
    return load_candidate(REPO)


def test_cad_reflected_inertia_is_present_once_in_plant_energy(candidate):
    _,cfg,parts,variants,derived=candidate
    inputs=load_inputs(REPO)
    parts=dict(parts,compact_cell={'values':variants['compact_nominal']})
    cfg['reference']['capacitor']='compact_cell'
    case=dict(name='energy_probe',units=1,fault='none')
    model=build_model(cfg,parts,inputs.scenarios['heavy_tempo_limit'],inputs.defaults,2,case)
    before=model['state0'].copy();after=before.copy()
    after[4+UNIT_FIELDS.index('omega_rad_s')]=1
    delta=float(model['energy'](after)-model['energy'](before))
    assert 2*delta==pytest.approx(derived['inertia']['complete_known_reflected_inertia_kg_m2'],rel=1e-8)
    assert model['rotor_inertia_kg_m2']>.024
    assert model['capacitance_f']==pytest.approx(100/22)


def test_air_flow_heat_balance_matches_volume_and_conditional_flow(candidate):
    spec,cfg,_,_,derived=candidate
    # Unit conversion independently: 25 ft³/min = 11.798686 litres/sec.
    flow_l_s=spec['airflow_cfm']*28.316846592/60
    expected=flow_l_s/1000*1.2*1005
    assert derived['air_to_room_w_k']==pytest.approx(expected)
    assert cfg['thermal']['air_capacity_j_k']==pytest.approx(.323*.139*.100*1.2*1005)
    assert cfg['thermal']['air_capacity_j_k']<6
