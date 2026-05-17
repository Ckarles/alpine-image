"""Temporal activities for the alpine-image-builder worker fleet.

These activities are executed by workers deployed from THIS repository.
External projects define workflows that call these activities by **name**
(string), not by importing this module.

Example (external workflow code, does NOT import this package):

    await workflow.execute_activity(
        "build_image",
        {"recipe_name": "alpine-image-vagrant", "version_id": "3.20", ...},
        start_to_close_timeout=timedelta(hours=2),
    )
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..build import build_recipe
from ..inventory import load_all_platforms, load_all_plugins
from ..recipe import discover_recipes, list_versions, load_single_recipe

try:
    from temporalio import activity as _activity
    _defn: Callable[[F], F] = _activity.defn  # type: ignore[name-defined]
except ModuleNotFoundError:
    def _defn[F: Callable[..., Any]](fn: F) -> F:
        return fn


@dataclass
class BuildImageInput:
    """Input for the build_image activity.

    All fields are JSON-serializable (strings, lists, dicts).
    The activity derives the recipe path from ``project_root/recipes/<name>``.
    """

    recipe_name: str
    version_id: str
    ssh_key: str
    platforms: list[str] | None
    archs: list[str] | None
    host_name: str | None
    inputs: dict[str, str]

    project_root: str


@dataclass
class BuildImageResult:
    """Result of a build_image activity.

    Contains paths to generated artifacts for downstream validation.
    """

    work_dir: str
    pkr_hcl_path: str
    outputs: list[str]  # resolved output paths


@_defn
async def build_image(data: BuildImageInput) -> BuildImageResult:
    """Build a single recipe end-to-end: workspace, templates, Packer.

    This is a single Temporal activity that encapsulates the entire
    build pipeline for one recipe. It is intentionally coarse-grained
    because all steps (prepare workspace, render templates, run Packer)
    are part of one atomic build operation.

    .. note::
       Heartbeating: This activity should heartbeat during the Packer
       build phase. Per Temporal best practices, long-running activities
       (> few minutes) should set a ``heartbeat_timeout`` (~30s) and
       call ``activity.heartbeat()`` regularly.

       See: https://docs.temporal.io/encyclopedia/detecting-activity-failures
       and https://raphaelbeamonte.com/posts/good-practices-for-writing-temporal-workflows-and-activities/

    .. todo::
       Cleanup: Add a ``cleanup_workspace`` activity or flag to remove
       generated directories after a build. This needs design decisions
       about retention policies and when cleanup is safe (e.g., after
       all dependent recipes have consumed the artifacts).
    """
    project_root = Path(data.project_root)
    recipe_path = project_root / "recipes" / data.recipe_name
    ssh_key_path = Path(data.ssh_key)

    # Load recipe and registries from disk (worker must have access to project files)
    loaded = load_single_recipe(recipe_path)
    all_plugins = load_all_plugins(project_root / "plugins")
    platforms_registry = load_all_platforms(project_root / "platforms", plugins=all_plugins)

    # Delegate to the shared build pipeline
    outcome = build_recipe(
        loaded=loaded,
        version_id=data.version_id,
        ssh_key=ssh_key_path,
        cli_platforms=data.platforms,
        cli_archs=data.archs,
        host_name=data.host_name,
        cli_inputs=data.inputs,
        project_root=project_root,
        plugins=all_plugins,
        platforms_registry=platforms_registry,
    )

    # Collect output paths for result
    output_paths: list[str] = []
    for out in loaded.recipe.outputs:
        iter_archs = list(outcome.archs) if out.for_each == "archs" else [None]
        for arch in iter_archs:
            output_paths.append(str(outcome.work_dir / out.path.format(arch=arch or "")))

    return BuildImageResult(
        work_dir=str(outcome.work_dir),
        pkr_hcl_path=str(outcome.pkr_hcl_path),
        outputs=output_paths,
    )


@dataclass
class BuildCatalogEntry:
    """Metadata for a single recipe, exposed to external workflows."""

    name: str
    platforms: list[str]
    archs: list[str]
    versions: list[str]
    dependencies: list[str]
    plugins: list[str]


@dataclass
class BuildCatalog:
    """Full catalog of buildable recipes and their metadata."""

    recipes: list[BuildCatalogEntry]
    project_root: str


@_defn
async def discover_build_catalog(project_root: str) -> BuildCatalog:
    """Discover all recipes and their metadata.

    This is a read-only activity (no side effects) that lets an external
    workflow learn what can be built and how, without importing this package.

    Returns:
        A catalog containing every recipe, its supported platforms/archs,
        available versions, and its cross-recipe dependencies.
    """
    root = Path(project_root)
    plugins_dir = root / "plugins"
    platforms_dir = root / "platforms"

    all_plugins = load_all_plugins(plugins_dir)
    platforms_registry = load_all_platforms(platforms_dir, plugins=all_plugins)
    recipes = discover_recipes(
        root / "recipes", plugins=all_plugins, platforms=platforms_registry
    )

    entries: list[BuildCatalogEntry] = []
    for name, loaded in recipes.items():
        recipe = loaded.recipe
        versions = list_versions(loaded.path)
        deps = [req.recipe for req in recipe.requires]
        entries.append(
            BuildCatalogEntry(
                name=name,
                platforms=list(recipe.platforms),
                archs=list(recipe.archs),
                versions=versions,
                dependencies=deps,
                plugins=list(recipe.plugins),
            )
        )

    return BuildCatalog(recipes=entries, project_root=project_root)
