from conductr_cli import validation, sandbox_common, sandbox_features, \
    sandbox_run_docker, sandbox_run_jvm
from conductr_cli.constants import DEFAULT_CLI_TMP_DIR
from conductr_cli.sandbox_common import LATEST_SANDBOX_RUN_ARGS_FILE
from conductr_cli.sandbox_version import is_sandbox_docker_based

import os
import sys


@validation.handle_connection_error
@validation.handle_http_error
@validation.handle_instance_count_error
@validation.handle_bind_address_not_found
@validation.handle_sandbox_image_fetch_error
@validation.handle_sandbox_image_not_found_error
@validation.handle_sandbox_image_not_available_offline_error
@validation.handle_sandbox_unsupported_os_error
@validation.handle_sandbox_unsupported_os_arch_error
@validation.handle_bintray_resolution_error
@validation.handle_bintray_credentials_error
@validation.handle_bintray_unreachable_error
@validation.handle_jvm_validation_error
@validation.handle_hostname_lookup_error
@validation.handle_docker_validation_error
@validation.handle_conductr_startup_error
def run(args):
    """`sandbox run` command"""
    write_run_command()
    features = sandbox_features.collect_features(args.features, args.no_default_features, args.image_version, args.offline_mode)
    sandbox = sandbox_run_docker if is_sandbox_docker_based(args.image_version) else sandbox_run_jvm

    run_result = sandbox.run(args, features)

    if run_result.wait_for_conductr:
        sandbox_common.wait_for_start(run_result)

    feature_results = []
    feature_provided = []

    for feature in features:
        feature.conductr_post_start(args, run_result)
        result = feature.start()
        feature_results += result.bundle_results

        if result.started:
            for provided in feature.provides:
                feature_provided.append(provided)

    sandbox.log_run_attempt(args, run_result, feature_results, feature_provided)

    return True


def write_run_command():
    # Only save the command if it is an actual 'sandbox run' command and not a 'sandbox restart' command
    if len(sys.argv) > 1 and sys.argv[1] == 'run':
        os.makedirs(DEFAULT_CLI_TMP_DIR, mode=0o700, exist_ok=True)
        with open(LATEST_SANDBOX_RUN_ARGS_FILE, mode='w') as f:
            f.write(' '.join(sys.argv[2:]))
