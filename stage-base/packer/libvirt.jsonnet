local common = import 'common.libsonnet';
local libvirt = import 'libvirt.libsonnet';

local stage = 'base';

local mirror = 'alpine.global.ssl.fastly.net';
local branch = 'v3.13';
local version = '3.13.5';

{
  source: {
    qemu: {
      alpine: libvirt.source {
        iso_url: 'https://' + mirror + '/alpine/' + branch + '/releases/x86_64/alpine-virt-' + version + '-x86_64.iso',
        iso_checksum: 'file:' + self.iso_url + '.sha512',
        output_directory: common.distDir + '/base',
        boot_command: [
          'root<enter><wait>',
          'ifconfig eth0 up && udhcpc -i eth0<enter><wait>',
          'setup-apkrepos -1<enter><wait>',
          'apk add openssh openssh-sftp-server<enter><wait>',
          'cat <<- EOF >> /etc/ssh/sshd_config<enter>',
          'PermitRootLogin yes<enter>',
          'PermitEmptyPasswords yes<enter>',
          'EOF<enter>',
          'ln -s /usr/lib/ssh/sftp-server /usr/lib/sftp-server<enter>',
          'rc-service sshd start<enter>',
        ],
      },
    },
  },
  build: common.build(stage) + {
    'post-processor': {
      checksum: {
        checksum_types: ['sha512'],
        output: common.distDir + '/base/{{.BuildName}}_{{.BuilderType}}.qcow2.{{.ChecksumType}}',
      },
    },
  },
}
