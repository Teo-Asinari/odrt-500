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


def test_r4_moves_bank_to_drive_bus_and_keeps_r3c_controller():
    pytest.importorskip('cadquery'); pytest.importorskip('casadi')
    from odrt.r2_candidate import load_r3c, load_r4, model_factory
    r3c, *_ = load_r3c(REPO); cfg, *_ , derived, _, _ = load_r4(REPO)
    assert cfg['power_topology'] == 'bidirectional' and 'power_topology' not in r3c
    assert cfg['control'] == r3c['control']
    assert cfg['power']['trip_v'] == 56 < r3c['power']['trip_v'] == 57
    assert {k: v for k, v in cfg['power'].items() if k != 'trip_v'} == {k: v for k, v in r3c['power'].items() if k != 'trip_v'}
    assert derived['r4_power']['proposal']['topology'] == 'bidirectional'
    # The bank-on-bus model is the base coupled model wrapped by the frame heat path.
    model_factory(cfg)


def test_r4_power_checks_flag_cell_voltage_and_continuous_rms():
    pytest.importorskip('cadquery'); pytest.importorskip('casadi')
    from odrt.r2_candidate import load_r4, power_checks
    cfg, parts, variants, derived, _, _ = load_r4(REPO)
    n = cfg['power']['cell_series']; rating = variants['r2_fresh']['current_rms_15k_rise_a']
    base = {'duration_s': 10., 'unit_0.max_capacitor_v': 52., 'unit_0.capacitor_rms_a': 1.,
            'unit_0.supply_peak_a': 5., 'unit_0.max_capacitor_c': 26.}
    cases = {'r2_fresh': {'a': dict(base)}, 'r2_aged': {'a': dict(base, **{'unit_0.capacitor_rms_a': 2*rating})}}
    k = power_checks(derived['r4_power'], cases, parts, cfg, variants)
    assert k['cell_voltage_pass'] and k['max_bank_v'] == 52.
    assert not k['rms_pass'] and k['rms_exceeding_cases'] == ['r2_aged/a']
    assert k['continuous_repetition_cell_c']['r2_aged'] > k['continuous_repetition_cell_c']['r2_fresh']
    cases['r2_fresh']['a']['unit_0.max_capacitor_v'] = 3.0*n
    assert not power_checks(derived['r4_power'], cases, parts, cfg, variants)['cell_voltage_pass']


@pytest.mark.slow
def test_r4_dump_monitor_catches_fresh_dump_failure_without_false_trips():
    pytest.importorskip('cadquery'); pytest.importorskip('casadi')
    from odrt.engineering import load_engineering
    from odrt.project import load_inputs
    from odrt.r2_candidate import _job, load_r4
    inputs = load_inputs(REPO); cfg, parts, variants, *_ = load_r4(REPO)
    parts['r2_cell'] = {'values': variants['r2_fresh']}; criteria = load_engineering(REPO)[0]
    cases = {c['name']: c for c in cfg['cases']}
    def run(name, window):
        case = dict(cases[name], window_s=window)
        return _job(('case', (name,), cfg, parts, inputs.scenarios[case['scenario']], inputs.defaults,
                     inputs.envelope.max_usable_stroke_m, case, {}, criteria, None))[2]
    fault = run('paired_dump_failure', 2.5)
    assert fault['unit_0.trip_reason'] == 'dump_fault' and fault['unit_1.trip_reason'] is None
    assert fault['maximum_bus_v'] < cfg['power']['trip_v']
    assert fault['unit_0.trip_time_s'] - cases['paired_dump_failure']['fault_time_s'] < 1.
    normal = run('single_fast_full', 6)
    assert not normal['unit_0.trip_latched'] and normal['numerical_valid']


@pytest.mark.slow
def test_gate_rule_survives_tolerance_corners_where_estimated_rule_false_trips():
    pytest.importorskip('cadquery'); pytest.importorskip('casadi')
    from odrt.config import load_yaml
    from odrt.monitor_study import _job, corner_config
    from odrt.project import load_inputs
    from odrt.r2_candidate import load_r4
    inputs = load_inputs(REPO); cfg, parts, variants, *_ = load_r4(REPO)
    assert cfg['dump_monitor']['duty_source'] == 'gate'
    spec = load_yaml(REPO/'configs/monitor_study.yaml'); parts['r2_cell'] = {'values': variants['r2_fresh']}
    cases = {c['name']: c for c in cfg['cases']}
    def run(corner, rule, name):
        c = corner_config(cfg, spec, spec['corners'][corner]); c['dump_monitor']['duty_source'] = rule
        case = cases[name]
        return _job((name, c, parts, inputs.scenarios[case['scenario']], inputs.defaults,
                     inputs.envelope.max_usable_stroke_m, case))[1]['units']
    assert run('false_trip_corner', 'estimated', 'single_fast_full')[0]['trip_reason'] == 'dump_fault'
    assert run('false_trip_corner', 'gate', 'single_fast_full')[0]['trip_reason'] is None
    fault = run('missed_detection_corner', 'gate', 'paired_dump_failure')
    assert fault[0]['trip_reason'] == 'dump_fault' and fault[1]['trip_reason'] is None
