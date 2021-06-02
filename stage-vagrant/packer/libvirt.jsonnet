local common = import 'common.libsonnet';
local libvirt = import 'libvirt.libsonnet';

local stage = 'vagrant';

{
  source: {
    qemu: {
      alpine: libvirt.source {
        iso_url: common.distDir + '/base/alpine_qemu.qcow2',
        iso_checksum: 'file:' + self.iso_url + '.sha512',
        disk_image: true,
        output_directory: 'build/intermediates',
      },
    },
  },
  build: common.build(stage) + {
    'post-processor': {
      vagrant: {
        output: common.distDir + '/vagrant/alpine_{{.Provider}}.box',
        vagrantfile_template: 'stage-vagrant/packer/Vagrantfile.tpl',
      },
    },
  },
}
