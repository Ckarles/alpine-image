{
  installProvisioner: [{
    ansible: {
      playbook_file: 'stage-base/ansible-playbook.yml',
      ansible_env_vars: ['ANSIBLE_CONFIG=common/ansible.cfg'],
      user: 'root',
    },
  }],
}
