# alpine-base-image
![Version](https://img.shields.io/badge/version-2.1-blue.svg?cacheSeconds=2592000)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

> Build Alpine Linux for hetzner cloud, qemu and vagrant using Packer and Ansible.

## Installation

```bash
# clone the project
git clone https://gitlab.com/Ckarles/alpine-base-image.git
```

### Requirements

- [mage](https://magefile.org)
- [ansible](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html) >= 2.11
- [packer](https://learn.hashicorp.com/tutorials/packer/get-started-install-cli) >= 1.7
- [vagrant](https://www.vagrantup.com/downloads)
- [vagrant-libvirt](https://github.com/vagrant-libvirt/vagrant-libvirt)

## Usage

Build an Alpine Linux base image for hetzner cloud, qemu, and vagrant, for arm64 and amd64.
```bash
HCLOUD_TOKEN=<token> mage build <path-to-private-ssh-key-to-use-for-root-account>
```

### [Homepage](https://gitlab.com/Ckarles/alpine-base-image)

## Contributing

Contributions, issues and feature requests are welcome!

Feel free to check [issues page](https://gitlab.com/Ckarles/alpine-base-image/-/issues).

## Show your support

Give a ⭐️ if this project helped you!
