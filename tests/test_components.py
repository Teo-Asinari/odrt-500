"""WP3 component data handling and option evaluation."""
import csv
import math

import numpy as np
import pytest

from conftest import REPO
from odrt.components import load_components, tension_capability_lbf
from odrt.config import ConfigError
from odrt.drivetrain import solve
from odrt.project import load_inputs
from odrt.scenarios import Trajectory
from odrt.units import n_to_lbf


def _rows(path):
    with path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        return reader.fieldnames, list(reader)


def _write(path, fields, rows):
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def test_blank_fields_stay_unknown():
    comps = load_components(REPO / "data/components.csv")
    d6374 = comps["odrive_d6374_150kv"]
    assert d6374.rotor_inertia_kg_m2 is None
    assert d6374.price_usd is None
    assert comps["myactuator_rmd_x10_p7_40"].km() is None


def test_km_conventions():
    comps = load_components(REPO / "data/components.csv")
    assert comps["odrive_d6374_150kv"].km() == pytest.approx(0.055 / math.sqrt(1.5 * 0.039))
    assert comps["cubemars_ro100_kv55"].km() == pytest.approx(0.2 / math.sqrt(0.143))


@pytest.mark.parametrize("field, value, message", [
    ("source_url", "http://example.com", "https URL"),
    ("accessed", "Nov 2026", "YYYY-MM-DD"),
    ("built_in_ratio", "", "built_in_ratio: required"),
    ("kt_nm_per_a", "fast", "not a number"),
    ("peak_torque_nm", "-3", ">"),
    ("kind", "gearbox", "not in"),
    ("resistance_basis", "line", "resistance_basis"),
    ("id", "odrive_d6374_150kv", "duplicate id"),
])
def test_invalid_component_rows_fail(tmp_path, field, value, message):
    fields, rows = _rows(REPO / "data/components.csv")
    rows[0][field] = value
    path = tmp_path / "c.csv"
    _write(path, fields, rows)
    with pytest.raises(ConfigError, match=message):
        load_components(path)


def test_wrong_columns_fail(tmp_path):
    fields, rows = _rows(REPO / "data/components.csv")
    path = tmp_path / "c.csv"
    _write(path, fields[:-1], [{k: r[k] for k in fields[:-1]} for r in rows])
    with pytest.raises(ConfigError, match="columns"):
        load_components(path)


def _hold(n=101, f=2000.0):
    full = np.ones(n)
    return Trajectory(t=np.arange(n) / 1000.0, x=0.5 * full, v=0 * full, a=0 * full, tension_n=f * full,
                      phase=np.zeros(n, dtype=np.int8))


def test_two_motors_halve_copper_loss_and_split_torque():
    inputs = load_inputs(REPO)
    one = inputs.options["cubemars_ro100_kv55@6:1"]
    two = inputs.options["2x cubemars_ro100_kv55@6:1"]
    s1 = solve(_hold(), one.architecture, inputs.common, 2.0)
    s2 = solve(_hold(), two.architecture, inputs.common, 2.0)
    np.testing.assert_allclose(s2.copper_w, s1.copper_w / 2)
    # Total torque is the same; each of the two motors carries half.
    np.testing.assert_allclose(s2.motor_torque_nm, s1.motor_torque_nm)


def test_tension_capability_hand_calc():
    inputs = load_inputs(REPO)
    opt = inputs.options["cubemars_ro100_kv55@6:1"]
    r = 0.025 + 0.002
    assert tension_capability_lbf(opt, 12, r) == pytest.approx(n_to_lbf(12 * 6 * 0.95 / r))
    two = inputs.options["2x cubemars_ro100_kv55@6:1"]
    assert tension_capability_lbf(two, 12, r) == pytest.approx(2 * n_to_lbf(12 * 6 * 0.95 / r))
    act = inputs.options["cubemars_ak10_9_v2_kv60@9:1 (built-in)"]
    assert tension_capability_lbf(act, 48, r) == pytest.approx(n_to_lbf(48 / r))
    assert tension_capability_lbf(opt, None, r) is None
