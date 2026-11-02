"""Locate and load every project input, with cross-reference checks."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from odrt.requirements import load_assumptions, load_requirements
from odrt.scenarios import Defaults, Envelope, load_envelope, load_scenarios

INPUT_FILES = ("requirements/requirements.yaml", "requirements/assumptions.yaml",
               "configs/baseline.yaml", "configs/scenarios.yaml")


@dataclass(frozen=True)
class Inputs:
    root: Path
    requirements: dict
    assumptions: dict
    envelope: Envelope
    defaults: Defaults
    scenarios: dict
    input_hash: str


def load_inputs(root: Path = Path(".")) -> Inputs:
    root = Path(root)
    req_path, asm_path, base_path, scen_path = (root / p for p in INPUT_FILES)
    requirements = load_requirements(req_path)
    assumptions = load_assumptions(asm_path, requirements)
    envelope = load_envelope(base_path)
    defaults, scenarios = load_scenarios(scen_path, envelope, requirements, assumptions)
    return Inputs(root, requirements, assumptions, envelope, defaults, scenarios, input_hash(root))


def input_hash(root: Path) -> str:
    """SHA-256 over repo-relative input paths and contents, independent of checkout location."""
    digest = hashlib.sha256()
    for rel in INPUT_FILES:
        digest.update(rel.encode() + b"\0" + (Path(root) / rel).read_bytes() + b"\0")
    return digest.hexdigest()
