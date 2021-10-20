local common = import 'common.libsonnet';

{
  sourcePath: ['source.hcloud.alpine'],
  source(version):: {
    hcloud: {
      alpine: {
        ssh_username: 'root',
        image: 'debian-11',
        location: 'fsn1',
        server_type: 'cx11',
        ssh_keys: ['infra-root'],
        rescue: 'linux64',
        snapshot_name: 'alpine-' + version + '_{{timestamp}}',
        snapshot_labels: {
          distribution: 'alpine',
          version: version,
        },
      },
    },
  },
  preInstallProvisioner(fetchURL):: [{
    shell: {
      only: common.sourceSplit($.sourcePath, start=1),
      expect_disconnect: true,
      script: 'stage-base/hetzner/kickstart.sh',
      environment_vars: ['FETCH_URL=' + fetchURL],
    },
  }],
}
