local common = import 'common.libsonnet';
local libvirt = import 'libvirt.libsonnet';

local stage = 'vagrant';

{
  source: {
    qemu: {
      alpine: libvirt.source {
        iso_url: './build/dist/base/alpine_libvirt.qcow2',
        iso_checksum: 'none',
        disk_image: true,
        output_directory: './build/intermediates',
      },
    },
  },
  build: common.build(stage) + {
    'post-processor': {
      vagrant: {
        output: './build/dist/vagrant/alpine_{{.Provider}}.box',
        vagrantfile_template: './stage-vagrant/packer/Vagrantfile.tpl',
      },
    },
  },
}
