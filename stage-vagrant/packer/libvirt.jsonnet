{
  source: {
    qemu: {
      alpine: {
        iso_url: './build/dist/base/alpine_libvirt.qcow2',
        iso_checksum: 'none',
        ssh_username: 'root',
        ssh_agent_auth: true,
        use_default_display: true,
        output_directory: './build/intermediates',
        vm_name: 'alpine_libvirt.qcow2',
        disk_image: true,
        shutdown_command: 'poweroff',
      },
    },
  },
  build: {
    sources: ['source.qemu.alpine'],
    provisioner: {
      ansible: {
        playbook_file: './stage-vagrant/ansible/playbook.yml',
        ansible_env_vars: ['ANSIBLE_CONFIG=./common/ansible/ansible.cfg'],
        user: 'root',
      },
    },
    'post-processor': {
      vagrant: {
        output: './build/dist/vagrant/alpine_libvirt.box',
        vagrantfile_template: './stage-vagrant/packer/Vagrantfile.tpl',
      },
    },
  },
}
