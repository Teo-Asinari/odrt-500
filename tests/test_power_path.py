"""R4 power-path sizing on a synthetic envelope."""
import math

import pytest

from conftest import REPO
from odrt.config import ConfigError, load_yaml


def envelope(rms=10., peak=30., bank_v=53.5, bus_v=54.4, supply_a=9., trips=False):
    m = {'unit_0.capacitor_rms_a': rms, 'unit_0.capacitor_peak_a': peak, 'unit_0.max_capacitor_v': bank_v,
         'unit_0.supply_peak_a': supply_a, 'unit_0.dump_average_peak_a': 20., 'unit_0.trip_latched': trips, 'maximum_bus_v': bus_v, 'minimum_bus_v': 45.}
    cell = {'capacitance_f': 100., 'esr_initial_max_ohm': .011, 'voltage_rated_v': 3., 'case_max_c': 65}
    return {'power': {'cell_series': 20, 'nominal_v': 52., 'trip_v': 57., 'dump_start_v': 54.35, 'dump_full_v': 54.5,
                      'dump_resistance_ohm': 1., 'bleed_resistance_ohm': 1e4},
            'cell_values': {'r2_fresh': cell, 'r2_aged': dict(cell, capacitance_f=63., esr_initial_max_ohm=.022)},
            'banks': {'r2_fresh': {'a': m, 'paired_dump_failure': dict(m, maximum_bus_v=55.6)}, 'r2_aged': {'a': dict(m)}},
            'derived': {'r4_power': {'functions': {'precharge': {'enable_threshold_v': 45}}},
                        'r4_checks': {'continuous_repetition_cell_c': {'r2_fresh': 40., 'r2_aged': 60.}}}}


def size(r4):
    from odrt.power_path import size
    return size(r4, load_yaml(REPO/'data/power_path.yaml'), load_yaml(REPO/'data/revision_components.yaml'))


def test_precharge_holds_supply_current_and_discharges_bank():
    out = size(envelope())
    pc = out['precharge_discharge']
    assert pc['supply_current_a'] < pc['supply_limit_a']
    fresh = next(x for x in pc['rows'] if x['bank'] == 'r2_fresh')
    assert fresh['time_to_enable_s'] < fresh['time_to_bypass_s']
    assert fresh['tau_s'] == pytest.approx(pc['resistor_ohm']*5.)
    # Charging a capacitor through a resistor dissipates the energy it stores (to the bypass point).
    assert fresh['precharge_energy_j'] == pytest.approx(5*52*47-.5*5*47**2)
    assert fresh['discharge_time_s'] == pytest.approx(fresh['tau_s']*math.log(53.5/5))


def test_bank_protection_and_balancing_scale_with_envelope():
    low, high = size(envelope()), size(envelope(rms=20., bank_v=56.))
    assert high['bank_protection']['fuse_min_rating_a'] == 2*low['bank_protection']['fuse_min_rating_a']
    assert (low['bank_protection']['prospective_fault_a']['r2_aged']
            < low['bank_protection']['prospective_fault_a']['r2_fresh'])
    b = low['balancing']
    assert b['worst_cell_at_max_bank_v'] > 53.5/20 and b['normal_below_monitor'] and b['trip_below_rating']
    assert high['balancing']['worst_cell_at_max_bank_v'] > b['worst_cell_at_max_bank_v']


def test_incomplete_envelope_is_refused():
    r4 = envelope(); r4['banks']['r2_aged']['bad'] = {'solver_failure': 'x'}
    with pytest.raises(ConfigError):
        size(r4)
