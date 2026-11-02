"""Independent load checks and invalid-input coverage for ADR-002 integration."""
import math

import pytest

from conftest import REPO, edit_yaml
from odrt.config import ConfigError
from odrt.modular import board_check, box_clashes, load_modular, mount_cases, placement
from odrt.project import load_inputs


def test_centred_force_is_shared_by_four_bolts():
    interface = load_modular(REPO / 'configs/modular.yaml')['interface']
    cases = mount_cases(4000, (0, 0, 0), interface)
    normal = next(r for r in cases if r['case'] == 'normal +1')
    vertical = next(r for r in cases if r['case'] == 'vertical +1')
    assert normal['bolt_tension_n'] == pytest.approx(1000)
    assert normal['bolt_shear_n'] == 0
    assert vertical['bolt_tension_n'] == 0
    assert vertical['bolt_shear_n'] == pytest.approx(1000)


def test_eccentric_vertical_pull_adds_tension_couple():
    interface = load_modular(REPO / 'configs/modular.yaml')['interface']
    row = next(r for r in mount_cases(4000, (0, 200, 0), interface) if r['case'] == 'vertical +1')
    assert row['moment_nm'] == pytest.approx(800)
    # Two bolts in the tensile row, with 120 mm between rows.
    assert row['bolt_tension_n'] == pytest.approx(800 / (.12 * 2))
    assert row['bolt_shear_n'] == pytest.approx(1000)
    assert row['stress_mpa'] == pytest.approx(math.sqrt((800 / .24)**2 + 3 * 1000**2) / 36.6)


def test_board_matches_four_point_bending():
    board = load_modular(REPO / 'configs/modular.yaml')['board']
    r = board_check(board, 4000)
    # 200 mm overhang: M=800 Nm, section modulus 0.65*0.025²/6.
    assert r['stress_mpa'] == pytest.approx(800 / (.65 * .025**2 / 6) / 1e6)
    # Doubling thickness gives 1/4 stress and 1/8 deflection.
    thick = board_check(dict(board, thickness_mm=50), 4000)
    assert thick['stress_mpa'] == pytest.approx(r['stress_mpa'] / 4)
    assert thick['deflection_mm'] == pytest.approx(r['deflection_mm'] / 8)
    assert not r['deflection_ok']


@pytest.mark.parametrize('mutate', [
    lambda d: d.__setitem__('units', 1),
    lambda d: d['interface'].__setitem__('bolt_spacing_mm', [200, 0]),
    lambda d: d['board'].__setitem__('foot_half_spacing_mm', 500),
    lambda d: d['board'].__setitem__('youngs_gpa', float('nan')),
])
def test_invalid_modular_input_is_rejected_by_check(repo_copy, mutate):
    edit_yaml(repo_copy / 'configs/modular.yaml', mutate)
    with pytest.raises(ConfigError):
        load_inputs(repo_copy)


def test_placement_detects_overlap_and_includes_every_electrical_item():
    from odrt.electronics import load_electronics
    cfg = load_modular(REPO / 'configs/modular.yaml')
    el = load_electronics(REPO / 'data/electronics.csv')
    p = placement(cfg, (-170,-180,0,170,135,170), 72, (0,0,117), el)
    assert p['clashes'] == []
    ids = {b['name'] for b in p['electronics']}
    assert set(el) - {'presence_pad','cap_cell','cap_cell_large'} <= ids
    assert 'cap_bank' in ids
    for box in p['electronics']:
        assert all(box['corner'][j] >= 0 and box['corner'][j]+box['dims'][j] <= p['dimensions_mm'][j]
                   for j in range(3))
    assert box_clashes([dict(name='a',corner=(0,0,0),dims=(2,2,2)),
                        dict(name='b',corner=(1,1,1),dims=(2,2,2))]) == [('a','b',1)]
