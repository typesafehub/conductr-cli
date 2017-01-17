from conductr_cli import sandbox_proxy, sandbox_stop_docker, sandbox_stop_jvm


def stop(args):
    """`sandbox stop` command"""
    is_proxy_success = sandbox_proxy.stop_proxy()
    is_docker_success = sandbox_stop_docker.stop(args)
    is_jvm_success = sandbox_stop_jvm.stop(args)
    return is_proxy_success and is_docker_success and is_jvm_success
