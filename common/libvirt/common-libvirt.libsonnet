{
  sourcePath: ['source.qemu.alpine'],
  source: {
    ssh_username: 'root',
    ssh_agent_auth: true,
    vm_name: 'alpine_qemu.qcow2',
    use_default_display: true,
    shutdown_command: 'poweroff',
  },
  distDir: 'build/dist',
}
