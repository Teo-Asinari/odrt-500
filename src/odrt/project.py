"""Locate and load every project input, with cross-reference checks."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from odrt.components import Study, load_components, load_study, options
from odrt.costing import load_bom
from odrt.platform import load_platform
from odrt.drivetrain import Common, load_architectures
from odrt.thermal import ThermalParams, load_thermal
from odrt.requirements import load_assumptions, load_requirements
from odrt.scenarios import Defaults, Envelope, load_envelope, load_scenarios

INPUT_FILES = ("requirements/requirements.yaml", "requirements/assumptions.yaml",
               "configs/baseline.yaml", "configs/scenarios.yaml", "configs/architectures.yaml",
               "data/components.csv", "configs/component_study.yaml",
               "configs/thermal.yaml", "configs/dynamics.yaml", "configs/structure.yaml",
               "requirements/hazards.yaml", "data/bom.csv", "configs/platform.yaml",
               "configs/custom_motor.yaml", "data/motor_family.csv", "configs/electronics.yaml",
               "data/electronics.csv")


@dataclass(frozen=True)
class Inputs:
    root: Path
    requirements: dict
    assumptions: dict
    envelope: Envelope
    defaults: Defaults
    scenarios: dict
    common: Common
    architectures: dict
    components: dict
    study: Study
    options: dict
    thermal: ThermalParams
    dynamics: object
    structure: object
    hazards: dict
    bom: list
    platform: object
    input_hash: str


def load_inputs(root: Path = Path(".")) -> Inputs:
    root = Path(root)
    (req_path, asm_path, base_path, scen_path, arch_path, comp_path, study_path,
     thermal_path, dyn_path, struct_path, haz_path, bom_path, plat_path, _motor_cfg, _family, _el_cfg, _el) = (
        root / p for p in INPUT_FILES)
    requirements = load_requirements(req_path)
    assumptions = load_assumptions(asm_path, requirements)
    envelope = load_envelope(base_path)
    defaults, scenarios = load_scenarios(scen_path, envelope, requirements, assumptions)
    common, architectures = load_architectures(arch_path, envelope.max_usable_stroke_m)
    components = load_components(comp_path)
    study = load_study(study_path, architectures)
    opts = options(components, study, architectures)
    from odrt.dynamics import load_dynamics
    dynamics = load_dynamics(dyn_path, opts, scenarios)
    from odrt.structural import load_structure
    structure = load_structure(struct_path, opts)
    from odrt.hazards import load_hazards
    hazards = load_hazards(haz_path, requirements, {c.name for c in dynamics.cases})
    return Inputs(root, requirements, assumptions, envelope, defaults, scenarios, common, architectures,
                  components, study, opts, load_thermal(thermal_path), dynamics, structure, hazards,
                  load_bom(bom_path), load_platform(plat_path), input_hash(root))


def thermal_models(inputs: Inputs) -> dict:
    """{option name: (MotorThermal or None, reason or None)}; raises if the step is too coarse."""
    from odrt.thermal import motor_thermal
    return {name: motor_thermal(opt.component, inputs.thermal) for name, opt in inputs.options.items()}


def input_hash(root: Path) -> str:
    """SHA-256 over repo-relative input paths and contents, independent of checkout location."""
    digest = hashlib.sha256()
    for rel in INPUT_FILES:
        digest.update(rel.encode() + b"\0" + (Path(root) / rel).read_bytes() + b"\0")
    return digest.hexdigest()
