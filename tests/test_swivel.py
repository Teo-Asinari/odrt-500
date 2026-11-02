"""Swivel exit load and grip checks."""
import math

import pytest

from conftest import REPO
from odrt import swivel as sw


@pytest.fixture(scope="module")
def cfg():
    return sw.load_swivel(REPO / "configs/swivel.yaml")


def test_vertical_pull_loads_nothing_sideways(cfg):
    r = sw.case(cfg, 0.0, 500.0)
    assert r["exit_axle_n"] == 0 and r["bearing_radial_n"] == 0 and r["mu_needed"] == 0


def test_exit_axle_load_formula(cfg):
    r = sw.case(cfg, 60.0, 200.0)
    t = 200 * 4.4482216152605 * cfg.snap_factor
    assert r["exit_axle_n"] == pytest.approx(2 * t * math.sin(math.radians(30)))


def test_grip_limit_is_friction_cone(cfg):
    assert sw.max_safe_tension_lbf(cfg, math.degrees(math.atan(cfg.deck_mu)) - 1) == float("inf")
    t = sw.max_safe_tension_lbf(cfg, 60.0)
    r = sw.case(cfg, 60.0, t)
    assert r["mu_needed"] == pytest.approx(cfg.deck_mu, rel=1e-9)
