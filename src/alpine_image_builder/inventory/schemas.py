"""Pydantic models for project inventory (plugins, platforms, hosts)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, model_validator


class _StrictModel(BaseModel):
    """Base for all externally-sourced models: reject extras, immutable, validate defaults."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        validate_default=True,
        str_strip_whitespace=True,
    )


class Plugin(_StrictModel):
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    source: str = Field(min_length=1)


class Platform(_StrictModel):
    name: str = Field(min_length=1)
    plugin: str = Field(min_length=1)
    archs: list[Literal["aarch64", "x86_64"]] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_plugin_reference(self, info: ValidationInfo) -> "Platform":
        ctx = info.context or {}
        plugins = ctx.get("plugins") if isinstance(ctx, dict) else None
        if plugins is not None and self.plugin not in plugins:
            raise ValueError(
                f"Platform '{self.name}' references unknown plugin '{self.plugin}'. "
                f"Known plugins: {sorted(plugins.keys())}"
            )
        return self


class HostDetect(_StrictModel):
    os: str = Field(min_length=1)
    version: str = Field(min_length=1)


class HostFirmwareEntry(_StrictModel):
    code: str = Field(min_length=1)
    vars: str = Field(min_length=1)


class Host(_StrictModel):
    name: str = Field(min_length=1)
    detect: HostDetect
    firmware: dict[Literal["aarch64", "x86_64"], HostFirmwareEntry] = Field(default_factory=dict)
    qemu: dict[str, str] = Field(default_factory=dict)
