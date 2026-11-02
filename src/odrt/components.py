"""WP3: real, cited component candidates evaluated through the WP2 drivetrain model.

Blank CSV fields mean "not stated by the cited source" and stay None; the model
never fills them in. Results that depend on a missing value are reported as
unavailable rather than estimated.
"""
from __future__ import annotations

import csv
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from odrt.config import ConfigError, check_keys, integer, load_yaml, number, string
from odrt.drivetrain import Architecture

KINDS = ("motor", "actuator")
RESISTANCE_BASES = ("phase_neutral", "phase_phase", "phase_rms")
_REQUIRED_TEXT = ("id", "kind", "vendor", "model", "source_url", "accessed")
_NUMERIC = ("built_in_ratio", "kt_nm_per_a", "resistance_ohm", "continuous_torque_nm", "peak_torque_nm",
            "max_speed_rpm", "rotor_inertia_kg_m2", "mass_kg", "price_usd")
_TEXT = ("kt_basis", "resistance_basis", "continuous_torque_basis", "peak_torque_basis", "max_speed_basis",
         "notes")
COLUMNS = ("id", "kind", "vendor", "model", "built_in_ratio", "kt_nm_per_a", "kt_basis", "resistance_ohm",
           "resistance_basis", "continuous_torque_nm", "continuous_torque_basis", "peak_torque_nm",
           "peak_torque_basis", "max_speed_rpm", "max_speed_basis", "rotor_inertia_kg_m2", "mass_kg",
           "price_usd", "source_url", "accessed", "notes")


@dataclass(frozen=True)
class Component:
    id: str
    kind: str
    vendor: str
    model: str
    built_in_ratio: float
    kt_nm_per_a: Optional[float]
    kt_basis: str
    resistance_ohm: Optional[float]
    resistance_basis: str
    continuous_torque_nm: Optional[float]
    continuous_torque_basis: str
    peak_torque_nm: Optional[float]
    peak_torque_basis: str
    max_speed_rpm: Optional[float]
    max_speed_basis: str
    rotor_inertia_kg_m2: Optional[float]
    mass_kg: Optional[float]
    price_usd: Optional[float]
    source_url: str
    accessed: str
    notes: str

    def km(self) -> Optional[float]:
        """Motor constant N*m/sqrt(W) under the stated convention (A-014), or None."""
        if self.kind != "motor" or self.kt_nm_per_a is None or self.resistance_ohm is None:
            return None
        # amplitude-convention Kt with phase-neutral R: P = 1.5 I^2 R; rms Kt with per-phase R: P = 3 I^2 R
        factor = {"phase_neutral": 1.5, "phase_phase": 1.0, "phase_rms": 3.0}[self.resistance_basis]
        return self.kt_nm_per_a / math.sqrt(factor * self.resistance_ohm)


@dataclass(frozen=True)
class Study:
    drum_from_architecture: str
    external_ratios: tuple
    motor_counts: tuple
    external_gear_efficiency: float
    actuator_gear_efficiency: float


@dataclass(frozen=True)
class Option:
    """A component plus the reduction it is evaluated with."""
    name: str
    component: Component
    count: int            # identical motors sharing the drum; torques below are per motor
    ratio: float          # total ratio between rated shaft and drum
    external_ratio: float
    efficiency: float
    architecture: Architecture  # what the drivetrain model solves; torque out is at the rated shaft


def load_components(path: Path) -> dict:
    path = Path(path)
    try:
        with path.open(newline="") as fh:
            reader = csv.DictReader(fh)
            if tuple(reader.fieldnames or ()) != COLUMNS:
                raise ConfigError(f"{path}: columns must be exactly {list(COLUMNS)}")
            rows = list(reader)
    except FileNotFoundError:
        raise ConfigError(f"{path}: file not found") from None
    out = {}
    for i, row in enumerate(rows, start=2):
        where = f"{path}: line {i}"
        for key in _REQUIRED_TEXT:
            string(row[key], f"{where}.{key}")
        if row["kind"] not in KINDS:
            raise ConfigError(f"{where}.kind: {row['kind']!r} not in {KINDS}")
        if not row["source_url"].startswith("https://"):
            raise ConfigError(f"{where}.source_url: must be an https URL")
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", row["accessed"]):
            raise ConfigError(f"{where}.accessed: must be YYYY-MM-DD")
        values = {}
        for key in _NUMERIC:
            text = row[key].strip()
            if not text:
                values[key] = None
                continue
            try:
                parsed = float(text)
            except ValueError:
                raise ConfigError(f"{where}.{key}: not a number: {text!r}") from None
            values[key] = number(parsed, f"{where}.{key}", minimum=0, exclusive_minimum=True)
        if values["built_in_ratio"] is None:
            raise ConfigError(f"{where}.built_in_ratio: required (1 for a bare motor)")
        if row["resistance_ohm"].strip() and row["resistance_basis"] not in RESISTANCE_BASES:
            raise ConfigError(f"{where}.resistance_basis: must be one of {RESISTANCE_BASES}")
        if row["id"] in out:
            raise ConfigError(f"{where}: duplicate id {row['id']}")
        out[row["id"]] = Component(**{k: row[k].strip() for k in _REQUIRED_TEXT + _TEXT}, **values)
    if not out:
        raise ConfigError(f"{path}: no components")
    return out


