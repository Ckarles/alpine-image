# alpine-base-image
![Version](https://img.shields.io/badge/version-2.0-blue.svg?cacheSeconds=2592000)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

> Build Alpine Linux for hetzner cloud, qemu and vagrant using Packer and Ansible.

## Installation

```bash
# clone the project
git clone https://gitlab.com/Ckarles/alpine-base-image.git
```

### Requirements

- [ansible](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html) >= 2.11
- [packer](https://learn.hashicorp.com/tutorials/packer/get-started-install-cli) >= 1.7
- [vagrant](https://www.vagrantup.com/downloads)
- [vagrant-libvirt](https://github.com/vagrant-libvirt/vagrant-libvirt)

## Usage

Build an Alpine Linux base image in hetzner cloud.
```bash
# Set packer variables
cat << EOF > params.pkrvars.hcl
alpine_version = "3.13.5"
alpine_mirror  = "alpine.global.ssl.fastly.net"
root_ssh_key   = "~/.ssh/infra-root_ed25519"
EOF

# Store hcloud secret token in a .env file
cat << EOF > .env
HCLOUD_TOKEN=<token>
EOF

# Build base image in hcloud
env $(cat .env | xargs)                       `# set token for this command` \
  packer build --var-file=params.pkrvars.hcl  `# input packer variables    ` \
  -only qemu.alpine base-image                `# build only for hcloud     `
```

Build the same image for qemu with an additional vagrant box.
```bash
# Build qemu image
packer build -only qemu.alpine --var-file=params.pkrvars.hcl base-image

# Build vagrant box from qemu image
packer build -only qemu.alpine --var-file=params.pkrvars.hcl base-image_vagrant
```

### [Homepage](https://gitlab.com/Ckarles/alpine-base-image)

## Contributing

Contributions, issues and feature requests are welcome!

Feel free to check [issues page](https://gitlab.com/Ckarles/alpine-base-image/-/issues).

## Show your support

Give a ⭐️ if this project helped you!
