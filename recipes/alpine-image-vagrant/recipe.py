"""Alpine image Vagrant repackaging recipe."""

from alpine_image_builder.recipe import Output, PerArchTemplate, Recipe, RequiredArtifact


class AlpineImageVagrant(Recipe):
    """Repackage Alpine QEMU images as Vagrant boxes."""
    name = "alpine-image-vagrant"
    platforms = ["qemu"]
    archs = ["aarch64", "x86_64"]
    plugins = ["qemu", "ansible", "vagrant"]
    url_patterns = {
        "branch": "v{major}.{minor}",
        "base":   "https://alpine.global.ssl.fastly.net/alpine/{branch}",
    }
    requires = (
        RequiredArtifact(
            recipe="alpine-image",
            path="dist/alpine-image_{arch}/alpine_{arch}.qcow2",
            message=(
                "Base image missing for arch {arch}. "
                "Run: alpine-image-builder build alpine-image "
                "--version <id> --ssh-key {ssh_key}"
            ),
        ),
    )
    pre_render = (
        PerArchTemplate(template="Vagrantfile.j2", output="Vagrantfile_{arch}.tpl"),
    )
    outputs = (
        Output(path="dist/intermediates/alpine-image-vagrant_{arch}"),
        Output(path="dist/alpine-image-vagrant_{arch}"),
    )
