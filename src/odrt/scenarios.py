"""WP1: named reference use cases and duty cycles as abstract 1-D cable trajectories.

Coordinates: x is cable paid out from the drum (m); v > 0 is extension.
Tension is the setpoint the device is asked to hold (N), always >= 0.
These are test inputs for later models, not exercise prescriptions (A-001).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from odrt.config import (ConfigError, check_keys, integer, load_yaml, number, string,
                         string_list)
from odrt.units import lbf_to_n

SCENARIO_KINDS = ("reference", "limit")
MAX_SAMPLES = 20_000_000

# Phase codes stored with each trajectory sample.
PHASE_REST, PHASE_EXTEND, PHASE_TOP_HOLD, PHASE_RETRACT, PHASE_BOTTOM_HOLD = range(5)
PHASE_NAMES = ("rest", "extend", "top_hold", "retract", "bottom_hold")


@dataclass(frozen=True)
class Envelope:
    peak_tension_lbf: float
    max_usable_stroke_m: float


@dataclass(frozen=True)
class Defaults:
    sample_rate_hz: float
    tension_ramp_s: float
    rest_tension_lbf: float
    tut_threshold_lbf: float


@dataclass(frozen=True)
class Scenario:
    name: str
    description: str
    kind: str
    requirements: tuple
    assumptions: tuple
    start_offset_m: float
    stroke_m: float
    extend_s: float
    top_hold_s: float
    retract_s: float
    bottom_hold_s: float
    reps: int
    sets: int
    rest_s: float
    extension_tension_lbf: float
    retraction_tension_lbf: float

    def cycle_s(self) -> float:
        return self.extend_s + self.top_hold_s + self.retract_s + self.bottom_hold_s


@dataclass(frozen=True)
class Trajectory:
    t: np.ndarray        # s
    x: np.ndarray        # m
    v: np.ndarray        # m/s
    a: np.ndarray        # m/s^2
    tension_n: np.ndarray
    phase: np.ndarray    # int8 phase codes

    @property
    def dt(self) -> float:
        return float(self.t[1] - self.t[0])

    @property
    def power_w(self) -> np.ndarray:
        """Power into the device; > 0 absorbed, < 0 returned (see units.cable_power_w)."""
        return self.tension_n * self.v


def load_envelope(path: Path) -> Envelope:
    data = load_yaml(path)
    check_keys(data, str(path), ["envelope"])
    env = data["envelope"]
    where = f"{path}: envelope"
    check_keys(env, where, ["peak_tension_lbf", "max_usable_stroke_m"])
    return Envelope(
        number(env["peak_tension_lbf"], f"{where}.peak_tension_lbf", minimum=0, exclusive_minimum=True),
        number(env["max_usable_stroke_m"], f"{where}.max_usable_stroke_m", minimum=0, exclusive_minimum=True),
    )


_SCENARIO_KEYS = ["description", "kind", "requirements", "assumptions", "start_offset_m", "stroke_m",
                  "extend_s", "top_hold_s", "retract_s", "bottom_hold_s", "reps", "sets", "rest_s",
                  "extension_tension_lbf", "retraction_tension_lbf"]


def load_scenarios(path: Path, envelope: Envelope, requirement_ids=(), assumption_ids=()):
    """Load and validate scenarios. Returns (Defaults, {name: Scenario})."""
    data = load_yaml(path)
    check_keys(data, str(path), ["defaults", "scenarios"])
    d = data["defaults"]
    where = f"{path}: defaults"
    check_keys(d, where, ["sample_rate_hz", "tension_ramp_s", "rest_tension_lbf", "tut_threshold_lbf"])
    peak = envelope.peak_tension_lbf
    defaults = Defaults(
        number(d["sample_rate_hz"], f"{where}.sample_rate_hz", minimum=10),
        number(d["tension_ramp_s"], f"{where}.tension_ramp_s", minimum=0),
        number(d["rest_tension_lbf"], f"{where}.rest_tension_lbf", minimum=0, maximum=peak),
        number(d["tut_threshold_lbf"], f"{where}.tut_threshold_lbf", minimum=0, maximum=peak),
    )
    if not isinstance(data["scenarios"], dict) or not data["scenarios"]:
        raise ConfigError(f"{path}: 'scenarios' must be a non-empty mapping")
    scenarios = {}
    for name, raw in data["scenarios"].items():
        scenarios[name] = _parse_scenario(str(name), raw, f"{path}: scenarios.{name}", envelope,
                                          set(requirement_ids), set(assumption_ids))
        _check_size(scenarios[name], defaults, f"{path}: scenarios.{name}")
        _segments(scenarios[name], defaults, f"{path}: scenarios.{name}")  # validates tension ramps
    return defaults, scenarios


def _parse_scenario(name, raw, where, envelope, requirement_ids, assumption_ids) -> Scenario:
    check_keys(raw, where, _SCENARIO_KEYS)
    kind = string(raw["kind"], f"{where}.kind")
    if kind not in SCENARIO_KINDS:
        raise ConfigError(f"{where}.kind: {kind!r} not in {SCENARIO_KINDS}")
    reqs = string_list(raw["requirements"], f"{where}.requirements")
    assumptions = string_list(raw["assumptions"], f"{where}.assumptions")
    if requirement_ids and set(reqs) - requirement_ids:
        raise ConfigError(f"{where}.requirements: unknown ids {sorted(set(reqs) - requirement_ids)}")
    if assumption_ids and set(assumptions) - assumption_ids:
        raise ConfigError(f"{where}.assumptions: unknown ids {sorted(set(assumptions) - assumption_ids)}")

    def dur(key, positive):
        return number(raw[key], f"{where}.{key}", minimum=0, exclusive_minimum=positive)

    def tension(key):
        return number(raw[key], f"{where}.{key}", minimum=0, maximum=envelope.peak_tension_lbf)

    start = number(raw["start_offset_m"], f"{where}.start_offset_m", minimum=0)
    stroke = number(raw["stroke_m"], f"{where}.stroke_m", minimum=0, exclusive_minimum=True)
    if start + stroke > envelope.max_usable_stroke_m + 1e-12:
        raise ConfigError(f"{where}: start_offset_m + stroke_m = {start + stroke} m exceeds "
                          f"max_usable_stroke_m {envelope.max_usable_stroke_m} m")
    return Scenario(
        name=name, description=string(raw["description"], f"{where}.description"), kind=kind,
        requirements=reqs, assumptions=assumptions, start_offset_m=start, stroke_m=stroke,
        extend_s=dur("extend_s", True), top_hold_s=dur("top_hold_s", False),
        retract_s=dur("retract_s", True), bottom_hold_s=dur("bottom_hold_s", False),
        reps=integer(raw["reps"], f"{where}.reps", minimum=1),
        sets=integer(raw["sets"], f"{where}.sets", minimum=1),
        rest_s=dur("rest_s", False),
        extension_tension_lbf=tension("extension_tension_lbf"),
        retraction_tension_lbf=tension("retraction_tension_lbf"),
    )


def _check_size(scenario: Scenario, defaults: Defaults, where: str) -> None:
    n = scenario_duration_s(scenario, defaults) * defaults.sample_rate_hz
    if n > MAX_SAMPLES:
        raise ConfigError(f"{where}: {n:.0f} samples exceeds limit {MAX_SAMPLES}")


def settle_s(defaults: Defaults) -> float:
    """Rest padding at the start and end of every record."""
    return max(1.0, 2.0 * defaults.tension_ramp_s)


def _segments(s: Scenario, defaults: Defaults, where: str = None):
    """(phase, duration_s, x_start, x_end, tension_lbf) tuples; zero-length segments dropped.

    Tension changes only while the cable is stationary: each stationary segment
    ramps linearly to its own setpoint over tension_ramp_s. A top hold ramps to
    the retraction tension, a bottom hold (and the pre-load hold that opens each
    set) to the extension tension, a rest to the rest tension. Moving segments
    hold their setpoint constant. If a required ramp does not fit, this raises.
    """
    where = where or s.name
    lo, hi = s.start_offset_m, s.start_offset_m + s.stroke_m
    ramp = defaults.tension_ramp_s
    settle = settle_s(defaults)
    segs = [(PHASE_REST, settle, lo, lo, defaults.rest_tension_lbf)]
    for set_index in range(s.sets):
        segs.append((PHASE_BOTTOM_HOLD, ramp, lo, lo, s.extension_tension_lbf))  # pre-load
        for _ in range(s.reps):
            segs += [
                (PHASE_EXTEND, s.extend_s, lo, hi, s.extension_tension_lbf),
                (PHASE_TOP_HOLD, s.top_hold_s, hi, hi, s.retraction_tension_lbf),
                (PHASE_RETRACT, s.retract_s, hi, lo, s.retraction_tension_lbf),
                (PHASE_BOTTOM_HOLD, s.bottom_hold_s, lo, lo, s.extension_tension_lbf),
            ]
        if set_index < s.sets - 1:
            segs.append((PHASE_REST, s.rest_s, lo, lo, defaults.rest_tension_lbf))
    segs.append((PHASE_REST, settle, lo, lo, defaults.rest_tension_lbf))

    out, current = [], defaults.rest_tension_lbf
    for phase, duration, x0, x1, target in segs:
        # Every moving segment follows a stationary one with the same setpoint,
        # so only stationary segments can need a ramp.
        if target != current and duration + 1e-12 < ramp:
            raise ConfigError(f"{where}: {PHASE_NAMES[phase]} lasts {duration:g} s but the tension "
                              f"change from {current:g} to {target:g} lbf needs tension_ramp_s = "
                              f"{ramp:g} s")
        if duration > 0:
            out.append((phase, duration, x0, x1, target))
            current = target
    return out


def scenario_duration_s(s: Scenario, defaults: Defaults) -> float:
    return (2 * settle_s(defaults) + s.sets * (defaults.tension_ramp_s + s.reps * s.cycle_s())
            + (s.sets - 1) * s.rest_s)


def min_jerk(tau):
    """Normalised minimum-jerk position, velocity and acceleration for tau in [0, 1]."""
    tau = np.clip(tau, 0.0, 1.0)
    pos = tau**3 * (10 - 15 * tau + 6 * tau**2)
    vel = 30 * tau**2 * (1 - tau) ** 2
    acc = 60 * tau * (1 - tau) * (1 - 2 * tau)
    return pos, vel, acc


def generate(s: Scenario, defaults: Defaults) -> Trajectory:
    segs = _segments(s, defaults)
    phase_code = np.array([g[0] for g in segs], dtype=np.int8)
    durations = np.array([g[1] for g in segs])
    x0 = np.array([g[2] for g in segs])
    x1 = np.array([g[3] for g in segs])
    f_to = lbf_to_n(np.array([g[4] for g in segs]))
    f_from = np.concatenate(([lbf_to_n(defaults.rest_tension_lbf)], f_to[:-1]))
    starts = np.concatenate(([0.0], np.cumsum(durations)[:-1]))
    total = float(np.sum(durations))

    fs = defaults.sample_rate_hz
    n = int(round(total * fs)) + 1
    t = np.arange(n) / fs
    idx = np.clip(np.searchsorted(starts, t, side="right") - 1, 0, len(segs) - 1)
    dur = durations[idx]
    elapsed = t - starts[idx]
    pos, vel, acc = min_jerk(elapsed / dur)
    span = x1[idx] - x0[idx]
    x = x0[idx] + span * pos
    v = span / dur * vel
    a = span / dur**2 * acc

    ramp = defaults.tension_ramp_s
    frac = np.clip(elapsed / ramp, 0.0, 1.0) if ramp > 0 else np.ones_like(t)
    tension = f_from[idx] + (f_to[idx] - f_from[idx]) * frac
    return Trajectory(t=t, x=x, v=v, a=a, tension_n=tension, phase=phase_code[idx])
