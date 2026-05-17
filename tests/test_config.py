"""Tests for configuration loading helpers and recipe discovery internals."""

from pathlib import Path
from types import ModuleType

import pytest
from pydantic import BaseModel, ValidationError

from alpine_image_builder._yaml import ConfigError, _load_yaml, _validate
from alpine_image_builder.inventory import Platform, Plugin
from alpine_image_builder.recipe import LoadedRecipe, Recipe
from alpine_image_builder.recipe.discovery import (
    _extract_recipe_class,
    _instantiate_recipe,
    _validate_recipe_refs,
    load_single_recipe,
)


class TestConfigError:
    def test_is_exception_subclass(self) -> None:
        assert issubclass(ConfigError, Exception)

    def test_message_preserved(self) -> None:
        with pytest.raises(ConfigError, match="boom"):
            raise ConfigError("boom")

    def test_chains_from_other_exception(self) -> None:
        original = ValueError("original")
        with pytest.raises(ConfigError) as exc_info:
            raise ConfigError("wrapped") from original
        assert exc_info.value.__cause__ is original


class TestLoadYaml:
    def test_loads_valid_mapping(self, tmp_path: Path) -> None:
        path = tmp_path / "test.yaml"
        path.write_text("name: test\nvalue: 42\n")
        data = _load_yaml(path)
        assert data == {"name": "test", "value": 42}

    def test_rejects_non_mapping(self, tmp_path: Path) -> None:
        path = tmp_path / "test.yaml"
        path.write_text("- a\n- b\n")
        with pytest.raises(ConfigError, match="Expected YAML mapping"):
            _load_yaml(path)

    def test_rejects_scalar(self, tmp_path: Path) -> None:
        path = tmp_path / "test.yaml"
        path.write_text("just_a_string\n")
        with pytest.raises(ConfigError, match="Expected YAML mapping"):
            _load_yaml(path)


class TestValidate:
    def test_valid_data(self, tmp_path: Path) -> None:
        class Dummy(BaseModel):
            name: str

        result = _validate(Dummy, {"name": "test"}, tmp_path / "d.yaml")
        assert result.name == "test"

    def test_invalid_data_raises_config_error(self, tmp_path: Path) -> None:
        class Dummy(BaseModel):
            name: str

        with pytest.raises(ConfigError, match="Invalid Dummy") as exc_info:
            _validate(Dummy, {"name": 123}, tmp_path / "d.yaml")
        assert isinstance(exc_info.value.__cause__, ValidationError)


class TestExtractRecipeClass:
    def test_finds_single_subclass(self) -> None:
        mod = ModuleType("test_mod")

        class Good(Recipe):
            name = "good"
            platforms = ["qemu"]
            archs = ["aarch64"]
            plugins = ["qemu"]
            url_patterns = {}

        mod.Good = Good  # type: ignore[attr-defined]
        result = _extract_recipe_class(mod, Path("/tmp/recipe.py"))
        assert result is Good

    def test_no_subclass_raises(self) -> None:
        mod = ModuleType("test_mod")
        mod.x = 1  # type: ignore[attr-defined]
        with pytest.raises(ConfigError, match="defines no Recipe subclass"):
            _extract_recipe_class(mod, Path("/tmp/recipe.py"))

    def test_multiple_subclasses_raises(self) -> None:
        mod = ModuleType("test_mod")

        class A(Recipe):
            name = "a"
            platforms = ["qemu"]
            archs = ["aarch64"]
            plugins = ["qemu"]
            url_patterns = {}

        class B(Recipe):
            name = "b"
            platforms = ["qemu"]
            archs = ["aarch64"]
            plugins = ["qemu"]
            url_patterns = {}

        mod.A = A  # type: ignore[attr-defined]
        mod.B = B  # type: ignore[attr-defined]
        with pytest.raises(ConfigError, match="multiple Recipe subclasses"):
            _extract_recipe_class(mod, Path("/tmp/recipe.py"))


class TestInstantiateRecipe:
    def test_name_mismatch_raises(self, tmp_path: Path) -> None:
        recipe_py = tmp_path / "recipe.py"
        recipe_py.write_text(
            "from alpine_image_builder.recipe import Recipe\n"
            "class Dummy(Recipe):\n"
            "    name = 'wrong-name'\n"
            "    platforms = ['qemu']\n"
            "    archs = ['aarch64']\n"
            "    plugins = ['qemu']\n"
            "    url_patterns = {}\n"
        )
        with pytest.raises(ConfigError, match="must match directory name"):
            _instantiate_recipe(recipe_py, tmp_path)


class TestValidateRecipeRefs:
    def test_unknown_plugin_raises(self) -> None:
        class Dummy(Recipe):
            name = "dummy"
            platforms = ["qemu"]
            archs = ["aarch64"]
            plugins = ["qemu", "unknown"]
            url_patterns = {}

        recipe = Dummy()
        plugins = {"qemu": Plugin.model_validate({"name": "qemu", "version": "1", "source": "local"})}
        with pytest.raises(ConfigError, match="unknown plugin"):
            _validate_recipe_refs(recipe, plugins=plugins)

    def test_unknown_platform_raises(self) -> None:
        class Dummy(Recipe):
            name = "dummy"
            platforms = ["qemu", "missing"]
            archs = ["aarch64"]
            plugins = ["qemu"]
            url_patterns = {}

        recipe = Dummy()
        platforms = {
            "qemu": Platform.model_validate(
                {"name": "qemu", "plugin": "qemu", "archs": ["aarch64"]},
                context={"plugins": {"qemu": None}},
            )
        }
        with pytest.raises(ConfigError, match="unknown platform"):
            _validate_recipe_refs(recipe, platforms=platforms)

    def test_no_plugins_registry_skips_validation(self) -> None:
        class Dummy(Recipe):
            name = "dummy"
            platforms = ["qemu"]
            archs = ["aarch64"]
            plugins = ["unknown"]
            url_patterns = {}

        recipe = Dummy()
        # None means skip validation — should not raise
        _validate_recipe_refs(recipe, plugins=None)

    def test_no_platforms_registry_skips_validation(self) -> None:
        class Dummy(Recipe):
            name = "dummy"
            platforms = ["missing"]
            archs = ["aarch64"]
            plugins = ["qemu"]
            url_patterns = {}

        recipe = Dummy()
        _validate_recipe_refs(recipe, platforms=None)


class TestLoadSingleRecipe:
    def test_missing_recipe_py_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ConfigError, match="No recipe.py found"):
            load_single_recipe(tmp_path)

    def test_loads_valid_recipe(self, tmp_path: Path) -> None:
        recipe_py = tmp_path / "recipe.py"
        recipe_py.write_text(
            "from alpine_image_builder.recipe import Recipe\n"
            "class Dummy(Recipe):\n"
            f"    name = {tmp_path.name!r}\n"
            "    platforms = ['qemu']\n"
            "    archs = ['aarch64']\n"
            "    plugins = ['qemu']\n"
            "    url_patterns = {}\n"
        )
        loaded = load_single_recipe(tmp_path)
        assert loaded.recipe.name == tmp_path.name
        assert loaded.path == tmp_path


class TestLoadedRecipe:
    def test_attributes(self) -> None:
        class Dummy(Recipe):
            name = "dummy"
            platforms = ["qemu"]
            archs = ["aarch64"]
            plugins = ["qemu"]
            url_patterns = {}

        loaded = LoadedRecipe(recipe=Dummy(), path=Path("/tmp/dummy"))
        assert loaded.path == Path("/tmp/dummy")
        assert loaded.recipe.name == "dummy"
