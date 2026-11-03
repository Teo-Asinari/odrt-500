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
                      'dump_resistance_ohm': 1., 'bleed_resistance_ohm': 1e4, 'supply_droop_ohm': .2,
                      'bus_capacitance_f': .003, 'drive_idle_w': 3.},
            'cell_values': {'r2_fresh': cell, 'r2_aged': dict(cell, capacitance_f=63., esr_initial_max_ohm=.022)},
            'banks': {'r2_fresh': {'a': m, 'paired_dump_failure': dict(m, maximum_bus_v=55.6)}, 'r2_aged': {'a': dict(m)}},
            'derived': {'r4_power': {'functions': {'precharge': {'enable_threshold_v': 45},
                                                     'dump_monitor': {'detection_s': .1, 'min_expected_a': 2, 'measured_fraction': .5, 'backup_bus_v': 55.}}},
                        'r4_checks': {'continuous_repetition_cell_c': {'r2_fresh': 40., 'r2_aged': 60.}}}}


def size(r4):
    from odrt.power_path import size
    return size(r4, load_yaml(REPO/'data/power_path.yaml'), load_yaml(REPO/'data/revision_components.yaml'))


def test_precharge_holds_supply_current_and_discharges_bank():
    out = size(envelope())
    pc = out['precharge_discharge']
    assert pc['supply_current_a'] < pc['supply_limit_a']
    fresh = next(x for x in pc['rows'] if x['bank'] == 'r2_fresh')
    assert fresh['time_to_enable_s'] == fresh['time_to_bypass_s']  # enable waits for bypass closure
    assert fresh['bypass_inrush_a'] < pc['supply_limit_a']
    assert fresh['tau_s'] == pytest.approx(pc['resistor_ohm']*5.)
    # Charging a capacitor through a resistor dissipates the energy it stores (to the bypass point).
    vc = 52-fresh['bypass_close_delta_v']
    assert fresh['precharge_energy_j'] == pytest.approx(5*52*vc-.5*5*vc**2)
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


def sequence_params(bank='r2_fresh'):
    from odrt.precharge import parameters
    spec = load_yaml(REPO/'data/power_path.yaml'); components = load_yaml(REPO/'data/revision_components.yaml')
    return parameters(envelope(), spec, components, bank)


def test_resistor_precharge_never_reaches_supply_limit_and_enables_after_bypass():
    from odrt.precharge import run_sequence
    q = sequence_params()
    b = run_sequence(q, 'resistor')
    assert b['drive_enabled'] and b['enable_s'] >= b['bypass_s'] and 'charged_s' in b
    assert b['supply_peak_a'] < q['limit'] and b['supply_at_limit_s'] == 0
    a = run_sequence(q, 'supply_cc')
    assert a['supply_at_limit_s'] > 0 and a['charged_s'] < b['charged_s']  # faster, but needs constant-current mode


def test_bypass_failing_open_keeps_drive_disabled_and_discharge_reaches_safe_voltage():
    from odrt.precharge import run_discharge, run_sequence
    q = sequence_params('r2_aged')
    fault = run_sequence(q, 'resistor', 'bypass_open')
    assert not fault['drive_enabled'] and 'bypass_timeout_s' in fault
    d = run_discharge(q, 53.5)
    assert d['safe_s'] == pytest.approx(q['c_bank']*(q['r_pre']+q['esr']+q['wiring'])*math.log(53.5/q['safe_v']), rel=.05)
    assert d['bus_below_aux_minimum_s'] < 1  # supervisor loses power: discharge switch must be normally closed
