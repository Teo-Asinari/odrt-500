"""Strict YAML loading and validation helpers.

Invalid inputs must fail loudly rather than produce reassuring output, so every
loader rejects unknown keys, missing keys and out-of-range values.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml


class ConfigError(ValueError):
    """Raised for any invalid configuration, requirement or scenario input."""


def load_yaml(path: Path) -> dict:
    path = Path(path)
    try:
        data = yaml.safe_load(path.read_text())
    except FileNotFoundError as exc:
        raise ConfigError(f"{path}: file not found") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"{path}: invalid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"{path}: top level must be a mapping")
    return data


def check_keys(data: Any, where: str, required: Iterable[str], optional: Iterable[str] = ()) -> None:
    if not isinstance(data, Mapping):
        raise ConfigError(f"{where}: expected a mapping, got {type(data).__name__}")
    required, optional = set(required), set(optional)
    missing = required - set(data)
    unknown = set(data) - required - optional
    if missing:
        raise ConfigError(f"{where}: missing keys {sorted(missing)}")
    if unknown:
        raise ConfigError(f"{where}: unknown keys {sorted(unknown)}")


def number(value: Any, where: str, *, minimum: float = None, maximum: float = None,
           exclusive_minimum: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"{where}: expected a number, got {value!r}")
    value = float(value)
    if value != value or value in (float("inf"), float("-inf")):
        raise ConfigError(f"{where}: must be finite, got {value}")
    if minimum is not None:
        if exclusive_minimum and value <= minimum:
            raise ConfigError(f"{where}: must be > {minimum}, got {value}")
        if not exclusive_minimum and value < minimum:
            raise ConfigError(f"{where}: must be >= {minimum}, got {value}")
    if maximum is not None and value > maximum:
        raise ConfigError(f"{where}: must be <= {maximum}, got {value}")
    return value


def integer(value: Any, where: str, *, minimum: int = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"{where}: expected an integer, got {value!r}")
    if minimum is not None and value < minimum:
        raise ConfigError(f"{where}: must be >= {minimum}, got {value}")
    return value


def string(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{where}: expected a non-empty string, got {value!r}")
    return value.strip()


def string_list(value: Any, where: str) -> tuple:
    if not isinstance(value, list):
        raise ConfigError(f"{where}: expected a list, got {value!r}")
    return tuple(string(v, f"{where}[{i}]") for i, v in enumerate(value))

