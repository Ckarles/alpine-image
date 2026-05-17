"""Platform loaders."""

from pathlib import Path

from pydantic import ValidationError

from .._yaml import ConfigError, _load_yaml
from .schemas import Platform, Plugin


def load_platform(path: Path, *, plugins: dict[str, Plugin] | None = None) -> Platform:
    data = _load_yaml(path)
    try:
        return Platform.model_validate(data, context={"plugins": plugins or {}})
    except ValidationError as e:
        raise ConfigError(f"Invalid Platform in {path}:\n{e}") from e


def load_all_platforms(platforms_dir: Path, plugins: dict[str, Plugin] | None = None) -> dict[str, Platform]:
    platforms: dict[str, Platform] = {}
    for f in sorted(platforms_dir.glob("*.yaml")):
        p = load_platform(f, plugins=plugins)
        platforms[p.name] = p
    return platforms
