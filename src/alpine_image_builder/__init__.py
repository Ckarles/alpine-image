"""Alpine Image Builder - Python CLI for building Alpine Linux images via Packer."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__: str = version("alpine-image-builder")
except PackageNotFoundError:
    __version__ = "0.0.0+dev"
