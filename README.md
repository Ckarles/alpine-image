# alpine-base-image
![Version](https://img.shields.io/badge/version-0.4-blue.svg?cacheSeconds=2592000)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

> Generate Alpine linux base images using Packer and Ansible.

## Installation

### Requirements

- [ansible](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html) >= 2.11
- [packer](https://learn.hashicorp.com/tutorials/packer/get-started-install-cli) >= 1.7
- [task](https://taskfile.dev/#/installation)
- [jsonnet](https://jsonnet.org)

```sh
# clone the project
git clone https://gitlab.com/Ckarles/alpine-base-image.git
```

## Usage

```sh
# list available tasks
task -l

# build images (use -f to force a rebuild)
# ensure that the root key is added in ssh-agent
task build
```


### [Homepage](https://gitlab.com/Ckarles/alpine-base-image)

## Contributing

Contributions, issues and feature requests are welcome!

Feel free to check [issues page](https://gitlab.com/Ckarles/alpine-base-image/-/issues).

### Dev requirements

- [yamllint](https://yamllint.readthedocs.io/en/stable/quickstart.html)

## Show your support

Give a ⭐️ if this project helped you!
