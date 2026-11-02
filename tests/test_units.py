import numpy as np
import pytest

from odrt.units import LB_TO_KG, LBF_TO_N, cable_power_w, lb_to_kg, lbf_to_n, n_to_lbf


def test_lbf_definition_is_exact():
    assert LBF_TO_N == pytest.approx(4.4482216152605, abs=1e-12)


def test_500_lbf_in_newtons():
    assert lbf_to_n(500) == pytest.approx(2224.11, abs=0.01)


def test_round_trip_arrays():
    f = np.array([0.0, 5.0, 20.0, 500.0])
    np.testing.assert_allclose(n_to_lbf(lbf_to_n(f)), f, rtol=1e-15)


def test_mass_and_force_are_distinct():
    assert lb_to_kg(1.0) == LB_TO_KG
    assert lbf_to_n(1.0) != lb_to_kg(1.0)


def test_drum_torque_from_brief():
    # DESIGN.md section 5: 500 lbf at r_eff = 0.020 m is about 44.5 N*m.
    assert lbf_to_n(500) * 0.020 == pytest.approx(44.5, abs=0.05)


@pytest.mark.parametrize("speed, expected_w", [(0.1, 222), (0.25, 556), (0.5, 1112), (1.0, 2224)])
def test_power_table_from_brief(speed, expected_w):
    assert cable_power_w(lbf_to_n(500), speed) == pytest.approx(expected_w, abs=0.6)


def test_power_sign_convention():
    assert cable_power_w(100.0, 0.5) > 0   # extension: device absorbs
    assert cable_power_w(100.0, -0.5) < 0  # retraction: device returns energy
