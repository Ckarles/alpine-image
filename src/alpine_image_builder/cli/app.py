"""CLI wiring: app definition, list command, and runtime command registration.

Pure Click — no Typer. Per-recipe ``build`` subcommands are generated at
startup and attached to a ``build`` Click group.
"""

import click

from .._root import find_project_root
from .build_cmd import _BuildGroup
from .list_cmd import list_recipes


def main() -> None:
    project_root = find_project_root()
    click_app = click.Group(help="Alpine Image Builder - build Alpine Linux images via Packer")
    click_app.add_command(list_recipes)
    click_app.add_command(
        _BuildGroup(project_root=project_root, help="Build image recipes"),
        name="build",
    )
    click_app()
