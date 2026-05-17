"""Host loaders."""

from pathlib import Path

from .._yaml import ConfigError, _load_yaml, _validate
from .schemas import Host


def load_host(path: Path) -> Host:
    return _validate(Host, _load_yaml(path), path)


def load_all_hosts(hosts_dir: Path) -> dict[str, Host]:
    hosts: dict[str, Host] = {}
    for f in sorted(hosts_dir.glob("*.yaml")):
        h = load_host(f)
        hosts[h.name] = h
    return hosts


def detect_local_host(hosts_dir: Path) -> Host:
    """Read /etc/os-release and find matching host config."""
    os_release: dict[str, str] = {}
    os_release_path = Path("/etc/os-release")
    try:
        with os_release_path.open() as f:
            for line in f:
                if "=" in line:
                    key, _, value = line.strip().partition("=")
                    os_release[key] = value.strip('"')
    except FileNotFoundError:
        pass

    os_id = os_release.get("ID", "")
    version_id = os_release.get("VERSION_ID", "")

    hosts = load_all_hosts(hosts_dir)
    matches = [
        h for h in hosts.values()
        if h.detect.os == os_id and h.detect.version == version_id
    ]

    if len(matches) == 1:
        return matches[0]
    if not matches:
        available = ", ".join(sorted(hosts.keys()))
        raise ConfigError(
            f"No host matches /etc/os-release (ID={os_id}, VERSION_ID={version_id}). "
            f"Available hosts: {available}. "
            "Either create a matching host YAML or specify --host explicitly."
        )
    raise ConfigError(
        f"Multiple hosts match /etc/os-release (ID={os_id}, VERSION_ID={version_id}). "
        "This is a configuration bug; host detections must be unique."
    )
