"""The shipped inputs load, and deliberately invalid inputs fail loudly."""
import pytest

from conftest import REPO, edit_yaml
from odrt.config import ConfigError
from odrt.project import load_inputs


def test_shipped_inputs_load():
    inputs = load_inputs(REPO)
    assert list(inputs.requirements) == [f"R-{i:02d}" for i in range(1, 14)]
    assert inputs.envelope.peak_tension_lbf == 500
    assert {"reference", "limit"} == {s.kind for s in inputs.scenarios.values()}
    for s in inputs.scenarios.values():
        assert s.requirements, s.name
        assert s.assumptions, s.name


def test_input_hash_is_location_independent(repo_copy):
    assert load_inputs(repo_copy).input_hash == load_inputs(REPO).input_hash


def _scenario(data):
    return data["scenarios"]["curl_reference"]


@pytest.mark.parametrize("mutate, message", [
    (lambda d: _scenario(d).__setitem__("extension_tension_lbf", 501), "<= 500"),
    (lambda d: _scenario(d).__setitem__("retraction_tension_lbf", -1), ">= 0"),
    (lambda d: _scenario(d).__setitem__("extend_s", 0), "> 0"),
    (lambda d: _scenario(d).__setitem__("top_hold_s", -0.1), ">= 0"),
    (lambda d: _scenario(d).__setitem__("stroke_m", 1.9), "exceeds max_usable_stroke_m"),
    (lambda d: _scenario(d).__setitem__("reps", 2.5), "expected an integer"),
    (lambda d: _scenario(d).__setitem__("sets", 0), ">= 1"),
    (lambda d: _scenario(d).__setitem__("kind", "demo"), "not in"),
    (lambda d: _scenario(d).__setitem__("strok_m", 0.5), "unknown keys"),
    (lambda d: _scenario(d).pop("rest_s"), "missing keys"),
    (lambda d: _scenario(d).__setitem__("requirements", ["R-99"]), "unknown ids"),
    (lambda d: _scenario(d).__setitem__("assumptions", ["A-999"]), "unknown ids"),
    (lambda d: _scenario(d).__setitem__("stroke_m", "0.5"), "expected a number"),
    (lambda d: _scenario(d).__setitem__("stroke_m", float("nan")), "finite"),
    (lambda d: _scenario(d).__setitem__("reps", 10_000_000), "samples exceeds limit"),
])
def test_invalid_scenarios_fail(repo_copy, mutate, message):
    edit_yaml(repo_copy / "configs/scenarios.yaml", mutate)
    with pytest.raises(ConfigError, match=message):
        load_inputs(repo_copy)


def test_duplicate_requirement_id_fails(repo_copy):
    edit_yaml(repo_copy / "requirements/requirements.yaml",
              lambda d: d["requirements"].append(dict(d["requirements"][0])))
    with pytest.raises(ConfigError, match="duplicate requirement id R-01"):
        load_inputs(repo_copy)


def test_bad_requirement_status_fails(repo_copy):
    edit_yaml(repo_copy / "requirements/requirements.yaml",
              lambda d: d["requirements"][0].__setitem__("status", "proven"))
    with pytest.raises(ConfigError, match="status"):
        load_inputs(repo_copy)


def test_assumption_citing_unknown_requirement_fails(repo_copy):
    edit_yaml(repo_copy / "requirements/assumptions.yaml",
              lambda d: d["assumptions"][0].__setitem__("affects", ["R-42"]))
    with pytest.raises(ConfigError, match="unknown requirement ids"):
        load_inputs(repo_copy)


def test_envelope_must_be_positive(repo_copy):
    edit_yaml(repo_copy / "configs/baseline.yaml",
              lambda d: d["envelope"].__setitem__("peak_tension_lbf", 0))
    with pytest.raises(ConfigError, match="> 0"):
        load_inputs(repo_copy)


@pytest.mark.parametrize("mutate, message", [
    (lambda d: d["hazards"][0].__setitem__("severity", "S5"), "severity"),
    (lambda d: d["hazards"][0].__setitem__("channel", "hope"), "channel"),
    (lambda d: d["hazards"][0]["evidence"].append({"case": "nope", "metric": "peak_bus_v"}), "unknown dynamics case"),
    (lambda d: d["hazards"][0]["evidence"].append({"case": "release_at_500lbf", "metric": "vibes"}), "unknown metric"),
    (lambda d: d["hazards"][1].__setitem__("id", "H-01"), "duplicate"),
    (lambda d: d["hazards"][0].__setitem__("requirements", ["R-77"]), "unknown ids"),
])
def test_invalid_hazards_fail(repo_copy, mutate, message):
    edit_yaml(repo_copy / "requirements/hazards.yaml", mutate)
    with pytest.raises(ConfigError, match=message):
        load_inputs(repo_copy)
