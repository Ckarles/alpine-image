# alpine-base-image
![Version](https://img.shields.io/badge/version-2.1-blue.svg?cacheSeconds=2592000)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

> Build Alpine Linux for hetzner cloud, qemu and vagrant using Packer and Ansible.

## Installation

```bash
# clone the project
git clone https://gitlab.com/Ckarles/alpine-base-image.git

# Install packer dependencies
packer init alpine-image
```

### Requirements

- [fedora 43](https://fedoraproject.org) _(dependencies and local build pipeline is configured for fedora 43. Easy to adapt to other distros)_
- [mage](https://magefile.org)
- [ansible](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html) >= 2.11
- [packer](https://learn.hashicorp.com/tutorials/packer/get-started-install-cli) >= 1.7
- [vagrant](https://www.vagrantup.com/downloads)
- [vagrant-libvirt](https://github.com/vagrant-libvirt/vagrant-libvirt)

## Usage

Build an Alpine Linux base image for hetzner cloud, qemu, and vagrant, for arm64 and amd64.
```bash
HCLOUD_TOKEN=<token> mage build <path-to-private-ssh-key-to-use-for-root-account>

# or, if using a .env file
env $(cat .env | xargs) mage build ~/.ssh/infra-root_ed25519
```

### [Homepage](https://gitlab.com/Ckarles/alpine-base-image)

## Contributing

Contributions, issues and feature requests are welcome!

Feel free to check [issues page](https://gitlab.com/Ckarles/alpine-base-image/-/issues).

```
# Run with packer logs
env $(cat .env | xargs) PACKER_LOG=1 mage build ~/.ssh/infra-root_ed25519

# Run with packer step-by-step debug
env $(cat .env | xargs) PACKER_DEBUG=1 mage build ~/.ssh/infra-root_ed25519

# Run with ansible verbose level
env $(cat .env | xargs) ANSIBLE_VERBOSITY=2 mage build ~/.ssh/infra-root_ed25519
```

## TODO

- [ ] Ensure deps are installed before mage
- [ ] Provide documenation for using mage and get the target arguments etc.
- [ ] Clean previous version of params
- [ ] Use target.Path and target.Dir for auto cleanup from sources and destinations definition
- [ ] Add params for arch and target (hcloud / qemu)
- [ ] Abstractions to separate configurations from the HOST / BUILDER (fedora 39 -> 43, ansible upgrades, qemu versions..) and configuration from the GUEST (alpine version, python versions) etc.
  - Which version mapping is supported. Should host / builder be versioned (should it be the app version), should one version support multiple GUEST versions?
- [ ] Migration from magefile? If not, upgrade magefile.
- [ ] Thought: Is this a workflow? 1. generate config - 2. build the images.

## Show your support

Give a ⭐️ if this project helped you!
