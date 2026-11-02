"""Electronics budget and packaging checks."""
import pytest
import yaml

from conftest import REPO
from odrt import electronics as el
from odrt.project import load_inputs


@pytest.fixture(scope="module")
def budget():
    return el.budget(load_inputs(REPO), yaml.safe_load((REPO / "configs/electronics.yaml").read_text()))


def test_awg_table():
    assert el.awg_for_area(2.0) == 14   # 2.08 mm2
    assert el.awg_for_area(8.0) == 8    # 8.37 mm2


def test_motor_current_from_torque(budget):
    inputs = load_inputs(REPO)
    opt = inputs.options[inputs.structure.design]
    # Unit peak torque / Kt, within the peak seen over the heavy set.
    from odrt.units import lbf_to_n
    radius = opt.architecture.drum_core_radius_m + inputs.common.cable_diameter_m / 2
    tau = lbf_to_n(inputs.envelope.peak_tension_lbf) * radius / (opt.external_ratio * opt.efficiency)
    assert budget["motor_peak_current_a"] >= 0.95 * tau / opt.component.kt_nm_per_a


def test_buffer_esr_scales_with_cells(budget):
    cfg = yaml.safe_load((REPO / "configs/electronics.yaml").read_text())
    assert budget["buffer_esr_small_ohm"] == pytest.approx(cfg["cells_in_series"] * cfg["small_cell_esr_ohm"])
    assert budget["buffer_loss_small_w"] / budget["buffer_loss_large_w"] == pytest.approx(
        cfg["small_cell_esr_ohm"] / cfg["large_cell_esr_ohm"])


def test_parts_file_rejects_uncited_cited_dims(tmp_path):
    import csv
    rows = list(csv.DictReader((REPO / "data/electronics.csv").open()))
    next(row for row in rows if row["dims_basis"].startswith("cited"))["source_url"] = ""
    path = tmp_path / "e.csv"
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    from odrt.config import ConfigError
    with pytest.raises(ConfigError, match="https"):
        el.load_electronics(path)


def test_current_modular_packaging_has_no_interferences():
    pytest.importorskip("cadquery")
    from odrt import cad
    from odrt.cli import structural_summary
    from odrt.drivetrain import Drum
    from odrt.modular import load_modular, placement
    inputs = load_inputs(REPO)
    st = inputs.structure
    opt = inputs.options[st.design]
    parts, geo = cad.build(st, opt, inputs.common, structural_summary(inputs, {}))
    assert cad.interferences(parts) == []
    bounds = [p.shape.val().BoundingBox() for p in parts]
    bb = (min(b.xmin for b in bounds), min(b.ymin for b in bounds), min(b.zmin for b in bounds),
          max(b.xmax for b in bounds), max(b.ymax for b in bounds), max(b.zmax for b in bounds))
    layout = placement(load_modular(REPO / 'configs/modular.yaml'), bb,
                       Drum(opt.architecture, inputs.common).width_m * 1000,
                       (0, 0, geo['cable_exit_height_mm']), el.load_electronics(REPO / 'data/electronics.csv'))
    assert layout['clashes'] == []
