"""Independent free-body/section checks for the compact structural screen."""
import math

import numpy as np
import pytest

from odrt.compact_structure import bearing_reactions,shaft_stress


def test_overhung_load_requires_opposite_reaction_and_magnifies_near_bearing():
    lower,upper,force_error,moment_error=bearing_reactions((0,10),[(20,(100,0))])
    np.testing.assert_allclose(lower,[100,0])
    np.testing.assert_allclose(upper,[-200,0])
    assert force_error<1e-12 and moment_error<1e-12


def test_two_axis_reactions_obey_separate_force_and_moment_balance():
    loads=[(5,(100,40)),(15,(-20,30))]
    lower,upper,force_error,moment_error=bearing_reactions((0,10),loads)
    np.testing.assert_allclose(upper,[-20,-65])
    np.testing.assert_allclose(lower,[-60,-5])
    assert force_error<1e-12 and moment_error<1e-12


def test_circular_shaft_stress_has_correct_units_and_cubic_size_scaling():
    # 1000 Nmm bending on a 10 mm shaft gives 32/pi MPa.
    assert shaft_stress(1000,0,10)==pytest.approx(32/math.pi)
    assert shaft_stress(0,1000,10)==pytest.approx(math.sqrt(3)*16/math.pi)
    assert shaft_stress(1000,500,20)==pytest.approx(shaft_stress(1000,500,10)/8)
