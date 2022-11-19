locals {
  source_image_filename = "alpine_qemu.qcow2"
  source_image_path = "${local.dist_path}/base-image/${local.source_image_filename}"
}

source "qemu" "alpine" {
  disk_image = true
  iso_checksum = "file:${local.source_image_path}.sha256"
  iso_url = "${local.source_image_path}"
  output_directory = "build/intermediates"
  shutdown_command = "poweroff"
  ssh_agent_auth = false
  ssh_private_key_file = "${local.root_ssh_keypair.private}"
  ssh_username = "root"
  use_default_display = true
  vm_name = "${local.source_image_filename}"
}
