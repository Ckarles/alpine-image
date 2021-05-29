local common = import 'common.libsonnet';
local libvirt = import 'libvirt.libsonnet';

local stage = 'base';

{
  source: {
    qemu: {
      alpine: libvirt.source {
        iso_url: 'https://alpine.global.ssl.fastly.net/alpine/v3.13/releases/x86_64/alpine-virt-3.13.5-x86_64.iso',
        iso_checksum: 'file:https://alpine.global.ssl.fastly.net/alpine/v3.13/releases/x86_64/alpine-virt-3.13.5-x86_64.iso.sha512',
        output_directory: './build/dist/base',
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
  build: common.build(stage),
}
