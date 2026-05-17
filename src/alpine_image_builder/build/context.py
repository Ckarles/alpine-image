"""BuildContext: resolved configuration + URL pattern resolution."""

from dataclasses import dataclass, field

from pydantic import BaseModel

from ..inventory import Host, Platform, Plugin
from ..recipe import Recipe


@dataclass
class BuildContext:
    recipe: Recipe
    version: str
    version_id: str
    inputs: BaseModel
    host: Host
    platforms: list[Platform]
    plugins: list[Plugin]
    archs: list[str]
    ssh_key: str
    _input_context: dict[str, str] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._input_context = self._build_input_context()

    def _build_input_context(self) -> dict[str, str]:
        """Extract scalar inputs into string context."""
        ctx: dict[str, str] = {}
        for k, v in self.inputs.model_dump().items():
            if isinstance(v, (str, int, float, bool)):
                ctx[k] = str(v)
            else:
                raise TypeError(
                    f"URL pattern context cannot use non-scalar input "
                    f"'{k}' = {v!r}"
                )
        return ctx

    def resolve_url(self, key: str, arch: str) -> str:
        """Resolve a URL pattern from recipe.url_patterns.

        Available placeholders:
          {version}, {major}, {minor}, {patch} — from version string
          {arch} — runtime build arch
          Any recipe input field
          Any earlier-defined pattern key (e.g., {branch}, {base})

        Resolution order: patterns are resolved in declaration order;
        later patterns can reference earlier ones.
        """
        parts = self.version.split(".")
        context: dict[str, str] = {
            "version": self.version,
            "major": parts[0],
            "minor": parts[1] if len(parts) > 1 else "",
            "patch": parts[2] if len(parts) > 2 else "",
            "arch": arch,
            **self._input_context,
        }
        for k, v in self.recipe.url_patterns.items():
            context[k] = v.format(**context)
        if key not in context:
            raise KeyError(
                f"URL pattern key '{key}' not found in recipe '{self.recipe.name}' "
                f"url_patterns. Available keys: {list(self.recipe.url_patterns.keys())}"
            )
        return context[key]

    def required_plugins_block(self) -> dict[str, dict[str, str]]:
        """Return dict for Jinja2 to render required_plugins HCL."""
        return {p.name: {"version": p.version, "source": p.source} for p in self.plugins}
