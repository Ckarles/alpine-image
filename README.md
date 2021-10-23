# alpine-base-image
![Version](https://img.shields.io/badge/version-1.0-blue.svg?cacheSeconds=2592000)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

> Generate Alpine linux base images using Packer and Ansible.

## Installation

### Requirements

- [ansible](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html) >= 2.11
- [packer](https://learn.hashicorp.com/tutorials/packer/get-started-install-cli) >= 1.7
- [task](https://taskfile.dev/#/installation)
- [jsonnet](https://jsonnet.org)
- [vagrant](https://www.vagrantup.com/downloads)
- [vagrant-libvirt](https://github.com/vagrant-libvirt/vagrant-libvirt)

```sh
# clone the project
git clone https://gitlab.com/Ckarles/alpine-base-image.git


# setup env variables in .env
cat <<- EOF >> .env
  # path of ssh private key
  SSH_KEY_PRIVATE_PATH=~/.ssh/<private-key>
  # Hezner TOKEN if using hcloud
  HCLOUD_TOKEN=<your token>
EOF
```

## Usage

```sh
# list available tasks
task -l

# build images
#   use -f to force a rebuild (e.g. in care .env config is changed)
#   add CLOUD=target to build only for one cloud (e.g. hcloud)
task build

# start and ssh to vagrant image
vagrant up
vagrant ssh
```


### [Homepage](https://gitlab.com/Ckarles/alpine-base-image)

## Contributing

Contributions, issues and feature requests are welcome!

Feel free to check [issues page](https://gitlab.com/Ckarles/alpine-base-image/-/issues).

### Dev requirements

- [yamllint](https://yamllint.readthedocs.io/en/stable/quickstart.html)

## Show your support

Give a ⭐️ if this project helped you!
