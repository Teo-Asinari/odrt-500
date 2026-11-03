"""R2 integration: CAD/support agreement and candidate configuration."""
import itertools

import pytest

from conftest import REPO
from odrt.config import load_yaml


def test_support_screen_reproduces_comparison_corners_and_scales_with_load():
    from odrt.support_revision import screen
    spec = load_yaml(REPO/'data/revision_support.yaml'); p = spec['revision_proposal']
    existing = load_yaml(REPO/'data/compact_structure.yaml')['assumptions']
    rows, difference, _ = screen(spec, existing, p['rope_force_comparison_n'], p['motor_torque_comparison_nm'])
    assert len(rows) == len(p['pretension_per_span_n'])*len(p['rope_height_range_mm'])*2
    assert all(r['max_force_residual_n'] < 1e-6 for r in rows)
    heavier, _, _ = screen(spec, existing, 2*p['rope_force_comparison_n'], p['motor_torque_comparison_nm'])
    assert all(h['drum_bearing_static_factor'] < r['drum_bearing_static_factor'] for h, r in zip(heavier, rows))
    assert difference == pytest.approx(p['motor_torque_comparison_nm']/(p['pinion_teeth']*p['pitch_mm']/(2*3.141592653589793)/1000))


def test_r2_candidate_uses_r2_ratio_bank_and_cad_inertia():
    pytest.importorskip('cadquery'); pytest.importorskip('casadi')
    from odrt.r2_candidate import load_r2
    cfg, parts, variants, derived, _, support = load_r2(REPO)
    p = support['revision_proposal']
    assert cfg['reference']['ratio'] == p['wheel_teeth']/p['pinion_teeth'] == 5
    assert cfg['power']['cell_series'] == p['cells_series']
    assert cfg['power']['trip_v'] < variants['r2_fresh']['voltage_rated_v']*p['cells_series']
    assert variants['r2_aged']['capacitance_f'] < variants['r2_fresh']['capacitance_f']
    assert variants['r2_aged']['esr_initial_max_ohm'] > variants['r2_fresh']['esr_initial_max_ohm']
    assert cfg['reference']['drum_inertia_kg_m2'] == derived['inertia']['equivalent_added_drum_inertia_kg_m2']
    assert cfg['upstream_buffer']['input_capacitance_f'] > 0


def test_r2_cad_fits_owner_body_without_clashes_and_places_every_cell():
    pytest.importorskip('cadquery')
    from odrt.r2_package import build, check
    objects, _, info = build(REPO)
    collisions, bounds, keepouts = check(objects, info)
    assert not collisions and not bounds
    assert not any(keepouts.values())
    cells = [o for o in objects if o.name.startswith('capacitor_')]
    assert len(cells) == info['proposal']['cells_series']
    # Every bearing named in the support screen sits where the screen assumes it.
    p = info['proposal']
    for name, centres in (('motor_bearing', p['motor_bearing_centres_mm']), ('drum_bearing', p['drum_bearing_centres_mm'])):
        found = sorted(o.shape.val().Center().z for o in objects if o.name[:-1] == name+'_')
        assert found == pytest.approx(centres, abs=1e-6)
    deck = next(o for o in objects if o.name == 'deck').shape.val().BoundingBox()
    assert (deck.zmin+deck.zmax)/2 == pytest.approx(p['shaft_support_z_mm'][1])


def test_frame_heat_path_keeps_energy_ledger_closed_and_cools_long_duty():
    pytest.importorskip('casadi')
    from odrt.engineering import load_engineering
    from odrt.project import load_inputs
    from odrt.r2_candidate import _job, load_r3
    inputs = load_inputs(REPO); cfg, parts, variants, _, _, _ = load_r3(REPO)
    parts['r2_cell'] = {'values': variants['r2_fresh']}
    case = dict(next(c for c in cfg['cases'] if c['name'] == 'paired_heavy_full'), window_s=8)
    criteria = load_engineering(REPO)[0]
    args = lambda c: ('case', ('x',), c, parts, inputs.scenarios[case['scenario']], inputs.defaults,
                      inputs.envelope.max_usable_stroke_m, case, {}, criteria, None)
    _, _, with_frame = _job(args(cfg))
    without = {k: v for k, v in cfg.items() if k != 'frame_thermal'}
    _, _, bare = _job(args(without))
    assert with_frame['energy_residual_fraction'] < criteria['energy_residual_fraction_max']['value']
    assert with_frame['worst_winding_c'] <= bare['worst_winding_c']


def test_optional_controller_keys_default_to_reference_and_unknown_keys_fail(repo_copy):
    from conftest import edit_yaml
    from odrt.config import ConfigError
    from odrt.coupled import CONTROL_DEFAULTS, OPTIONAL_KEYS, load_coupled
    assert set(CONTROL_DEFAULTS) == set(OPTIONAL_KEYS['control'])
    assert all(v == 0 for v in CONTROL_DEFAULTS.values())  # zero = reference behaviour
    edit_yaml(repo_copy/'configs/coupled.yaml', lambda d: d['control'].update(acceleration_blend=1.0))
    load_coupled(repo_copy)
    edit_yaml(repo_copy/'configs/coupled.yaml', lambda d: d['control'].update(not_a_gain=1.0))
    with pytest.raises(ConfigError):
        load_coupled(repo_copy)
