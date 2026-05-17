"""Project inventory: plugins, platforms, hosts."""

from .._yaml import ConfigError
from .hosts import detect_local_host, load_all_hosts, load_host
from .platforms import load_all_platforms, load_platform
from .plugins import load_all_plugins, load_plugin
from .schemas import Host, HostDetect, HostFirmwareEntry, Platform, Plugin

__all__ = [
    "ConfigError",
    "Host",
    "HostDetect",
    "HostFirmwareEntry",
    "Platform",
    "Plugin",
    "detect_local_host",
    "load_all_hosts",
    "load_all_platforms",
    "load_all_plugins",
    "load_host",
    "load_platform",
    "load_plugin",
]
