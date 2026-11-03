"""Independent checks of source/assumption separation in the buffer experiment."""
from pathlib import Path

import pytest

from odrt.buffer_study import candidate_variants
from odrt.config import load_yaml


def test_compact_corner_combines_initial_tolerance_and_relative_aging():
    spec = load_yaml(Path(__file__).parents[1]/'data/compact_buffer.yaml')
    variants = candidate_variants(spec)
    assert variants['compact_nominal']['capacitance_f'] == 100
    assert variants['compact_initial_min']['capacitance_f'] == 90
    aged = variants['compact_aged']
    assert aged['capacitance_f'] == pytest.approx(63)
    assert aged['esr_initial_max_ohm'] == pytest.approx(.024)
    assert aged['capacitance_f']/22 == pytest.approx(2.86363636)
    assert aged['esr_initial_max_ohm']*22 == pytest.approx(.528)
    assert aged['diameter_mm'] == 18.5  # use maximum, not nominal, for space claim
    assert 'thermal_capacity_j_per_k' not in spec['documented']


def test_thermal_brackets_do_not_change_electrical_corner_or_source():
    spec = load_yaml(Path(__file__).parents[1]/'data/compact_buffer.yaml')
    variants = candidate_variants(spec)
    assert spec['documented']['capacitance_f'] == 100
    assert spec['documented']['esr_initial_max_ohm'] == .012
    low, high = (variants['compact_aged_'+suffix] for suffix in
                 ('low_heat_capacity', 'high_heat_capacity'))
    assert low['thermal_capacity_j_per_k'] == 10
    assert high['thermal_capacity_j_per_k'] == 40
    assert {k: v for k, v in low.items() if k != 'thermal_capacity_j_per_k'} == {
        k: v for k, v in high.items() if k != 'thermal_capacity_j_per_k'}
