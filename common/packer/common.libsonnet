{
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
