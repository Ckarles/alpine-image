"""Tests for Recipe base class validation and DSL helpers."""

import pytest
from pydantic import BaseModel, ConfigDict

from alpine_image_builder.recipe import (
    InputField,
    Output,
    PerArchTemplate,
    Recipe,
    RequiredArtifact,
)


class TestRecipeSubclassValidation:
    def test_missing_single_required_attr(self) -> None:
        with pytest.raises(TypeError, match="missing required class attribute"):
            class Bad(Recipe):
                name = "bad"
                url_patterns = {}

    def test_missing_multiple_required_attrs(self) -> None:
        with pytest.raises(TypeError, match="missing required class attribute"):
            class Bad(Recipe):
                name = "bad"
                # missing platforms, archs, plugins, url_patterns

    def test_valid_subclass(self) -> None:
        class Good(Recipe):
            name = "good"
            platforms = ["qemu"]
            archs = ["aarch64"]
            plugins = ["qemu"]
            url_patterns = {}

        assert Good.name == "good"

    def test_tuple_defaults(self) -> None:
        class Minimal(Recipe):
            name = "minimal"
            platforms = ["qemu"]
            archs = ["aarch64"]
            plugins = ["qemu"]
            url_patterns = {}

        assert Minimal.requires == ()
        assert Minimal.outputs == ()
        assert Minimal.pre_render == ()

    def test_direct_instantiation_forbidden(self) -> None:
        with pytest.raises(TypeError, match="abstract"):
            Recipe()

    def test_empty_name_rejected(self) -> None:
        with pytest.raises(TypeError, match="non-empty str"):
            class Bad(Recipe):
                name = ""
                platforms = ["qemu"]
                archs = ["aarch64"]
                plugins = ["qemu"]
                url_patterns = {}

    @pytest.mark.parametrize("attr", ["platforms", "archs", "plugins"])
    def test_non_list_attr_rejected(self, attr: str) -> None:
        with pytest.raises(TypeError, match=r"must be a list\[str\]"):
            code = f"""
class Bad(Recipe):
    name = "bad"
    platforms = ["qemu"]
    archs = ["aarch64"]
    plugins = ["qemu"]
    url_patterns = {{}}
    {attr} = "not-a-list"
"""
            exec(code)

    @pytest.mark.parametrize("attr", ["platforms", "archs", "plugins"])
    def test_list_with_non_string_elements_rejected(self, attr: str) -> None:
        with pytest.raises(TypeError, match=r"must be a list\[str\]"):
            code = f"""
class Bad(Recipe):
    name = "bad"
    platforms = ["qemu"]
    archs = ["aarch64"]
    plugins = ["qemu"]
    url_patterns = {{}}
    {attr} = [1, 2]
"""
            exec(code)

    def test_url_patterns_not_dict_rejected(self) -> None:
        with pytest.raises(TypeError, match=r"dict\[str, str\]"):
            class Bad(Recipe):
                name = "bad"
                platforms = ["qemu"]
                archs = ["aarch64"]
                plugins = ["qemu"]
                url_patterns = "not-a-dict"  # type: ignore[assignment]

    def test_unknown_url_placeholder_rejected(self) -> None:
        with pytest.raises(TypeError, match="unknown placeholder"):
            class Bad(Recipe):
                name = "bad"
                platforms = ["qemu"]
                archs = ["aarch64"]
                plugins = ["qemu"]
                url_patterns = {"base": "https://{unknown}/"}

    def test_reserved_input_collision_rejected(self) -> None:
        # Define Inputs at module scope so it is resolvable inside the class body.
        class _VersionInputs(BaseModel):  # type: ignore[no-redef]
            model_config = ConfigDict(extra="forbid", frozen=True)
            version: str = InputField("3.20", description="Version")  # type: ignore[assignment]

        with pytest.raises(TypeError, match="collide with reserved URL placeholders"):
            class Bad(Recipe):
                name = "bad"
                platforms = ["qemu"]
                archs = ["aarch64"]
                plugins = ["qemu"]
                Inputs = _VersionInputs
                url_patterns = {}


class TestInputField:
    def test_basic(self) -> None:
        class Inputs(BaseModel):
            model_config = ConfigDict(extra="forbid", frozen=True)
            mirror: str = InputField("default", description="Mirror URL")  # type: ignore[assignment]

        inp = Inputs()
        assert inp.mirror == "default"

    def test_choices(self) -> None:
        class Inputs(BaseModel):
            model_config = ConfigDict(extra="forbid", frozen=True)
            opt: str = InputField("a", description="Option", choices=["a", "b"])  # type: ignore[assignment]

        inp = Inputs()
        assert inp.opt == "a"

    def test_cli_flag(self) -> None:
        class Inputs(BaseModel):
            model_config = ConfigDict(extra="forbid", frozen=True)
            mirror: str = InputField("default", description="Mirror", cli_flag="--mirror-url")  # type: ignore[assignment]

        field = Inputs.model_fields["mirror"]
        extra = field.json_schema_extra
        assert isinstance(extra, dict)
        assert extra.get("cli_flag") == "--mirror-url"

    def test_cli_short(self) -> None:
        class Inputs(BaseModel):
            model_config = ConfigDict(extra="forbid", frozen=True)
            mirror: str = InputField("default", description="Mirror", cli_short="-m")  # type: ignore[assignment]

        field = Inputs.model_fields["mirror"]
        extra = field.json_schema_extra
        assert isinstance(extra, dict)
        assert extra.get("cli_short") == "-m"


class TestOutput:
    def test_for_each_default(self) -> None:
        out = Output(path="dist/{arch}")
        assert out.for_each == "archs"

    def test_for_each_none(self) -> None:
        out = Output(path="dist/image", for_each=None)
        assert out.for_each is None


class TestRequiredArtifact:
    def test_defaults(self) -> None:
        req = RequiredArtifact(recipe="base", path="dist/{arch}")
        assert req.for_each == "archs"
        assert req.message == ""

    def test_custom_message(self) -> None:
        req = RequiredArtifact(
            recipe="base",
            path="dist/{arch}",
            message="Please build {recipe} first",
        )
        assert req.message == "Please build {recipe} first"


class TestPerArchTemplate:
    def test_basic(self) -> None:
        tpl = PerArchTemplate(template="boot.j2", output="boot-{arch}.cfg")
        assert tpl.template == "boot.j2"
        assert tpl.output == "boot-{arch}.cfg"
