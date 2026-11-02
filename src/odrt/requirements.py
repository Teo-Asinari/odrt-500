"""Machine-readable requirements (R-xx) and assumptions (A-xxx) registers."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from odrt.config import ConfigError, check_keys, load_yaml, string, string_list

REQUIREMENT_STATUSES = (
    "hypothesis",
    "required-analysis",
    "stretch",
    "simulation-metric-tbd",
    "provisional",
    "independent-review-required",
    "exploratory",
    "target-tbd",
    "required",
)
ASSUMPTION_CONFIDENCE = ("low", "medium", "high")
ASSUMPTION_STATUS = ("open", "accepted", "retired")

_REQ_ID = re.compile(r"^R-\d{2}$")
_ASSUMPTION_ID = re.compile(r"^A-\d{3}$")


@dataclass(frozen=True)
class Requirement:
    id: str
    title: str
    target: str
    acceptance: str
    status: str


@dataclass(frozen=True)
class Assumption:
    id: str
    statement: str
    basis: str
    confidence: str
    status: str
    affects: tuple


def _unique(items, kind: str, path: Path) -> dict:
    out = {}
    for item in items:
        if item.id in out:
            raise ConfigError(f"{path}: duplicate {kind} id {item.id}")
        out[item.id] = item
    return out


def load_requirements(path: Path) -> dict:
    data = load_yaml(path)
    check_keys(data, str(path), ["requirements"])
    if not isinstance(data["requirements"], list) or not data["requirements"]:
        raise ConfigError(f"{path}: 'requirements' must be a non-empty list")
    items = []
    for i, raw in enumerate(data["requirements"]):
        where = f"{path}: requirements[{i}]"
        check_keys(raw, where, ["id", "title", "target", "acceptance", "status"])
        rid = string(raw["id"], f"{where}.id")
        if not _REQ_ID.match(rid):
            raise ConfigError(f"{where}.id: {rid!r} does not match R-NN")
        status = string(raw["status"], f"{where}.status")
        if status not in REQUIREMENT_STATUSES:
            raise ConfigError(f"{where}.status: {status!r} not in {REQUIREMENT_STATUSES}")
        items.append(Requirement(rid, string(raw["title"], f"{where}.title"),
                                 string(raw["target"], f"{where}.target"),
                                 string(raw["acceptance"], f"{where}.acceptance"), status))
    return _unique(items, "requirement", path)


def load_assumptions(path: Path, requirement_ids) -> dict:
    data = load_yaml(path)
    check_keys(data, str(path), ["assumptions"])
    if not isinstance(data["assumptions"], list) or not data["assumptions"]:
        raise ConfigError(f"{path}: 'assumptions' must be a non-empty list")
    items = []
    for i, raw in enumerate(data["assumptions"]):
        where = f"{path}: assumptions[{i}]"
        check_keys(raw, where, ["id", "statement", "basis", "confidence", "status", "affects"])
        aid = string(raw["id"], f"{where}.id")
        if not _ASSUMPTION_ID.match(aid):
            raise ConfigError(f"{where}.id: {aid!r} does not match A-NNN")
        confidence = string(raw["confidence"], f"{where}.confidence")
        if confidence not in ASSUMPTION_CONFIDENCE:
            raise ConfigError(f"{where}.confidence: {confidence!r} not in {ASSUMPTION_CONFIDENCE}")
        status = string(raw["status"], f"{where}.status")
        if status not in ASSUMPTION_STATUS:
            raise ConfigError(f"{where}.status: {status!r} not in {ASSUMPTION_STATUS}")
        affects = string_list(raw["affects"], f"{where}.affects")
        unknown = sorted(set(affects) - set(requirement_ids))
        if unknown:
            raise ConfigError(f"{where}.affects: unknown requirement ids {unknown}")
        items.append(Assumption(aid, string(raw["statement"], f"{where}.statement"),
                                string(raw["basis"], f"{where}.basis"), confidence, status, affects))
    return _unique(items, "assumption", path)
