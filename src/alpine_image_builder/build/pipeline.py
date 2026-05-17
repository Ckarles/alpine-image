"""Build orchestration: resolve inputs, workspace, templates, Packer invocation."""

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel

from ..inventory import Host, Platform, Plugin, detect_local_host, load_host
from ..recipe import LoadedRecipe, Recipe, VersionPreset, load_version_preset
from .context import BuildContext
from .packer import run_packer
from .templates import create_env, render_template

logger = logging.getLogger(__name__)


@dataclass
class BuildOutcome:
    """Result of a successful build_recipe call."""

    work_dir: Path
    pkr_hcl_path: Path
    archs: list[str]


def _resolve_inputs(
    recipe: Recipe, path: Path, version_id: str, cli_inputs: dict[str, str]
) -> tuple[BaseModel, VersionPreset]:
    """Resolve effective inputs from defaults, version preset overrides, and CLI."""
    preset = load_version_preset(path / "versions" / f"{version_id}.yaml", recipe)
    defaults = {
        name: f.default for name, f in recipe.Inputs.model_fields.items()
        if not f.is_required()
    }
    cli_set = {k: v for k, v in cli_inputs.items() if v is not None}
    inputs = recipe.Inputs(**{**defaults, **preset.data.overrides, **cli_set})
    return inputs, preset


def _resolve_host(hosts_dir: Path, host_name: str | None) -> Host:
    """Load named host or auto-detect from /etc/os-release."""
    if host_name:
        return load_host(hosts_dir / f"{host_name}.yaml")
    return detect_local_host(hosts_dir)


def _resolve_dimensions(
    recipe: Recipe,
    cli_platforms: list[str] | None,
    cli_archs: list[str] | None,
    platforms_registry: dict[str, Platform],
) -> tuple[list[Platform], list[str]]:
    """Select platforms and architectures that satisfy all selected platforms."""
    selected_platform_names = cli_platforms or recipe.platforms
    platforms = [platforms_registry[n] for n in selected_platform_names]
    selected_archs = cli_archs or recipe.archs
    archs = [a for a in selected_archs if all(a in p.archs for p in platforms)]
    if not archs:
        raise RuntimeError(
            f"No architectures satisfy all selected platforms. "
            f"Requested: {selected_archs}. "
            f"Platform support: {[(p.name, p.archs) for p in platforms]}"
        )
    return platforms, archs


def _prepare_workspace(project_root: Path, recipe: Recipe) -> Path:
    """Create (or recreate) the working directory for this recipe."""
    work_dir = project_root / "generated" / recipe.name
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True)
    return work_dir


def _copy_supporting_files(path: Path, work_dir: Path) -> None:
    """Copy static files from recipe's files/ directory into the workspace."""
    files_dir = path / "files"
    if files_dir.exists():
        for f in files_dir.iterdir():
            shutil.copy2(f, work_dir / f.name)


def _link_required_artifacts(
    project_root: Path,
    recipe: Recipe,
    archs: list[str],
    preset: VersionPreset,
    work_dir: Path,
    ssh_key: Path,
) -> None:
    """Symlink artifacts required from other recipe builds."""
    for req in recipe.requires:
        iter_archs: list[str | None] = list(archs) if req.for_each == "archs" else [None]
        for arch in iter_archs:
            fmt = {
                "arch": arch or "",
                "version": preset.data.version,
                "ssh_key": str(ssh_key),
                "recipe": req.recipe,
            }
            relpath = req.path.format(**fmt)
            src = project_root / "generated" / req.recipe / relpath
            if not src.exists():
                msg = (req.message or f"Required artifact missing: {src}").format(**fmt)
                raise FileNotFoundError(msg)
            dst = work_dir / relpath
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.is_symlink() or dst.exists():
                dst.unlink()
            dst.symlink_to(src)


def _clean_declared_outputs(recipe: Recipe, work_dir: Path, archs: list[str]) -> None:
    """Remove any stale output directories declared by the recipe."""
    for out in recipe.outputs:
        iter_archs = list(archs) if out.for_each == "archs" else [None]
        for arch in iter_archs:
            shutil.rmtree(work_dir / out.path.format(arch=arch or ""), ignore_errors=True)


def _render_templates(
    path: Path, recipe: Recipe, build_ctx: BuildContext, work_dir: Path
) -> Path:
    """Render all recipe templates into the workspace. Returns path to main .pkr.hcl."""
    env = create_env([path / "templates"])
    for pre in recipe.pre_render:
        for arch in build_ctx.archs:
            (work_dir / pre.output.format(arch=arch)).write_text(
                render_template(env, pre.template, {"ctx": build_ctx, "arch": arch})
            )
    pkr_hcl_path = work_dir / f"{recipe.name}.pkr.hcl"
    pkr_hcl_path.write_text(render_template(env, "main.j2", {"ctx": build_ctx}))
    logger.info("Generated Packer template: %s", pkr_hcl_path)
    return pkr_hcl_path


def _invoke_packer(project_root: Path, pkr_hcl_path: Path, ssh_key: str) -> None:
    """Run Packer and propagate its exit code."""
    rc = run_packer(project_root, pkr_hcl_path, ssh_key)
    if rc != 0:
        raise RuntimeError(f"Packer exited with code {rc}")


def build_recipe(
    loaded: LoadedRecipe,
    version_id: str,
    ssh_key: Path,
    cli_platforms: list[str] | None,
    cli_archs: list[str] | None,
    host_name: str | None,
    cli_inputs: dict[str, str],
    *,
    project_root: Path,
    plugins: dict[str, Plugin],
    platforms_registry: dict[str, Platform],
) -> BuildOutcome:
    """Orchestrate the full build pipeline for a recipe."""
    recipe = loaded.recipe
    path = loaded.path

    inputs, preset = _resolve_inputs(recipe, path, version_id, cli_inputs)
    host = _resolve_host(project_root / "hosts", host_name)
    platforms, archs = _resolve_dimensions(recipe, cli_platforms, cli_archs, platforms_registry)
    selected_plugins = [plugins[n] for n in recipe.plugins]

    work_dir = _prepare_workspace(project_root, recipe)
    _copy_supporting_files(path, work_dir)

    _link_required_artifacts(project_root, recipe, archs, preset, work_dir, ssh_key)
    _clean_declared_outputs(recipe, work_dir, archs)

    build_ctx = BuildContext(
        recipe=recipe,
        version=preset.data.version,
        version_id=version_id,
        inputs=inputs,
        host=host,
        platforms=platforms,
        plugins=selected_plugins,
        archs=archs,
        ssh_key=str(ssh_key),
    )
    pkr_hcl_path = _render_templates(path, recipe, build_ctx, work_dir)
    _invoke_packer(project_root, pkr_hcl_path, build_ctx.ssh_key)

    return BuildOutcome(work_dir=work_dir, pkr_hcl_path=pkr_hcl_path, archs=archs)
