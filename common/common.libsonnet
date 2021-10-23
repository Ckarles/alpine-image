{
  getInstallProvisioner(stage, sshKeyPublicPath=''):: [{
    ansible: {
      playbook_file: 'stage-' + stage + '/ansible-playbook.yml',
      ansible_env_vars: ['ANSIBLE_CONFIG=common/ansible.cfg'],
      extra_arguments: [
        '--extra-vars',
        "ssh_key_public='" + sshKeyPublicPath + "'",
      ],
      user: 'root',
    },
  }],
}
