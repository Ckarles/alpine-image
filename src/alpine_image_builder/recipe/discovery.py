"""Recipe module import, instantiation, and discovery."""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

from .._yaml import ConfigError
from ..inventory import Platform, Plugin
from .dsl import Recipe


def _import_recipe_class(recipe_py: Path) -> type[Recipe]:
    """Import a recipe module and return the single Recipe subclass defined within.

    Uses ``sys.modules`` as a cache so that repeated loads of the same recipe
    return the already-imported module. This follows the pattern used by
    Django's ``cached_import`` and prevents duplicate module objects in memory.

    .. note::
       The module is inserted into ``sys.modules`` so that relative imports
       inside the recipe work correctly. Recipes are loaded once per process
       lifetime and never reloaded; if you need hot-reloading, clear the
       ``sys.modules`` entry before calling this again.
    """
    module_name = f"alpine_image_builder._recipes.{recipe_py.parent.name.replace('-', '_')}"
    modules = sys.modules

    # Fast path: already imported and fully initialized.
    if module_name in modules:
        module = modules[module_name]
        spec = getattr(module, "__spec__", None)
        if spec is None or getattr(spec, "_initializing", False) is False:
            return _extract_recipe_class(module, recipe_py)

    # Slow path: create, register, and execute the module.
    spec = importlib.util.spec_from_file_location(module_name, recipe_py)
    if spec is None or spec.loader is None:
        raise ConfigError(f"Cannot load recipe module from {recipe_py}")
    module = importlib.util.module_from_spec(spec)
    modules[module_name] = module
    spec.loader.exec_module(module)

    return _extract_recipe_class(module, recipe_py)


def _extract_recipe_class(module: ModuleType, recipe_py: Path) -> type[Recipe]:
    """Find the single Recipe subclass inside an already-loaded module."""
    candidates = [
        v for v in vars(module).values()
        if isinstance(v, type) and issubclass(v, Recipe) and v is not Recipe
    ]
    if len(candidates) == 0:
        raise ConfigError(f"{recipe_py} defines no Recipe subclass")
    if len(candidates) > 1:
        raise ConfigError(
            f"{recipe_py} defines multiple Recipe subclasses: "
            f"{[c.__name__ for c in candidates]}. Exactly one is required."
        )
    return candidates[0]


def _instantiate_recipe(recipe_py: Path, recipe_dir: Path) -> Recipe:
    """Import recipe class, instantiate it, and validate name matches directory."""
    recipe_cls = _import_recipe_class(recipe_py)
    recipe = recipe_cls()
    if recipe.name != recipe_dir.name:
        raise ConfigError(
            f"{recipe_py}: Recipe.name='{recipe.name}' must match directory "
            f"name '{recipe_dir.name}'."
        )
    return recipe


def _validate_recipe_refs(
    recipe: Recipe,
    *,
    plugins: dict[str, Plugin] | None = None,
    platforms: dict[str, Platform] | None = None,
) -> None:
    """Cross-validate recipe references against the loaded registries."""
    if plugins is not None:
        unknown = [p for p in recipe.plugins if p not in plugins]
        if unknown:
            raise ConfigError(
                f"Recipe '{recipe.name}' references unknown plugin(s) {unknown}. "
                f"Known plugins: {sorted(plugins.keys())}"
            )
    if platforms is not None:
        unknown = [p for p in recipe.platforms if p not in platforms]
        if unknown:
            raise ConfigError(
                f"Recipe '{recipe.name}' references unknown platform(s) {unknown}. "
                f"Known platforms: {sorted(platforms.keys())}"
            )


@dataclass(frozen=True)
class LoadedRecipe:
    """A recipe discovered on disk, guaranteed to have a filesystem path."""

    recipe: Recipe
    path: Path


def load_single_recipe(recipe_dir: Path) -> LoadedRecipe:
    """Load a single recipe from its directory (must contain recipe.py).

    Unlike ``discover_recipes``, this does not cross-validate plugins or
    platforms. Useful when the caller already knows the registries or
    when loading inside a Temporal activity where only one recipe is needed.
    """
    recipe_py = recipe_dir / "recipe.py"
    if not recipe_py.is_file():
        raise ConfigError(f"No recipe.py found in {recipe_dir}")
    recipe = _instantiate_recipe(recipe_py, recipe_dir)
    return LoadedRecipe(recipe=recipe, path=recipe_dir)


def discover_recipes(
    recipes_dir: Path,
    *,
    plugins: dict[str, Plugin] | None = None,
    platforms: dict[str, Platform] | None = None,
) -> dict[str, LoadedRecipe]:
    """Import each recipe.py, then cross-validate references against the registries."""
    recipes: dict[str, LoadedRecipe] = {}
    for subdir in sorted(d for d in recipes_dir.iterdir() if d.is_dir()):
        recipe_py = subdir / "recipe.py"
        if not recipe_py.is_file():
            continue
        recipe = _instantiate_recipe(recipe_py, subdir)
        _validate_recipe_refs(recipe, plugins=plugins, platforms=platforms)
        recipes[recipe.name] = LoadedRecipe(recipe=recipe, path=subdir)
    return recipes
