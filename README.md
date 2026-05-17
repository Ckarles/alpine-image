# alpine-image-builder
![Version](https://img.shields.io/badge/version-0.1.0-blue.svg?cacheSeconds=2592000)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

> Build Alpine Linux images for hetzner cloud and qemu using Packer.

## Installation

```bash
# clone the project
git clone https://gitlab.com/Ckarles/alpine-image-builder.git
cd alpine-image-builder

# Install Python dependencies (managed by uv)
uv sync
```

### Requirements

- [fedora 43](https://fedoraproject.org) _(build host; other distros supported via host configs)_
- [uv](https://docs.astral.sh/uv/)
- [packer](https://learn.hashicorp.com/tutorials/packer/get-started-install-cli) >= 1.7
- Python >= 3.13

## Usage

```bash
# List available recipes, hosts, platforms, and plugins
uv run alpine-image-builder list

# List versions for a recipe
uv run alpine-image-builder list --recipe alpine-image

# Build the base image
uv run alpine-image-builder build alpine-image --version 3.20 --ssh-key ~/.ssh/infra-root_ed25519

# Build with platform/arch filtering
uv run alpine-image-builder build alpine-image --version 3.20 --ssh-key ~/.ssh/infra-root_ed25519 --platform qemu --arch x86_64
```

### [Homepage](https://gitlab.com/Ckarles/alpine-image-builder)

## Contributing

Contributions, issues and feature requests are welcome!

Feel free to check [issues page](https://gitlab.com/Ckarles/alpine-image-builder/-/issues).

## Show your support

Give a ⭐️ if this project helped you!
