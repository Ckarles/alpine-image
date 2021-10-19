local commonLibvirt = import 'common-libvirt.libsonnet';
//local common = import 'common.libsonnet';

local stage = 'vagrant';

{
  source: {
    qemu: {
      alpine: commonLibvirt.source {
        iso_url: commonLibvirt.distDir + '/base/alpine_qemu.qcow2',
        iso_checksum: 'file:' + self.iso_url + '.sha512',
        disk_image: true,
        output_directory: 'build/intermediates',
      },
    },
  },
  build: commonLibvirt.build(stage) + {
    'post-processor': {
      vagrant: {
        output: commonLibvirt.distDir + '/vagrant/alpine_{{.Provider}}.box',
        vagrantfile_template: 'stage-vagrant/packer/Vagrantfile.tpl',
      },
    },
  },
}
