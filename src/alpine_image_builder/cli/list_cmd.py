"""``list`` command implementation."""

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from .._root import find_project_root
from .._yaml import ConfigError
from ..inventory import (
    detect_local_host,
    load_all_hosts,
    load_all_platforms,
    load_all_plugins,
)
from ..recipe import discover_recipes, list_versions, load_version_preset

console = Console()


@click.command(name="list")
@click.option(
    "--recipe",
    default=None,
    help="List versions for a specific recipe",
)
def list_recipes(recipe: str | None) -> None:
    """List available recipes, hosts, platforms, plugins, or versions."""
    project_root = find_project_root()

    if recipe:
        try:
            plugins = load_all_plugins(project_root / "plugins")
            recipes = discover_recipes(
                project_root / "recipes",
                plugins=plugins,
                platforms=load_all_platforms(project_root / "platforms", plugins=plugins),
            )
            loaded = recipes[recipe]
        except (KeyError, ConfigError) as e:
            click.echo(f"Recipe '{recipe}' not found: {e}", err=True)
            raise click.ClickException(str(e)) from e

        r = loaded.recipe
        table = Table(title=f"Recipe: {recipe}")
        table.add_column("Platforms")
        table.add_column("Archs")
        table.add_column("Plugins")
        table.add_row(
            ", ".join(r.platforms),
            ", ".join(r.archs),
            ", ".join(r.plugins),
        )
        console.print(table)
        console.print()

        versions = list_versions(loaded.path)
        table = Table(title="Versions")
        table.add_column("Version")
        table.add_column("Pinned")
        table.add_column("Overrides")
        for v in versions:
            preset = load_version_preset(loaded.path / "versions" / f"{v}.yaml", r)
            overrides = ", ".join(f"{k}={v_}" for k, v_ in preset.data.overrides.items()) or "-"
            table.add_row(v, preset.data.version, overrides)
        console.print(table)
        return

    plugins = load_all_plugins(project_root / "plugins")
    platforms = load_all_platforms(project_root / "platforms", plugins=plugins)
    recipes = discover_recipes(
        project_root / "recipes",
        plugins=plugins,
        platforms=platforms,
    )
    hosts = load_all_hosts(project_root / "hosts")

    try:
        current_host = detect_local_host(project_root / "hosts")
    except ConfigError:
        current_host = None

    table = Table(title="Recipes")
    table.add_column("Recipe")
    table.add_column("Platforms")
    table.add_column("Archs")
    table.add_column("Versions")
    for loaded in recipes.values():
        versions = list_versions(loaded.path)
        table.add_row(
            loaded.recipe.name,
            ", ".join(loaded.recipe.platforms),
            ", ".join(loaded.recipe.archs),
            ", ".join(versions),
        )
    console.print(table)
    console.print()

    table = Table(title="Hosts")
    table.add_column("Host")
    table.add_column("OS")
    table.add_column("Version")
    table.add_column("Current")
    for host in hosts.values():
        current = "*" if current_host and current_host.name == host.name else ""
        table.add_row(host.name, host.detect.os, host.detect.version, current)
    console.print(table)
    if not current_host:
        console.print(
            "[yellow]Warning: No host matches /etc/os-release. "
            "Use --host to specify explicitly.[/yellow]"
        )
    console.print()

    table = Table(title="Platforms")
    table.add_column("Platform")
    table.add_column("Plugin")
    table.add_column("Archs")
    for platform in platforms.values():
        table.add_row(platform.name, platform.plugin, ", ".join(platform.archs))
    console.print(table)
    console.print()

    table = Table(title="Plugins")
    table.add_column("Plugin")
    table.add_column("Version")
    table.add_column("Source")
    for plugin in plugins.values():
        table.add_row(plugin.name, plugin.version, plugin.source)
    console.print(table)