def load_study(path: Path, architectures: dict) -> Study:
    data = load_yaml(path)
    where = str(path)
    check_keys(data, where, ["drum_from_architecture", "external_ratios", "motor_counts", "external_gear_efficiency",
                             "actuator_gear_efficiency"])
    drum = string(data["drum_from_architecture"], f"{where}.drum_from_architecture")
    if drum not in architectures:
        raise ConfigError(f"{where}.drum_from_architecture: unknown architecture {drum!r}")
    ratios = data["external_ratios"]
    if not isinstance(ratios, list) or not ratios:
        raise ConfigError(f"{where}.external_ratios: must be a non-empty list")
    counts = data["motor_counts"]
    if not isinstance(counts, list) or not counts:
        raise ConfigError(f"{where}.motor_counts: must be a non-empty list")
    return Study(
        drum_from_architecture=drum,
        motor_counts=tuple(integer(n, f"{where}.motor_counts", minimum=1) for n in counts),
        external_ratios=tuple(number(r, f"{where}.external_ratios", minimum=0, exclusive_minimum=True)
                              for r in ratios),
        external_gear_efficiency=number(data["external_gear_efficiency"], f"{where}.external_gear_efficiency",
                                        minimum=0, exclusive_minimum=True, maximum=1),
        actuator_gear_efficiency=number(data["actuator_gear_efficiency"], f"{where}.actuator_gear_efficiency",
                                        minimum=0, exclusive_minimum=True, maximum=1),
    )


def options(components: dict, study: Study, architectures: dict) -> dict:
    """Expand components into evaluated options.

    Motors: torque is evaluated at the motor shaft through an external reduction.
    Actuators: ratings are at the actuator output, so the actuator output drives
    the drum directly and its internal gearbox only affects reflected inertia,
    which is unknown (None) for both listed actuators.
    """
    drum = architectures[study.drum_from_architecture]
    out = {}
    for comp in components.values():
        inertia = comp.rotor_inertia_kg_m2 or 0.0
        km = comp.km() or float("nan")
        if comp.kind == "motor":
            for n in study.motor_counts:
                for g in study.external_ratios:
                    name = f"{n}x {comp.id}@{g:g}:1" if n > 1 else f"{comp.id}@{g:g}:1"
                    # n motors sharing torque equally behave like one motor with n times the
                    # inertia and sqrt(n) times Km; per-motor torque is the total divided by n.
                    arch = Architecture(name=name, description=comp.model, gear_ratio=g,
                                        gear_efficiency=study.external_gear_efficiency,
                                        drum_core_radius_m=drum.drum_core_radius_m,
                                        turns_per_layer=drum.turns_per_layer, max_layers=drum.max_layers,
                                        drum_inertia_kg_m2=drum.drum_inertia_kg_m2,
                                        motor_rotor_inertia_kg_m2=n * inertia,
                                        motor_km_nm_per_sqrt_w=km * math.sqrt(n))
                    out[name] = Option(name, comp, n, g * comp.built_in_ratio, g,
                                       study.external_gear_efficiency, arch)
        else:
            name = f"{comp.id}@{comp.built_in_ratio:g}:1 (built-in)"
            arch = Architecture(name=name, description=comp.model, gear_ratio=1.0, gear_efficiency=1.0,
                                drum_core_radius_m=drum.drum_core_radius_m,
                                turns_per_layer=drum.turns_per_layer, max_layers=drum.max_layers,
                                drum_inertia_kg_m2=drum.drum_inertia_kg_m2, motor_rotor_inertia_kg_m2=0.0,
                                motor_km_nm_per_sqrt_w=km)
            out[name] = Option(name, comp, 1, comp.built_in_ratio, 1.0, study.actuator_gear_efficiency, arch)
    return out


def tension_capability_lbf(option: Option, torque_nm: Optional[float], radius_m: float) -> Optional[float]:
    """Static cable tension a rated shaft torque can hold at the given drum radius."""
    from odrt.units import n_to_lbf
    if torque_nm is None:
        return None
    if option.component.kind == "actuator":
        return float(n_to_lbf(torque_nm / radius_m))
    # Holding: motor torque = F r / (G eta) (conservative direction), so F = tau G eta / r.
    return float(n_to_lbf(option.count * torque_nm * option.external_ratio * option.efficiency / radius_m))


def none_if_nan(value):
    return None if value is None or (isinstance(value, float) and math.isnan(value)) else value
