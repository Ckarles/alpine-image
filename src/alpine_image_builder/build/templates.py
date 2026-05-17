"""Jinja2 environment setup and template rendering helpers."""

from pathlib import Path
from typing import NotRequired, TypedDict

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from .context import BuildContext


class TemplateContext(TypedDict):
    ctx: BuildContext
    arch: NotRequired[str]


def create_env(template_dirs: list[Path]) -> Environment:
    return Environment(
        loader=FileSystemLoader([str(d) for d in template_dirs]),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )


def render_template(env: Environment, template_name: str, context: TemplateContext) -> str:
    template = env.get_template(str(template_name))
    return template.render(**context)
