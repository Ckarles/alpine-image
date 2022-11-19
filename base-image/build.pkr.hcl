build {
  sources = [
    "source.qemu.alpine",
    "source.hcloud.alpine",
  ]

  provisioner "shell" {
    only = ["hcloud.alpine"]

    environment_vars = ["FETCH_URL=${local.alpine_tar}"]
    expect_disconnect = true
    script = "${path.root}/hcloud_kickstart.sh"
  }

  provisioner "ansible" {
    #ansible_env_vars = ["ANSIBLE_CONFIG=./ansible.cfg"]
    ansible_env_vars = ["HOST_KEY_CHECKING=false"]
    extra_arguments = [
      "--extra-vars",
      jsonencode({
        apk_repos = local.alpine_repos
        root_ssh_keypair_public = "${local.root_ssh_keypair.public}"
      })
    ]
    playbook_file = "${path.root}/ansible-playbook.yml"
    user = "root"
    use_proxy = false
  }

  post-processor "checksum" {
   only = ["qemu.alpine"]

   checksum_types = ["sha256"]
   output = "${local.dist_path}/base-image/{{.BuildName}}_{{.BuilderType}}.qcow2.{{.ChecksumType}}"
  }
}
