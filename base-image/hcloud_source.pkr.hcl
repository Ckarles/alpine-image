source "hcloud" "alpine" {
  image = "debian-11"
  location = "fsn1"
  rescue = "linux64"
  server_type = "cx11"
  snapshot_labels = {
    distribution = "alpine"
    version = "${var.alpine_version}"
  }
  snapshot_name = "alpine-${var.alpine_version}"
  ssh_username = "root"
}
