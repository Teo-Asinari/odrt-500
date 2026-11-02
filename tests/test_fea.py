"""Side-plate FEA sanity checks (coarse mesh; skipped without the [fea] extra)."""
import pytest

from conftest import REPO
from odrt.project import load_inputs

pytest.importorskip("gmsh")
pytest.importorskip("skfem")

from odrt import cad, fea  # noqa: E402
from odrt.cli import structural_summary  # noqa: E402


@pytest.fixture(scope="module")
def dims_force():
    inputs = load_inputs(REPO)
    st = inputs.structure
    sizes = structural_summary(inputs, {})
    return cad.layout(st, inputs.options[st.design], inputs.common, sizes), sizes["bearing_radial_load_n"], st


def test_applied_load_matches_target(dims_force):
    dims, force, st = dims_force
    r = fea.side_plate(dims, force, st.plate.youngs_gpa * 1e9, st.plate.poisson, 10)
    assert r["applied_force_n"] == pytest.approx(force, rel=0.01)


def test_stress_scales_linearly_with_load(dims_force):
    dims, force, st = dims_force
    a = fea.side_plate(dims, force, st.plate.youngs_gpa * 1e9, st.plate.poisson, 10)
    b = fea.side_plate(dims, 2 * force, st.plate.youngs_gpa * 1e9, st.plate.poisson, 10)
    assert b["max_von_mises_mpa"] == pytest.approx(2 * a["max_von_mises_mpa"], rel=1e-6)


def test_stiffer_material_deflects_less(dims_force):
    dims, force, st = dims_force
    al = fea.side_plate(dims, force, 69e9, 0.33, 10)
    steel = fea.side_plate(dims, force, 200e9, 0.33, 10)
    assert steel["max_displacement_mm"] == pytest.approx(al["max_displacement_mm"] * 69 / 200, rel=1e-6)


def test_bore_breakout_shows_up_as_missing_load(dims_force):
    """Regression for the layout bug the FEA caught: a bore cut through the plate top loses load area."""
    dims, force, st = dims_force
    broken = dict(dims, plate_h=dims["axis_z"] + dims["bearing_od"] / 2 - 8)
    r = fea.side_plate(broken, force, st.plate.youngs_gpa * 1e9, st.plate.poisson, 10)
    assert r["applied_force_n"] < 0.97 * force
