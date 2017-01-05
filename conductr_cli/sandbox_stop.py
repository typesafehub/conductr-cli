from conductr_cli import sandbox_stop_docker


def stop(args):
    """`sandbox stop` command"""

    sandbox_stop_docker.stop(args)
    return True
