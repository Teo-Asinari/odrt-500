"""Independent architecture calculations, component conflicts and target validation."""
import math

import pytest

from conftest import REPO, edit_yaml
from odrt.config import ConfigError
from odrt.engineering import candidate, compatibility_issues, fits_envelope, load_engineering
from odrt.project import input_hash, load_inputs


@pytest.fixture(scope='module')
def data():
    return load_engineering(REPO)


def test_owner_envelope_matches_voltra_and_rejects_volume_only_fit(data):
    criteria, _, _, _ = data
    dims = [criteria[k]['value'] for k in ('unit_length_mm_max','unit_width_mm_max','unit_height_mm_max')]
    assert dims == [323, 139, 100]
    assert math.prod(dims)/1e6 == pytest.approx(criteria['unit_volume_l_max']['value'])
    assert criteria['unit_volume_l_max']['origin'] == 'owner'
    assert criteria['unit_mass_kg_max']['origin'] == 'provisional'
    assert fits_envelope((100,323,139), dims)
    assert not fits_envelope((20,20,2000), dims)  # only 0.8 L; cannot fit any orientation


def test_drive_conflict_uses_actual_manufacturer_rating(data):
    drive = data[1]['odrive_s1']['values']
    assert drive['voltage_absolute_max_v'] == 50.5
    original = dict(nominal_v=48, dump_on_v=56, overvoltage_v=60)
    assert len(compatibility_issues(original, drive)) == 2
    assert compatibility_issues(dict(nominal_v=48, dump_on_v=49, overvoltage_v=50), drive) == []
    assert compatibility_issues(dict(nominal_v=48, dump_on_v=49, overvoltage_v=50.5), drive)


def test_winding_capacity_torque_and_rotor_energy_against_hand_calc(data):
    criteria, parts, cfg, _ = data
    r = candidate(criteria,parts,cfg,'ro100_lite','dynaone_hs_5',25,6,3,6,'guided','folded_3m')
    expected = 6*2*math.pi*(.0275+.0325+.0375)-3*2*math.pi*.0275
    assert r['usable_capacity_m'] == pytest.approx(expected)
    assert r['radius_min_mm'] == pytest.approx(27.5)
    assert r['radius_max_mm'] == pytest.approx(37.5)
    force = 250 * 4.4482216152605
    assert r['motor_torque_at_peak_nm'] == pytest.approx(force*.0375/(6*.95))
    inertia = (.0003+6**2*.000529)/.0275**2
    assert r['effective_mass_kg'] == pytest.approx(inertia)
    assert r['reflected_kinetic_energy_j'] == pytest.approx(.5*inertia*.95**2)


def test_direct_drive_and_rope_failures_are_explicit(data):
    criteria, parts, cfg, _ = data
    r = candidate(criteria,parts,cfg,'ro100_standard','dynaone_hs_4',25,18,1,1,'guided','folded_3m')
    assert 'motor peak torque' in r['failures']
    assert 'reference transient rope strength' in r['failures']
    assert not r['screen_checks_pass']
    # 5 mm spliced strength, not unspliced linear strength, is the comparison basis.
    r = candidate(criteria,parts,cfg,'ro100_standard','dynaone_hs_5',25,18,1,1,'guided','folded_3m')
    assert 'reference transient rope strength' not in r['failures']
    assert r['spliced_strength_n'] == 30000


def test_fleet_distance_and_loss_sensitivity_are_independent_of_guided_proposal(data):
    criteria, parts, cfg, _ = data
    a = candidate(criteria,parts,cfg,'ro100_lite','dynaone_hs_5',25,6,3,6,'unguided','folded_3m')
    b = candidate(criteria,parts,cfg,'ro100_lite','dynaone_hs_5',25,6,3,6,'guided','folded_3m')
    assert a['lead_mm'] == pytest.approx(15/math.tan(math.radians(4)))
    assert b['lead_mm'] == 90
    assert a['motor_torque_at_peak_nm'] == b['motor_torque_at_peak_nm']
    assert a['copper_low_km_w']/a['copper_nominal_w'] == pytest.approx((.53/.34)**2)


@pytest.mark.parametrize('rel,mutate', [
    ('requirements/engineering.yaml', lambda d:d['criteria']['unit_volume_l_max'].__setitem__('origin','approved-by-model')),
    ('requirements/engineering.yaml', lambda d:d['criteria']['force_peak_lbf'].__setitem__('value',float('nan'))),
    ('configs/engineering.yaml', lambda d:d['study'].__setitem__('routings',[])),
    ('configs/engineering.yaml', lambda d:d['study'].__setitem__('motors',['imaginary'])),
    ('configs/engineering.yaml', lambda d:d['study'].__setitem__('turns_per_layer',[1.5])),
    ('configs/engineering.yaml', lambda d:d['study'].__setitem__('capacitor_series',2.5)),
    ('data/engineering_components.yaml', lambda d:d['components']['odrive_s1'].__setitem__('source','http://example.com')),
    ('data/engineering_components.yaml', lambda d:d['components']['odrive_s1']['values'].__setitem__('voltage_absolute_max_v',-1)),
])
def test_invalid_engineering_data_rejected_by_standard_input_loader(repo_copy,rel,mutate):
    edit_yaml(repo_copy/rel, mutate)
    with pytest.raises(ConfigError):
        load_inputs(repo_copy)


def test_requirement_and_vendor_data_change_project_fingerprint(repo_copy):
    before = input_hash(repo_copy)
    edit_yaml(repo_copy/'data/engineering_components.yaml',
              lambda d:d['components']['odrive_s1']['values'].__setitem__('voltage_absolute_max_v',51))
    assert input_hash(repo_copy) != before
