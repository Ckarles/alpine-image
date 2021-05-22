variable "output_dir" {
  type    = string
}

variable "vm_name" {
  type    = string
  default = "alpine"
}

source "qemu" "alpine" {
  iso_url             = "https://alpine.global.ssl.fastly.net/alpine/v3.13/releases/x86_64/alpine-virt-3.13.5-x86_64.iso"
  iso_checksum        = "file:https://alpine.global.ssl.fastly.net/alpine/v3.13/releases/x86_64/alpine-virt-3.13.5-x86_64.iso.sha512"
  ssh_username        = "root"
  ssh_password        = ""
  use_default_display = true
  output_directory    = "${var.output_dir}"
  vm_name             = "${var.vm_name}.qcow2"
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
}

build {
  sources = ["source.qemu.alpine"]
  post-processor "vagrant" {
    keep_input_artifact = true
    output              = "${var.output_dir}/${var.vm_name}_{{.Provider}}.box"
  }
}
