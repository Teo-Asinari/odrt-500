"""Custom motor sizing: fit quality and internal consistency."""
import math

import pytest

from conftest import REPO
from odrt import motor_sizing as ms


@pytest.fixture(scope="module")
def fit():
    return ms.fit(ms.load_family(REPO / "data/motor_family.csv"))


def test_fit_reproduces_family_km_within_15pct(fit):
    assert fit.errors["km2"] < 0.15


def test_stack_solution_inverts_km_law(fit):
    for od, km in ((0.105, 0.6), (0.13, 1.0), (0.21, 3.5)):
        L = ms.stack_for_km(fit, od, km)
        r = ms.r_from_od(fit, od)
        assert math.sqrt(ms.km2_law(fit, r, L)) == pytest.approx(km, rel=1e-9)


def test_bigger_diameter_needs_shorter_stack(fit):
    assert ms.stack_for_km(fit, 0.16, 1.0) < ms.stack_for_km(fit, 0.105, 1.0)


def test_copper_scales_with_inverse_km_squared(fit):
    from odrt.project import load_inputs
    inputs = load_inputs(REPO)
    a = ms.evaluate(inputs, ms.size(fit, "a", 0.13, 0.6), 6, 0.95, 140)
    b = ms.evaluate(inputs, ms.size(fit, "b", 0.13, 1.2), 6, 0.95, 140)
    assert a["copper_peak_w"] / b["copper_peak_w"] == pytest.approx(4.0, rel=1e-9)
