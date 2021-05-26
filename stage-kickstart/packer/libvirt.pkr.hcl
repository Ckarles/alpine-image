variable "output_dir" {
  type = string
}

variable "vm_name" {
  type    = string
  default = "alpine"
}

locals {
  project_root = abspath("${path.root}/../..")
}

source "qemu" "alpine" {
  iso_url             = "https://alpine.global.ssl.fastly.net/alpine/v3.13/releases/x86_64/alpine-virt-3.13.5-x86_64.iso"
  iso_checksum        = "file:https://alpine.global.ssl.fastly.net/alpine/v3.13/releases/x86_64/alpine-virt-3.13.5-x86_64.iso.sha512"
  ssh_username        = "root"
  ssh_password        = ""
  ssh_agent_auth      = true
  use_default_display = true
  output_directory    = "${var.output_dir}"
  vm_name             = "${var.vm_name}_libvirt.qcow2"
  boot_command = [
    "root<enter><wait>",
    "ifconfig eth0 up && udhcpc -i eth0<enter><wait>",
    "setup-apkrepos -1<enter><wait>",
    "apk add openssh openssh-sftp-server<enter><wait>",
    "cat <<- EOF >> /etc/ssh/sshd_config<enter>",
    "PermitRootLogin yes<enter>",
    "PermitEmptyPasswords yes<enter>",
    "EOF<enter>",
    "ln -s /usr/lib/ssh/sftp-server /usr/lib/sftp-server<enter>",
    "rc-service sshd start<enter>",
  ]
  shutdown_command = "poweroff"
}

build {
  sources = ["source.qemu.alpine"]
  provisioner "ansible" {
    playbook_file    = "${path.root}/../ansible/playbook.yml"
    ansible_env_vars = ["ANSIBLE_CONFIG=${local.project_root}/common/ansible/ansible.cfg"]
    user             = "root"
  }
}
