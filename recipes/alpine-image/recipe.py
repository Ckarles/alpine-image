"""Alpine image recipe."""

from pydantic import BaseModel, ConfigDict

from alpine_image_builder.recipe import InputField, Output, Recipe


class Inputs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    mirror: str = InputField(
        "alpine.global.ssl.fastly.net",
        description="Mirror to download Alpine from",
        choices=["alpine.global.ssl.fastly.net"],
        cli_flag="--mirror",
    )


class AlpineImage(Recipe):
    """Build Alpine Linux QEMU and Hetzner Cloud images."""
    name = "alpine-image"
    platforms = ["qemu", "hcloud"]
    archs = ["aarch64", "x86_64"]
    plugins = ["qemu", "hcloud", "ansible"]
    Inputs = Inputs
    url_patterns = {
        "branch":   "v{major}.{minor}",
        "base":     "https://{mirror}/alpine/{branch}",
        "virt_iso": "{base}/releases/{arch}/alpine-virt-{version}-{arch}.iso",
        "rootfs":   "{base}/releases/{arch}/alpine-minirootfs-{version}-{arch}.tar.gz",
    }
    outputs = (
        Output(path="dist/alpine-image_{arch}"),
    )
