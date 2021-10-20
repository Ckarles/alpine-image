local semver = import 'semver.libsonnet';

{
  installProvisioner: [{
    ansible: {
      playbook_file: 'stage-base/ansible-playbook.yml',
      ansible_env_vars: ['ANSIBLE_CONFIG=common/ansible.cfg'],
      user: 'root',
    },
  }],

  sourceSplit(src, start=0, end=3)::
    [std.join('.', std.split(src[0], '.')[start:end])],

  fetchURL(inputV, mirror):: {
    local semV = semver(inputV),
    local version = semV.canonical,
    local branch = 'v' + semV.majorMinor,

    local joinURL = function(filename)
      'https://' + mirror + '/alpine/' + branch + '/releases/x86_64/' + filename,

    iso: joinURL('alpine-virt-' + version + '-x86_64.iso'),
    rootFS: joinURL('alpine-minirootfs-' + version + '-x86_64.tar.gz'),
  },
}
