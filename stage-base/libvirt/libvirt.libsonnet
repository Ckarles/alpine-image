local semver = import 'semver.libsonnet';

local baseCommon = import 'base-common.libsonnet';

local commonLibvirt = import 'common-libvirt.libsonnet';

{
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
      only: baseCommon.sourceSplit(commonLibvirt.sourcePath, start=1),
      checksum_types: ['sha512'],
      output: commonLibvirt.distDir + '/base/{{.BuildName}}_{{.BuilderType}}.qcow2.{{.ChecksumType}}',
    },
  },
}
