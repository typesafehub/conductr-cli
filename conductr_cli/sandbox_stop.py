from conductr_cli import sandbox_common, terminal, validation


@validation.handle_docker_errors
def stop(args):
    """`sandbox stop` command"""

    running_containers = sandbox_common.resolve_running_docker_containers()
    if running_containers:
        print('Stopping ConductR..')
        terminal.docker_rm(running_containers)
