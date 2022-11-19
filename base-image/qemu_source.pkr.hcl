source "qemu" "alpine" {
  #boot_command = split("\n", file("${path.root}/qemu_bootcmd"))
  boot_command = [file("qemu_bootcmd")]
  iso_url = "${local.alpine_iso}"
  iso_checksum = "file:${local.alpine_iso}.sha512"
  output_directory = "${local.dist_path}/base-image"
  shutdown_command = "poweroff"
  ssh_username = "root"
  use_default_display = true
  vm_name = "alpine_qemu.qcow2"
}
