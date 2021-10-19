#local common = import 'common.libsonnet';
local commonLibvirt = import 'common-libvirt.libsonnet';

{
  source(iso_url):: {
    qemu: {
      alpine: commonLibvirt.source {
        iso_url: iso_url,
        iso_checksum: 'file:' + iso_url + '.sha512',
        output_directory: commonLibvirt.distDir + '/base',
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
  build: commonLibvirt.build('base') + {
    'post-processor': {
      checksum: {
        checksum_types: ['sha512'],
        output: commonLibvirt.distDir + '/base/{{.BuildName}}_{{.BuilderType}}.qcow2.{{.ChecksumType}}',
      },
    },
  },
}
