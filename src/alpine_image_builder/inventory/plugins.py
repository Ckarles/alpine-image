"""Plugin loaders."""

from pathlib import Path

from .._yaml import _load_yaml, _validate
from .schemas import Plugin


def load_plugin(path: Path) -> Plugin:
    return _validate(Plugin, _load_yaml(path), path)


def load_all_plugins(plugins_dir: Path) -> dict[str, Plugin]:
    plugins: dict[str, Plugin] = {}
    for f in sorted(plugins_dir.glob("*.yaml")):
        p = load_plugin(f)
        plugins[p.name] = p
    return plugins
