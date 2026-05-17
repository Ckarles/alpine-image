"""Tests for Pydantic inventory models and version presets."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from alpine_image_builder.inventory import (
    Host,
    HostDetect,
    HostFirmwareEntry,
    Platform,
    Plugin,
)
from alpine_image_builder.recipe import VersionPreset, VersionPresetData


class TestStrictModel:
    """_StrictModel is an internal base, but its behavior underpins all inventory schemas."""

    def test_extra_field_rejected(self) -> None:
        with pytest.raises(ValidationError, match="extra_forbidden"):
            Plugin.model_validate({"name": "qemu", "version": "1", "source": "local", "extra": "x"})

    def test_frozen_instance(self) -> None:
        plugin = Plugin.model_validate({"name": "qemu", "version": "1", "source": "local"})
        with pytest.raises(ValidationError, match="frozen"):
            plugin.name = "other"

    def test_str_strip_whitespace(self) -> None:
        plugin = Plugin.model_validate({"name": "  qemu  ", "version": "1", "source": "local"})
        assert plugin.name == "qemu"


class TestPlugin:
    def test_valid(self) -> None:
        plugin = Plugin.model_validate({"name": "qemu", "version": "1.0", "source": "local"})
        assert plugin.name == "qemu"
        assert plugin.version == "1.0"
        assert plugin.source == "local"

    @pytest.mark.parametrize("field", ["name", "version", "source"])
    def test_empty_string_rejected(self, field: str) -> None:
        data = {"name": "qemu", "version": "1", "source": "local"}
        data[field] = ""
        with pytest.raises(ValidationError, match="String should have at least 1 character"):
            Plugin.model_validate(data)


class TestPlatform:
    def test_valid(self) -> None:
        platform = Platform.model_validate(
            {"name": "qemu", "plugin": "qemu", "archs": ["aarch64"]},
            context={"plugins": {"qemu": None}},
        )
        assert platform.name == "qemu"
        assert platform.archs == ["aarch64"]

    def test_unknown_plugin_raises(self) -> None:
        with pytest.raises(ValidationError, match="references unknown plugin"):
            Platform.model_validate(
                {"name": "qemu", "plugin": "missing", "archs": ["aarch64"]},
                context={"plugins": {"qemu": None}},
            )

    def test_no_context_skips_plugin_check(self) -> None:
        # Without context, the plugin validator cannot run — should succeed
        platform = Platform.model_validate(
            {"name": "qemu", "plugin": "qemu", "archs": ["aarch64"]}
        )
        assert platform.plugin == "qemu"

    def test_invalid_arch_rejected(self) -> None:
        with pytest.raises(ValidationError, match="validation error"):
            Platform.model_validate(
                {"name": "qemu", "plugin": "qemu", "archs": ["invalid"]},
            )

    def test_empty_archs_rejected(self) -> None:
        with pytest.raises(ValidationError, match="List should have at least 1 item"):
            Platform.model_validate(
                {"name": "qemu", "plugin": "qemu", "archs": []},
            )


class TestHostDetect:
    def test_valid(self) -> None:
        detect = HostDetect.model_validate({"os": "alpine", "version": "3.20"})
        assert detect.os == "alpine"
        assert detect.version == "3.20"

    def test_empty_os_rejected(self) -> None:
        with pytest.raises(ValidationError, match="String should have at least 1 character"):
            HostDetect.model_validate({"os": "", "version": "3.20"})


class TestHostFirmwareEntry:
    def test_valid(self) -> None:
        entry = HostFirmwareEntry.model_validate({"code": "edk2-aarch64", "vars": "edk2-arm-vars"})
        assert entry.code == "edk2-aarch64"
        assert entry.vars == "edk2-arm-vars"


class TestHost:
    def test_valid(self) -> None:
        host = Host.model_validate(
            {
                "name": "alpine",
                "detect": {"os": "alpine", "version": "3.20"},
            }
        )
        assert host.name == "alpine"
        assert host.detect.os == "alpine"

    def test_firmware(self) -> None:
        host = Host.model_validate(
            {
                "name": "alpine",
                "detect": {"os": "alpine", "version": "3.20"},
                "firmware": {
                    "aarch64": {"code": "edk2-aarch64", "vars": "edk2-arm-vars"},
                },
            }
        )
        assert host.firmware["aarch64"].code == "edk2-aarch64"

    def test_empty_name_rejected(self) -> None:
        with pytest.raises(ValidationError, match="String should have at least 1 character"):
            Host.model_validate(
                {"name": "", "detect": {"os": "alpine", "version": "3.20"}}
            )

    def test_default_firmware_empty(self) -> None:
        host = Host.model_validate(
            {"name": "alpine", "detect": {"os": "alpine", "version": "3.20"}}
        )
        assert host.firmware == {}

    def test_default_qemu_empty(self) -> None:
        host = Host.model_validate(
            {"name": "alpine", "detect": {"os": "alpine", "version": "3.20"}}
        )
        assert host.qemu == {}


class TestVersionPresetData:
    def test_valid(self) -> None:
        data = VersionPresetData.model_validate({"version": "3.20.0"})
        assert data.version == "3.20.0"
        assert data.overrides == {}

    def test_with_overrides(self) -> None:
        data = VersionPresetData.model_validate(
            {"version": "3.20.0", "mirror": "custom"},
            context={"declared_inputs": {"mirror"}},
        )
        assert data.overrides == {"mirror": "custom"}

    def test_missing_version(self) -> None:
        with pytest.raises(ValidationError, match="Missing 'version' key"):
            VersionPresetData.model_validate({})

    def test_unknown_override(self) -> None:
        with pytest.raises(ValidationError, match="Unknown override key"):
            VersionPresetData.model_validate(
                {"version": "3.20.0", "bad_key": "val"},
                context={"declared_inputs": set()},
            )

    @pytest.mark.parametrize(
        "bad_version,expected_match",
        [
            ("not-a-version", "String should match pattern"),
            ("3", "String should match pattern"),
            ("3.a", "String should match pattern"),
            ("", "String should have at least 1 character"),
        ],
    )
    def test_invalid_version_pattern_rejected(self, bad_version: str, expected_match: str) -> None:
        with pytest.raises(ValidationError, match=expected_match):
            VersionPresetData.model_validate({"version": bad_version})


class TestVersionPreset:
    def test_runtime_wrapper(self) -> None:
        data = VersionPresetData.model_validate({"version": "3.20.0"})
        preset = VersionPreset(id="stable", path=Path("/tmp/stable.yaml"), data=data)
        assert preset.id == "stable"
        assert preset.data.version == "3.20.0"
        assert preset.path == Path("/tmp/stable.yaml")
