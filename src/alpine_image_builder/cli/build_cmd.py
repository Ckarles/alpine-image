"""Dynamic Click command factory for per-recipe CLI subcommands."""

from pathlib import Path
from typing import Any

import click

from .._yaml import ConfigError
from ..build import build_recipe
from ..inventory import Platform, Plugin
from ..recipe import (
    LoadedRecipe,
    collect_input_choices,
    discover_recipes,
    list_versions,
    load_version_preset,
)


def build_recipe_command(
    loaded: LoadedRecipe,
    version_choices: list[str],
    host_names: list[str],
    input_choices: dict[str, list[str]],
    plugins: dict[str, Plugin],
    platforms_registry: dict[str, Platform],
    project_root: Path,
) -> click.Command:
    """Create a Click command for a specific recipe, including dynamic input options."""
    recipe = loaded.recipe

    params: list[click.Parameter] = [
        click.Option(
            ["--version", "-v"],
            required=True,
            type=click.Choice(version_choices),
            help="Version to build",
        ),
        click.Option(
            ["--ssh-key"],
            required=True,
            type=click.Path(exists=True, dir_okay=False, path_type=Path),
            help="Path to SSH private key",
        ),
        click.Option(
            ["--platform"],
            multiple=True,
            type=click.Choice(recipe.platforms),
            help="Filter platform (repeatable)",
        ),
        click.Option(
            ["--arch"],
            multiple=True,
            type=click.Choice(recipe.archs),
            help="Filter architecture (repeatable)",
        ),
        click.Option(
            ["--host"],
            default=None,
            type=click.Choice(host_names) if host_names else click.STRING,
            help="Host config to use (default: auto-detect)",
        ),
    ]

    for field_name, field in recipe.Inputs.model_fields.items():
        extra = field.json_schema_extra
        extra_dict = extra if isinstance(extra, dict) else {}
        flag = str(extra_dict.get("cli_flag") or f"--{field_name.replace('_', '-')}")
        decls: list[str] = [flag]
        short = extra_dict.get("cli_short")
        if isinstance(short, str):
            decls.append(short)
        choices = input_choices.get(field_name)
        click_type = click.Choice(choices) if choices else click.STRING
        params.append(
            click.Option(
                decls,
                default=None,
                type=click_type,
                help=field.description or "",
            )
        )

    def callback(
        version: str,
        ssh_key: Path,
        platform: tuple[str, ...],
        arch: tuple[str, ...],
        host: str | None,
        **input_kwargs: str,
    ) -> None:
        try:
            build_recipe(
                loaded=loaded,
                version_id=version,
                ssh_key=ssh_key,
                cli_platforms=list(platform) or None,
                cli_archs=list(arch) or None,
                host_name=host,
                cli_inputs=input_kwargs,
                project_root=project_root,
                plugins=plugins,
                platforms_registry=platforms_registry,
            )
        except (RuntimeError, FileNotFoundError) as exc:
            raise click.ClickException(str(exc)) from exc

    return click.Command(
        name=recipe.name,
        help=(recipe.__doc__ or "").strip(),
        params=params,
        callback=callback,
    )


class _BuildGroup(click.Group):
    """Lazy-loading Click group that discovers recipes only when accessed."""

    def __init__(self, project_root: Path, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._project_root = project_root
        self._loaded = False

    def _load_recipes(self) -> None:
        if self._loaded:
            return
        from ..inventory import load_all_hosts, load_all_platforms, load_all_plugins

        plugins = load_all_plugins(self._project_root / "plugins")
        platforms = load_all_platforms(self._project_root / "platforms", plugins=plugins)
        hosts = load_all_hosts(self._project_root / "hosts")
        recipes = discover_recipes(
            self._project_root / "recipes", plugins=plugins, platforms=platforms,
        )
        host_names = sorted(hosts.keys())
        for loaded in recipes.values():
            version_choices = list_versions(loaded.path)
            version_presets = [
                load_version_preset(loaded.path / "versions" / f"{v}.yaml", loaded.recipe)
                for v in version_choices
            ]
            input_choices = collect_input_choices(loaded.recipe, version_presets)
            self.add_command(
                build_recipe_command(
                    loaded, version_choices, host_names, input_choices,
                    plugins, platforms, self._project_root,
                )
            )
        self._loaded = True

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        self._load_recipes()
        return super().get_command(ctx, cmd_name)

    def list_commands(self, ctx: click.Context) -> list[str]:
        self._load_recipes()
        return super().list_commands(ctx)
