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
    # 500 lbf hold torque / Kt, within the peak seen over the set
    tau = 2224.11 * 0.027 / (opt.external_ratio * opt.efficiency)
    assert budget["motor_peak_current_a"] >= 0.95 * tau / opt.component.kt_nm_per_a


def test_buffer_esr_scales_with_cells(budget):
    cfg = yaml.safe_load((REPO / "configs/electronics.yaml").read_text())
    assert budget["buffer_esr_small_ohm"] == pytest.approx(cfg["cells_in_series"] * cfg["small_cell_esr_ohm"])
    assert budget["buffer_loss_small_w"] / budget["buffer_loss_large_w"] == pytest.approx(
        cfg["small_cell_esr_ohm"] / cfg["large_cell_esr_ohm"])


def test_parts_file_rejects_uncited_cited_dims(tmp_path):
    import csv
    rows = list(csv.DictReader((REPO / "data/electronics.csv").open()))
    rows[0]["source_url"] = ""
    path = tmp_path / "e.csv"
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    from odrt.config import ConfigError
    with pytest.raises(ConfigError, match="https"):
        el.load_electronics(path)


def test_packaging_has_no_interferences():
    pytest.importorskip("cadquery")
    import json
    from odrt import cad, packaging
    from odrt.cli import platform_summary, structural_summary
    inputs = load_inputs(REPO)
    sim = REPO / "build/sim/metrics.json"
    if not sim.exists():
        pytest.skip("needs `make simulate`")
    st = inputs.structure
    opt = inputs.options[st.design]
    sz = structural_summary(inputs, json.loads(sim.read_text()))
    mp, _ = cad.build(st, opt, inputs.common, sz)
    back = -min(p.shape.val().BoundingBox().ymin for p in mp)
    z = platform_summary(inputs, sz, cad.envelope_mm(mp), 7.0, back)
    plat, parts, _, _ = packaging.build(st, opt, inputs.common, sz, inputs.platform, z,
                                        el.load_electronics(REPO / "data/electronics.csv"))
    assert packaging.interferences(plat, parts) == []
