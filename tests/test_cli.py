import json

from conftest import REPO, edit_yaml
from odrt.cli import main


def test_check_passes_on_repo():
    assert main(["--root", str(REPO), "check"]) == 0


def test_simulate_and_report_end_to_end(repo_copy, tmp_path):
    sim, out = tmp_path / "sim", tmp_path / "reports"
    root = str(repo_copy)
    assert main(["--root", root, "simulate", "--out", str(sim), "--only", "curl_reference"]) == 0
    payload = json.loads((sim / "metrics.json").read_text())
    assert set(payload["scenarios"]) == {"curl_reference"}
    # report refuses partial results
    assert main(["--root", root, "report", "--sim", str(sim), "--out", str(out)]) == 2
    assert main(["--root", root, "simulate", "--out", str(sim)]) == 0
    assert main(["--root", root, "report", "--sim", str(sim), "--out", str(out)]) == 0
    assert (out / "figures/curl_reference.png").stat().st_size > 0
    assert "curl_reference" in (out / "duty_cycles.md").read_text()
    assert "R-13" in (out / "traceability.md").read_text()


def test_report_refuses_stale_results(repo_copy, tmp_path):
    sim = tmp_path / "sim"
    root = str(repo_copy)
    assert main(["--root", root, "simulate", "--out", str(sim), "--only", "low_force_limit"]) == 0
    edit_yaml(repo_copy / "configs/scenarios.yaml",
              lambda d: d["defaults"].__setitem__("tension_ramp_s", 0.3))
    assert main(["--root", root, "report", "--sim", str(sim), "--out", str(tmp_path / "r")]) == 2


def test_invalid_input_exits_nonzero(repo_copy, capsys):
    edit_yaml(repo_copy / "configs/baseline.yaml",
              lambda d: d["envelope"].__setitem__("max_usable_stroke_m", -1))
    assert main(["--root", str(repo_copy), "check"]) == 2
    assert "error:" in capsys.readouterr().err
