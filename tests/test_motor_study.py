"""Motor study: candidate data conversion and variant validation."""
import math

import pytest

from conftest import REPO
from odrt.config import ConfigError, load_yaml


def test_candidate_dc_port_matches_datasheet_conventions():
    from odrt.motor_study import load_candidates
    tbm = load_candidates(REPO)['tbm2g_11526d']; d, v = tbm['datasheet'], tbm['values']
    # Kt_dc is the cold line-line peak back-EMF per rad/s.
    assert v['kt_nm_per_a'] == pytest.approx(d['ke_cold_vrms_per_krpm_ll']*math.sqrt(2)/(1000*2*math.pi/60), rel=1e-3)
    # Power consistency: Kt_dc * sqrt(3/2) is the rms-current torque constant (cold).
    assert v['kt_nm_per_a']*math.sqrt(1.5) == pytest.approx(d['kt_cold_nm_per_arms'], rel=0.01)
    # Km is convention-free: cold Kt over sqrt of copper loss per rms amp squared (1.5 * R_ll for a star winding).
    assert d['kt_cold_nm_per_arms']/math.sqrt(1.5*d['resistance_ll_ohm']) == pytest.approx(v['km_nm_per_sqrt_w'], rel=0.02)
    assert v['inertia_kg_m2'] == pytest.approx(d['inertia_kg_cm2']*1e-4)


def test_motor_variants_are_valid_and_unknown_keys_fail():
    pytest.importorskip('cadquery'); pytest.importorskip('casadi')
    from odrt.motor_study import apply_variant, load_candidates, motor_summary
    from odrt.r2_candidate import load_r4
    cfg, parts, *_ = load_r4(REPO); candidates = load_candidates(REPO)
    spec = load_yaml(REPO/'configs/motor_study.yaml')
    for changes in spec['variants'].values():
        apply_variant(cfg, parts, candidates, changes)
    c, q = apply_variant(cfg, parts, candidates, {'motor': 'tbm2g_11526d', 'reference': {'ratio': 6.0},
                                                  'thermal_scale': {'winding_to_housing_k_w': 2}})
    assert c['reference']['motor'] == 'tbm2g_11526d' and cfg['reference']['motor'] != 'tbm2g_11526d'
    assert c['thermal']['winding_to_housing_k_w'] == pytest.approx(2*cfg['thermal']['winding_to_housing_k_w'])
    # The candidate's lower back-EMF constant raises the speed ceiling even at a higher ratio.
    assert motor_summary(q, c)['model_no_load_drum_rpm'] > motor_summary(parts, cfg)['model_no_load_drum_rpm']
    for bad in ({'motor': 'ro200'}, {'control': {'not_a_gain': 1}}, {'mechanics': {}},
                {'thermal_scale': {'ambient_c': 2}}):
        with pytest.raises(ConfigError):
            apply_variant(cfg, parts, candidates, bad)
