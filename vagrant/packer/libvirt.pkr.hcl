variable "input_dir" {
  type = string
}

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
  iso_url             = "${var.input_dir}/${var.vm_name}_libvirt.qcow2"
  iso_checksum        = "none"
  ssh_username        = "root"
  ssh_agent_auth      = true
  use_default_display = true
  output_directory    = "${var.output_dir}/raw"
  vm_name             = "${var.vm_name}_libvirt.qcow2"
  disk_image          = true
  shutdown_command    = "poweroff"
}

build {
  sources = ["source.qemu.alpine"]

  provisioner "ansible" {
    playbook_file    = "${path.root}/../ansible/playbook.yml"
    ansible_env_vars = ["ANSIBLE_CONFIG=${local.project_root}/common/ansible/ansible.cfg"]
    user             = "root"
  }

  post-processor "vagrant" {
    output               = "${var.output_dir}/${var.vm_name}_{{.Provider}}.box"
    vagrantfile_template = "${path.root}/Vagrantfile.tpl"
  }
}
