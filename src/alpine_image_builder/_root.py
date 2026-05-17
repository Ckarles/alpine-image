"""Project root detection and path helpers."""

from pathlib import Path


def find_project_root() -> Path:
    """Walk up from CWD looking for pyproject.toml."""
    cwd = Path.cwd().resolve()
    for path in [cwd, *cwd.parents]:
        if (path / "pyproject.toml").exists():
            return path
    raise RuntimeError(
        "Could not find project root (no pyproject.toml). "
        "Run from within the alpine-image project."
    )
