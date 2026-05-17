"""Recipe abstract base class and supporting declarative models."""

from __future__ import annotations

import abc
import re
from pathlib import Path
from typing import Any, ClassVar, Literal, cast

from pydantic import BaseModel, ConfigDict, Field
from pydantic.fields import FieldInfo


def InputField(
    default: Any = ...,
    *,
    description: str,
    choices: list[Any] | None = None,
    cli_flag: str | None = None,
    cli_short: str | None = None,
) -> FieldInfo:
    extra: dict[str, Any] = {}
    if choices is not None:
        extra["choices"] = choices
    if cli_flag is not None:
        extra["cli_flag"] = cli_flag
    if cli_short is not None:
        extra["cli_short"] = cli_short
    return cast(FieldInfo, Field(
        default=default,
        description=description,
        json_schema_extra=extra or None,
    ))


class _StrictBase(BaseModel):
    """Base for internal helper models. Forbids unknown fields, immutable instances."""
    model_config = ConfigDict(extra="forbid", frozen=True)


class Output(_StrictBase):
    path: str
    for_each: Literal["archs"] | None = "archs"


class RequiredArtifact(_StrictBase):
    recipe: str
    path: str
    for_each: Literal["archs"] | None = "archs"
    message: str = ""


class PerArchTemplate(_StrictBase):
    template: str
    output: str


class _EmptyInputs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Recipe(abc.ABC):
    """Abstract base class for image-build recipes.

    Subclasses declare their identity (`name`), dimensions (`platforms`, `archs`),
    plugins, inputs, outputs, dependencies, and any per-arch auxiliary templates
    as class-level data. The framework reads this declaration to drive the CLI,
    the build context, and the Packer template renderer.

    Instances are constructed once by `discover_recipes`; subclasses should not
    override `__init__`.
    """

    # Contract — subclasses MUST set these. Enforced by __init_subclass__.
    name: ClassVar[str]
    platforms: ClassVar[list[str]]
    archs: ClassVar[list[str]]
    plugins: ClassVar[list[str]]
    url_patterns: ClassVar[dict[str, str]]

    # Optional — default values provided (immutable to prevent cross-class mutation).
    requires: ClassVar[tuple[RequiredArtifact, ...]] = ()
    pre_render: ClassVar[tuple[PerArchTemplate, ...]] = ()
    outputs: ClassVar[tuple[Output, ...]] = ()
    Inputs: ClassVar[type[BaseModel]] = _EmptyInputs

    _REQUIRED_ATTRS: ClassVar[frozenset[str]] = frozenset(
        {"name", "platforms", "archs", "plugins", "url_patterns"}
    )
    _RESERVED_PLACEHOLDERS: ClassVar[frozenset[str]] = frozenset(
        {"version", "major", "minor", "patch", "arch"}
    )

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        # 1. Required attributes are present at class-definition time.
        missing = [a for a in cls._REQUIRED_ATTRS if not hasattr(cls, a)]
        if missing:
            raise TypeError(
                f"Recipe subclass '{cls.__name__}' is missing required class "
                f"attribute(s): {sorted(missing)}"
            )

        # 2. Input names cannot shadow reserved URL placeholders.
        collisions = set(cls.Inputs.model_fields).intersection(cls._RESERVED_PLACEHOLDERS)
        if collisions:
            raise TypeError(
                f"Recipe '{cls.__name__}' declares input(s) {sorted(collisions)} "
                f"which collide with reserved URL placeholders "
                f"{sorted(cls._RESERVED_PLACEHOLDERS)}."
            )

        # 3. name/platforms/archs/plugins basic type sanity.
        if not isinstance(cls.name, str) or not cls.name:
            raise TypeError(f"Recipe '{cls.__name__}'.name must be a non-empty str.")
        for attr in ("platforms", "archs", "plugins"):
            value = getattr(cls, attr)
            if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
                raise TypeError(
                    f"Recipe '{cls.__name__}'.{attr} must be a list[str], got {value!r}."
                )

        # 4. Validate url_patterns placeholders at class-definition time.
        cls._validate_url_patterns()

    @classmethod
    def _validate_url_patterns(cls) -> None:
        """Check that every placeholder referenced in url_patterns is resolvable.

        A placeholder is valid if it is:
        - a reserved built-in (version, major, minor, patch, arch), or
        - a declared recipe input field, or
        - an earlier key in url_patterns itself.
        """
        if not isinstance(cls.url_patterns, dict):
            raise TypeError(
                f"Recipe '{cls.name}'.url_patterns must be a dict[str, str], "
                f"got {type(cls.url_patterns).__name__}."
            )
        allowed: set[str] = set(cls._RESERVED_PLACEHOLDERS)
        allowed |= set(cls.Inputs.model_fields)
        allowed |= set(cls.url_patterns)
        pattern = re.compile(r"\{(\w+)\}")
        for key, tmpl in cls.url_patterns.items():
            for ph in pattern.findall(tmpl):
                if ph not in allowed:
                    raise TypeError(
                        f"Recipe '{cls.name}' url_patterns['{key}'] references "
                        f"unknown placeholder '{ph}'. Allowed: {sorted(allowed)}"
                    )

    def __new__(cls, *args: Any, **kwargs: Any) -> Recipe:
        if cls is Recipe:
            raise TypeError("Recipe is abstract; subclass it.")
        return super().__new__(cls)
