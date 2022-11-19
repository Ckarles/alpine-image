build {
  sources = ["source.qemu.alpine"]

  provisioner "ansible" {
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

  post-processors {
    post-processor "vagrant" {
      output = "${local.dist_path}/base-image_vagrant/{{.BuildName}}_${source.type}.box"
      vagrantfile_template = "${path.root}/Vagrantfile.tpl"
    }

    post-processor "checksum" {
     checksum_types = ["sha256"]
     output = "${local.dist_path}/base-image_vagrant/{{.BuildName}}_${source.type}.box.{{.ChecksumType}}"
    }
  }
}
