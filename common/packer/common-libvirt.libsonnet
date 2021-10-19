{
  source: {
    ssh_username: 'root',
    ssh_agent_auth: true,
    vm_name: 'alpine_qemu.qcow2',
    use_default_display: true,
    shutdown_command: 'poweroff',
  },
  distDir: 'build/dist',
  build(stage)::
    {
      sources: ['source.qemu.alpine'],
      provisioner: {
        ansible: {
          playbook_file: 'stage-' + stage + '/ansible/playbook.yml',
          ansible_env_vars: ['ANSIBLE_CONFIG=common/ansible/ansible.cfg'],
          user: 'root',
        },
      },
    },
}
