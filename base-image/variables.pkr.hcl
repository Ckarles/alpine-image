variable "alpine_version" {
  type = string
  description = "Alpine version to create an image of"
}

locals {
  # https://semver.org/
  semver_regex = "^(?P<major>0|[1-9]\\d*)\\.(?P<minor>0|[1-9]\\d*)\\.(?P<patch>0|[1-9]\\d*)(?:-(?P<prerelease>(?:0|[1-9]\\d*|\\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\\.(?:0|[1-9]\\d*|\\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\\.[0-9a-zA-Z-]+)*))?$"

  alpine_version_split = regex(local.semver_regex, var.alpine_version)
}

variable "alpine_mirror" {
  type = string
  description = "Alpine mirror to get the artifacts and configure the image from"
}

locals {
  alpine_branch = "v${local.alpine_version_split.major}.${local.alpine_version_split.minor}"
  alpine_baseurl = "https://${var.alpine_mirror}/alpine/${local.alpine_branch}"
  
  alpine_iso = "${local.alpine_baseurl}/releases/x86_64/alpine-virt-${var.alpine_version}-x86_64.iso"
  alpine_tar = "${local.alpine_baseurl}/releases/x86_64/alpine-minirootfs-${var.alpine_version}-x86_64.tar.gz"

  alpine_repos = [for repo in ["main", "community"] : "${local.alpine_baseurl}/${repo}"]
}

variable "debian_version" {
  type = string
  description = "Debian version"
}

variable "debian_mirror" {
  type = string
  description = "Debian mirror to download debian from"
}

locals {
  debian_iso = "https://${var.debian_mirror}/debian-cd/current/amd64/iso-cd/debian-${var.debian_version}-amd64-netinst.iso"
}

variable "root_ssh_key" {
  type = string
  description = "Path to the private key to push to the image root user. A compatible public key must also be present on the same dir."
  validation {
    condition     = fileexists("${var.root_ssh_key}")
    error_message = "The private key does not exists."
  }
  validation {
    condition     = fileexists("${var.root_ssh_key}.pub")
    error_message = "The public key does not exists."
  }
}

locals {
  root_ssh_keypair = {
    private = "${var.root_ssh_key}"
    public = "${var.root_ssh_key}.pub"
  }
}

locals {
  dist_path = "${path.root}/../dist"
}
