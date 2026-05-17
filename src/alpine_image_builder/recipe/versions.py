"""Version preset discovery and loading."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ModelWrapValidatorHandler,
    ValidationError,
    ValidationInfo,
    model_validator,
)

from .._yaml import ConfigError
from ..inventory.schemas import _StrictModel
from .dsl import Recipe


class VersionPresetData(_StrictModel):
    """YAML payload for a version preset."""

    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=False)
    version: str = Field(min_length=1, pattern=r"^\d+\.\d+(\.\d+)?$")
    overrides: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="wrap")
    @classmethod
    def _check_known_keys(
        cls,
        data: Any,
        handler: ModelWrapValidatorHandler["VersionPresetData"],
        info: ValidationInfo,
    ) -> "VersionPresetData":
        if not isinstance(data, dict):
            return handler(data)

        ctx = info.context or {}
        declared_inputs: set[str] = ctx.get("declared_inputs", set())

        unknown = set(data) - {"version"} - declared_inputs
        if unknown:
            raise ValueError(f"Unknown override key(s): {sorted(unknown)}")

        version_value = data.get("version")
        if version_value is None:
            raise ValueError("Missing 'version' key")

        overrides = {k: str(v) for k, v in data.items() if k != "version"}
        return handler({"version": str(version_value), "overrides": overrides})


@dataclass(frozen=True)
class VersionPreset:
    """Runtime wrapper that pairs YAML data with its file identity."""

    id: str
    path: Path
    data: VersionPresetData


def list_versions(recipe_dir: Path) -> list[str]:
    versions_dir = recipe_dir / "versions"
    if not versions_dir.exists():
        return []
    return sorted(f.stem for f in versions_dir.glob("*.yaml"))


def load_version_preset(version_path: Path, recipe: Recipe) -> VersionPreset:
    if not version_path.is_file():
        raise ConfigError(f"Version preset not found: {version_path}")
    raw = yaml.safe_load(version_path.read_text())
    try:
        data = VersionPresetData.model_validate(
            raw,
            context={"declared_inputs": set(recipe.Inputs.model_fields)},
        )
    except ValidationError as e:
        raise ConfigError(f"Invalid version preset in {version_path}:\n{e}") from e
    return VersionPreset(
        id=version_path.stem,
        path=version_path,
        data=data,
    )


def collect_input_choices(
    recipe: Recipe, version_presets: list[VersionPreset]
) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for field_name, field in recipe.Inputs.model_fields.items():
        extra = field.json_schema_extra
        extra_dict = extra if isinstance(extra, dict) else {}
        choices = extra_dict.get("choices")
        values: set[str] = set()
        if isinstance(choices, list):
            for c in choices:
                if isinstance(c, str):
                    values.add(c)
        for preset in version_presets:
            if field_name in preset.data.overrides:
                v = preset.data.overrides[field_name]
                if isinstance(v, str):
                    values.add(v)
        if values:
            result[field_name] = sorted(values)
    return result
