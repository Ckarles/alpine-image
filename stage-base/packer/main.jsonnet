local hetzner = import 'hetzner.libsonnet';
local libvirt = import 'libvirt.libsonnet';
local semver = import 'semver.libsonnet';

local semV = semver('3.13.5');
local mirror = 'alpine.global.ssl.fastly.net';

local branch = 'v' + semV.majorMinor;
local version = semV.canonical;
local iso_url = 'https://' + mirror + '/alpine/' + branch + '/releases/x86_64/alpine-virt-' + version + '-x86_64.iso';

{
  //source: libvirt.source(iso_url) + {
  source: {
    hcloud: {
      alpine: {
        ssh_username: 'root',
        image: 'debian-11',
        location: 'fsn1',
        server_type: 'cx11',
        user_data_file: 'stage-base/packer/user_data',
        ssh_keys: ['infra-root'],
        rescue: 'linux64',
      },
    },
  },
  build: {
    sources: ['source.hcloud.alpine'],
    provisioner: [{
      shell: {
        expect_disconnect: true,
        script: 'stage-base/packer/user_data',
      }
    }, {
      ansible: {
        playbook_file: 'stage-base/ansible/playbook.yml',
        ansible_env_vars: ['ANSIBLE_CONFIG=common/ansible/ansible.cfg''],
        user: 'root',
    },
  }]
}
  //build: libvirt.build,
}
