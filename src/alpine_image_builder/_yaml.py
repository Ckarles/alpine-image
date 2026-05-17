"""Base exception and shared YAML/Pydantic validation helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ValidationError


class ConfigError(Exception):
    """Base for all configuration-related errors."""


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file and return its top-level mapping.

    Values remain as raw Python objects; Pydantic ``model_validate`` handles
    type coercion and validation.
    """
    with path.open() as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ConfigError(f"Expected YAML mapping in {path}, got {type(data).__name__}")
    return data


def _validate[T: BaseModel](model_cls: type[T], data: dict[str, Any], path: Path) -> T:
    """Pass raw dict to Pydantic and raise a descriptive error on failure."""
    try:
        return model_cls.model_validate(data)
    except ValidationError as e:
        raise ConfigError(f"Invalid {model_cls.__name__} in {path}:\n{e}") from e
