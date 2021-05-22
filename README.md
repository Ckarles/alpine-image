# alpine-base-image
![Version](https://img.shields.io/badge/version-0.1-blue.svg?cacheSeconds=2592000)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

> Generate Alpine linux base images using Packer and Ansible.

## Installation

### Requirements

- [ansible](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html) >= 2.11
- [packer](https://learn.hashicorp.com/tutorials/packer/get-started-install-cli) >= 1.7

```sh
# clone the project
git clone https://gitlab.com/Ckarles/alpine-base-image.git
```

## Running test

### Requirements

- [golang](https://golang.org/doc/install) >= 1.16

### Install dependencies

```sh
go mod download
```

### Run all tests
```sh
go test -timeout 30m ./...
```

### [Homepage](https://gitlab.com/Ckarles/alpine-base-image)

## Contributing

Contributions, issues and feature requests are welcome!

Feel free to check [issues page](https://gitlab.com/Ckarles/alpine-base-image/-/issues). 

## Show your support

Give a ⭐️ if this project helped you!
