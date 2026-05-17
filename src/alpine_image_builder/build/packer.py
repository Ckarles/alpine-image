"""Packer invocation subprocess."""

import subprocess
from pathlib import Path


def run_packer(
    project_root: Path,
    pkr_hcl_path: Path,
    ssh_key: str,
) -> int:
    """Invoke Packer build.

    Args:
        project_root: Project root (retained for API consistency; Packer runs
            from the generated file's parent directory).
        pkr_hcl_path: Absolute path to the generated .pkr.hcl file.
        ssh_key: Absolute path to SSH private key.

    Returns:
        Packer exit code.

    Raises:
        RuntimeError: If the Packer executable is not found in PATH.
    """
    cmd = [
        "packer", "build",
        "-var", f"root_ssh_key={ssh_key}",
        str(pkr_hcl_path),
    ]
    try:
        result = subprocess.run(cmd, cwd=pkr_hcl_path.parent, check=False)
    except FileNotFoundError as exc:
        raise RuntimeError("Packer executable not found in PATH") from exc
    return result.returncode
