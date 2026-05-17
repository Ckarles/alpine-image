"""Tests for BuildContext URL resolution and helpers."""

from pathlib import Path

import pytest
from pydantic import BaseModel, ConfigDict

from alpine_image_builder.build import BuildContext
from alpine_image_builder.inventory import Host, Plugin
from alpine_image_builder.recipe import Recipe


class _FakeInputs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    mirror: str = "example.com"


class _FakeRecipe(Recipe):
    name = "test"
    platforms = ["qemu"]
    archs = ["aarch64"]
    plugins = ["qemu"]
    Inputs = _FakeInputs
    url_patterns = {
        "branch": "v{major}.{minor}",
        "base": "https://{mirror}/alpine/{branch}",
        "iso": "{base}/alpine-{version}-{arch}.iso",
    }


@pytest.fixture
def fake_host() -> Host:
    return Host.model_validate(
        {"name": "h", "detect": {"os": "alpine", "version": "3.20"}}
    )


@pytest.fixture
def fake_plugin() -> Plugin:
    return Plugin.model_validate(
        {"name": "qemu", "version": "1.0.10", "source": "github.com/hashicorp/qemu"}
    )


@pytest.fixture
def build_ctx(fake_host: Host, fake_plugin: Plugin) -> BuildContext:
    return BuildContext(
        recipe=_FakeRecipe(),
        version="3.20.0",
        version_id="stable",
        inputs=_FakeInputs(),
        host=fake_host,
        platforms=[],
        plugins=[fake_plugin],
        archs=["aarch64"],
        ssh_key="/tmp/key",
    )


class TestResolveUrl:
    def test_builtin_placeholders(self, build_ctx: BuildContext) -> None:
        assert build_ctx.resolve_url("branch", "aarch64") == "v3.20"

    def test_input_placeholder(self, build_ctx: BuildContext) -> None:
        assert build_ctx.resolve_url("base", "aarch64") == "https://example.com/alpine/v3.20"

    def test_chained_pattern(self, build_ctx: BuildContext) -> None:
        assert (
            build_ctx.resolve_url("iso", "aarch64")
            == "https://example.com/alpine/v3.20/alpine-3.20.0-aarch64.iso"
        )

    def test_unknown_key_raises(self, build_ctx: BuildContext) -> None:
        with pytest.raises(KeyError, match="not found"):
            build_ctx.resolve_url("missing", "aarch64")


class TestVersionParsing:
    def test_major_only_version(self, fake_host: Host) -> None:
        ctx = BuildContext(
            recipe=_FakeRecipe(),
            version="3",
            version_id="stable",
            inputs=_FakeInputs(),
            host=fake_host,
            platforms=[],
            plugins=[],
            archs=["aarch64"],
            ssh_key="/tmp/key",
        )
        assert ctx.resolve_url("branch", "aarch64") == "v3."

    def test_major_minor_no_patch(self, fake_host: Host) -> None:
        ctx = BuildContext(
            recipe=_FakeRecipe(),
            version="3.20",
            version_id="stable",
            inputs=_FakeInputs(),
            host=fake_host,
            platforms=[],
            plugins=[],
            archs=["aarch64"],
            ssh_key="/tmp/key",
        )
        assert ctx.resolve_url("branch", "aarch64") == "v3.20"
        # patch should be empty string when not present
        assert ctx.resolve_url("iso", "aarch64").endswith("alpine-3.20-aarch64.iso")


class TestScalarInputs:
    def test_int_input_accepted(self, fake_host: Host) -> None:
        class IntInputs(BaseModel):
            model_config = ConfigDict(extra="forbid", frozen=True)
            port: int = 8080

        class IntRecipe(Recipe):
            name = "int"
            platforms = ["qemu"]
            archs = ["aarch64"]
            plugins = ["qemu"]
            Inputs = IntInputs
            url_patterns = {"url": "http://host:{port}"}

        ctx = BuildContext(
            recipe=IntRecipe(),
            version="3.20.0",
            version_id="stable",
            inputs=IntInputs(),
            host=fake_host,
            platforms=[],
            plugins=[],
            archs=["aarch64"],
            ssh_key="/tmp/key",
        )
        assert ctx.resolve_url("url", "aarch64") == "http://host:8080"

    def test_bool_input_accepted(self, fake_host: Host) -> None:
        class BoolInputs(BaseModel):
            model_config = ConfigDict(extra="forbid", frozen=True)
            secure: bool = True

        class BoolRecipe(Recipe):
            name = "bool"
            platforms = ["qemu"]
            archs = ["aarch64"]
            plugins = ["qemu"]
            Inputs = BoolInputs
            url_patterns = {"flag": "{secure}"}

        ctx = BuildContext(
            recipe=BoolRecipe(),
            version="3.20.0",
            version_id="stable",
            inputs=BoolInputs(),
            host=fake_host,
            platforms=[],
            plugins=[],
            archs=["aarch64"],
            ssh_key="/tmp/key",
        )
        assert ctx.resolve_url("flag", "aarch64") == "True"

    def test_float_input_accepted(self, fake_host: Host) -> None:
        class FloatInputs(BaseModel):
            model_config = ConfigDict(extra="forbid", frozen=True)
            ratio: float = 1.5

        class FloatRecipe(Recipe):
            name = "float"
            platforms = ["qemu"]
            archs = ["aarch64"]
            plugins = ["qemu"]
            Inputs = FloatInputs
            url_patterns = {"val": "{ratio}"}

        ctx = BuildContext(
            recipe=FloatRecipe(),
            version="3.20.0",
            version_id="stable",
            inputs=FloatInputs(),
            host=fake_host,
            platforms=[],
            plugins=[],
            archs=["aarch64"],
            ssh_key="/tmp/key",
        )
        assert ctx.resolve_url("val", "aarch64") == "1.5"

    def test_non_scalar_input_raises(self, fake_host: Host) -> None:
        class BadInputs(BaseModel):
            model_config = ConfigDict(extra="forbid", frozen=True)
            extra: list[str] = ["a", "b"]

        class BadRecipe(Recipe):
            name = "bad"
            platforms = ["qemu"]
            archs = ["aarch64"]
            plugins = ["qemu"]
            Inputs = BadInputs
            url_patterns = {"x": "{extra}"}

        with pytest.raises(TypeError, match="non-scalar"):
            BuildContext(
                recipe=BadRecipe(),
                version="3.20.0",
                version_id="stable",
                inputs=BadInputs(),
                host=fake_host,
                platforms=[],
                plugins=[],
                archs=["aarch64"],
                ssh_key="/tmp/key",
            )


class TestRequiredPluginsBlock:
    def test_maps_plugins(self, fake_host: Host, fake_plugin: Plugin) -> None:
        ctx = BuildContext(
            recipe=_FakeRecipe(),
            version="3.20.0",
            version_id="stable",
            inputs=_FakeInputs(),
            host=fake_host,
            platforms=[],
            plugins=[fake_plugin],
            archs=["aarch64"],
            ssh_key="/tmp/key",
        )
        block = ctx.required_plugins_block()
        assert block == {
            "qemu": {
                "version": "1.0.10",
                "source": "github.com/hashicorp/qemu",
            }
        }

    def test_empty_plugins(self, fake_host: Host) -> None:
        ctx = BuildContext(
            recipe=_FakeRecipe(),
            version="3.20.0",
            version_id="stable",
            inputs=_FakeInputs(),
            host=fake_host,
            platforms=[],
            plugins=[],
            archs=["aarch64"],
            ssh_key="/tmp/key",
        )
        assert ctx.required_plugins_block() == {}
