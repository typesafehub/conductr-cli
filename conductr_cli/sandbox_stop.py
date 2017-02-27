from conductr_cli import sandbox_features, sandbox_stop_docker, sandbox_stop_jvm


def feature():
    return sandbox_features.feature_classes


def stop(args):
    """`sandbox stop` command"""

    is_feature_success = sandbox_features.stop_features()
    is_docker_success = sandbox_stop_docker.stop(args)
    is_jvm_success = sandbox_stop_jvm.stop(args)

    return is_feature_success and is_docker_success and is_jvm_success
