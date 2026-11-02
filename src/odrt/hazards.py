"""WP5 hazard log loader (requirements/hazards.yaml)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from odrt.config import ConfigError, check_keys, load_yaml, string, string_list

SEVERITIES = ("S1", "S2", "S3", "S4")
CHANNELS = ("mechanical", "independent-hardware", "firmware", "not-yet-defined")
DYNAMIC_METRICS = ("peak_tension_lbf", "peak_tension_after_fault_lbf", "tracking_rms_error_n",
                   "tracking_rms_error_pct", "peak_retract_speed_m_s", "handle_end_stop_speed_m_s", "peak_bus_v",
                   "time_to_overvoltage_ms", "torque_saturated_fraction", "fell_back_to_feedforward",
                   "release_detected", "min_bus_v", "tension_below_10pct_ms", "peak_hand_deviation_after_fault_m")


@dataclass(frozen=True)
class Hazard:
    id: str
    title: str
    cause: str
    effect: str
    severity: str
    evidence: tuple   # ((case, metric), ...)
    mitigations: tuple
    channel: str
    validation_gap: str
    requirements: tuple


def load_hazards(path: Path, requirement_ids, case_names) -> dict:
    data = load_yaml(path)
    check_keys(data, str(path), ["hazards"])
    if not isinstance(data["hazards"], list) or not data["hazards"]:
        raise ConfigError(f"{path}: 'hazards' must be a non-empty list")
    out = {}
    for i, raw in enumerate(data["hazards"]):
        w = f"{path}: hazards[{i}]"
        check_keys(raw, w, ["id", "title", "cause", "effect", "severity", "evidence", "mitigations", "channel",
                            "validation_gap", "requirements"])
        hid = string(raw["id"], f"{w}.id")
        if not re.match(r"^H-\d{2}$", hid):
            raise ConfigError(f"{w}.id: {hid!r} does not match H-NN")
        if hid in out:
            raise ConfigError(f"{w}.id: duplicate {hid}")
        if raw["severity"] not in SEVERITIES:
            raise ConfigError(f"{w}.severity: {raw['severity']!r} not in {SEVERITIES}")
        if raw["channel"] not in CHANNELS:
            raise ConfigError(f"{w}.channel: {raw['channel']!r} not in {CHANNELS}")
        if not isinstance(raw["evidence"], list):
            raise ConfigError(f"{w}.evidence: expected a list")
        evidence = []
        for j, ev in enumerate(raw["evidence"]):
            check_keys(ev, f"{w}.evidence[{j}]", ["case", "metric"])
            if ev["case"] not in case_names:
                raise ConfigError(f"{w}.evidence[{j}].case: unknown dynamics case {ev['case']!r}")
            if ev["metric"] not in DYNAMIC_METRICS:
                raise ConfigError(f"{w}.evidence[{j}].metric: unknown metric {ev['metric']!r}")
            evidence.append((ev["case"], ev["metric"]))
        reqs = string_list(raw["requirements"], f"{w}.requirements")
        unknown = sorted(set(reqs) - set(requirement_ids))
        if unknown:
            raise ConfigError(f"{w}.requirements: unknown ids {unknown}")
        out[hid] = Hazard(hid, string(raw["title"], f"{w}.title"), string(raw["cause"], f"{w}.cause"),
                          string(raw["effect"], f"{w}.effect"), raw["severity"], tuple(evidence),
                          string_list(raw["mitigations"], f"{w}.mitigations"), raw["channel"],
                          string(raw["validation_gap"], f"{w}.validation_gap"), reqs)
    return out
