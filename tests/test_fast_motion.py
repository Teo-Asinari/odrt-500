"""Fast-motion study: variant validation, voltage-saturation diagnostic and storage topology."""
import pytest

from conftest import REPO
from odrt.config import ConfigError, load_yaml


def test_study_variants_are_valid_and_unknown_keys_fail():
    pytest.importorskip('cadquery'); pytest.importorskip('casadi')
    from odrt.fast_motion_study import apply_variant
    from odrt.r2_candidate import load_r3c
    cfg, parts, *_ = load_r3c(REPO)
    spec = load_yaml(REPO/'configs/fast_motion_study.yaml')
    for changes in spec['variants'].values():
        apply_variant(cfg, parts, changes)
    c, _, _, topology = apply_variant(cfg, parts, {'reference': {'ratio': 4.0}, 'topology': 'bidirectional'})
    assert c['reference']['ratio'] == 4.0 and cfg['reference']['ratio'] == 5 and topology == 'bidirectional'
    for bad in ({'control': {'not_a_gain': 1}}, {'mechanics': {}}, {'topology': 'battery'},
                {'sensitivity': {'cable_ea_scale': 2}}):
        with pytest.raises(ConfigError):
            apply_variant(cfg, parts, bad)


@pytest.mark.slow
def test_fast_reversal_is_voltage_limited_and_bidirectional_bank_recovers_regen():
    pytest.importorskip('cadquery'); pytest.importorskip('casadi')
    from odrt.engineering import load_engineering
    from odrt.fast_motion_study import _job
    from odrt.project import load_inputs
    from odrt.r2_candidate import load_r3c
    inputs = load_inputs(REPO); cfg, parts, banks, *_ = load_r3c(REPO)
    parts['r2_cell'] = {'values': banks['r2_fresh']}
    criteria = load_engineering(REPO)[0]
    cases = {c['name']: c for c in cfg['cases']}

    def run(name, topology, window):
        case = dict(cases[name], window_s=window)
        args = ((name,), cfg, parts, topology, inputs.scenarios[case['scenario']], inputs.defaults,
                inputs.envelope.max_usable_stroke_m, case, {}, criteria)
        return _job(args)[1]

    clamp, bidirectional = run('single_fast_full', 'clamp', 8), run('single_fast_full', 'bidirectional', 8)
    for m in (clamp, bidirectional):
        assert m['numerical_valid']
    # Most of the clamp-topology error occurs on the back-EMF/bus bound.
    assert clamp['unit_0.voltage_limited_fraction'] > .3
    assert clamp['unit_0.voltage_limited_error_share'] > .6
    # A bank that can absorb regeneration dumps less and sags less.
    assert bidirectional['unit_0.dump_mean_w'] < .5*clamp['unit_0.dump_mean_w']
    assert bidirectional['unit_0.min_capacitor_v'] > clamp['unit_0.min_capacitor_v']
    # The heavy tempo is not voltage-limited.
    heavy = run('single_heavy_full', 'clamp', 6)
    assert heavy['unit_0.voltage_limited_fraction'] < .02
