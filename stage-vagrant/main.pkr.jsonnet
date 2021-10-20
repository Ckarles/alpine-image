local common = import 'common.libsonnet';

local commonLibvirt = import 'common-libvirt.libsonnet';

{
  source: {
    qemu: {
      alpine: commonLibvirt.source + {
        iso_url: commonLibvirt.distDir + '/base/alpine_qemu.qcow2',
        iso_checksum: 'file:' + self.iso_url + '.sha512',
        disk_image: true,
        output_directory: 'build/intermediates',
      },
    },
  },
  build: {
    sources: commonLibvirt.sourcePath,
    provisioner: common.installProvisioner,
    }
  {
    'post-processor': {
      vagrant: {
        output: commonLibvirt.distDir + '/vagrant/alpine_{{.Provider}}.box',
        vagrantfile_template: 'stage-vagrant/Vagrantfile.tpl',
      },
    },
  },
}
