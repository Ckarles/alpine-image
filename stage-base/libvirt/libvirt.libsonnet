local semver = import 'semver.libsonnet';

local common = import 'common.libsonnet';

local commonLibvirt = import 'common-libvirt.libsonnet';

{
  sourcePath: ['source.qemu.alpine'],
  source(fetchURL):: {
    qemu: {
      alpine: commonLibvirt.source {
        iso_url: fetchURL,
        iso_checksum: 'file:' + fetchURL + '.sha512',
        output_directory: commonLibvirt.distDir + '/base',
        boot_command: std.split(importstr 'boot_command', '\n'),
      },
    },
  },
  postProcessor: {
    checksum: {
      only: common.sourceSplit($.sourcePath, start=1),
      checksum_types: ['sha512'],
      output: commonLibvirt.distDir + '/base/{{.BuildName}}_{{.BuilderType}}.qcow2.{{.ChecksumType}}',
    },
  },
}
