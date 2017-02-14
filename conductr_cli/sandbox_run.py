from conductr_cli import conduct_request, conduct_url, validation, sandbox_features, sandbox_proxy, \
    sandbox_run_docker, sandbox_run_jvm
from conductr_cli.constants import DEFAULT_CLI_TMP_DIR
from conductr_cli.http import DEFAULT_HTTP_TIMEOUT
from conductr_cli.sandbox_common import major_version, LATEST_SANDBOX_RUN_ARGS_FILE
from requests.exceptions import ConnectionError

import logging
import os
import time
import sys


# Will retry 30 times, every two seconds
DEFAULT_WAIT_RETRIES = 30
DEFAULT_WAIT_RETRY_INTERVAL = 2.0


@validation.handle_connection_error
@validation.handle_http_error
@validation.handle_instance_count_error
@validation.handle_bind_address_not_found
@validation.handle_sandbox_image_not_found_error
@validation.handle_sandbox_image_not_available_offline_error
@validation.handle_sandbox_unsupported_os_error
@validation.handle_sandbox_unsupported_os_arch_error
@validation.handle_bintray_credentials_error
@validation.handle_bintray_unreachable_error
@validation.handle_jvm_validation_error
@validation.handle_docker_validation_error
def run(args):
    """`sandbox run` command"""
    write_run_command()
    is_conductr_v1 = major_version(args.image_version) == 1
    features = sandbox_features.collect_features(args.features, args.image_version, args.offline_mode)
    sandbox = sandbox_run_docker if is_conductr_v1 else sandbox_run_jvm

    run_result = sandbox.run(args, features)

    is_conductr_started, wait_timeout = wait_for_start(args, run_result)

    feature_results = []
    print_proxy_output = False
    if is_conductr_started:
        if not is_conductr_v1:
            print_proxy_output = sandbox_proxy.start_proxy(proxy_bind_addr=run_result.core_addrs[0],
                                                           bundle_http_port=args.bundle_http_port,
                                                           proxy_ports=sorted(args.ports))

        for feature in features:
            result = feature.start()
            feature_results += result

    sandbox.log_run_attempt(args, run_result, feature_results, is_conductr_started, print_proxy_output, wait_timeout)

    return True


def wait_for_start(args, run_result):
    if not args.no_wait:
        retries = int(os.getenv('CONDUCTR_SANDBOX_WAIT_RETRIES', DEFAULT_WAIT_RETRIES))
        interval = float(os.getenv('CONDUCTR_SANDBOX_WAIT_RETRY_INTERVAL', DEFAULT_WAIT_RETRY_INTERVAL))
        return wait_for_conductr(args, run_result, 0, retries, interval), retries * interval
    else:
        return True, 0


def wait_for_conductr(args, run_result, current_retry, max_retries, interval):
    log = logging.getLogger(__name__)
    last_message = 'Waiting for ConductR to start'
    log.progress(last_message, flush=False)
    for attempt in range(0, max_retries):
        time.sleep(interval)

        last_message = '{}.'.format(last_message)
        log.progress(last_message, flush=False)

        url = conduct_url.url('members', run_result)
        try:
            conduct_request.get(dcos_mode=False, host=run_result.host, url=url, timeout=DEFAULT_HTTP_TIMEOUT)
            break
        except ConnectionError:
            current_retry += 1

    # Reprint previous message with flush to go to next line
    log.progress(last_message, flush=True)
    return True if current_retry < max_retries else False


def write_run_command():
    # Only save the command if it is an actual 'sandbox run' command and not a 'sandbox restart' command
    if len(sys.argv) > 1 and sys.argv[1] == 'run':
        os.makedirs(DEFAULT_CLI_TMP_DIR, mode=0o700, exist_ok=True)
        with open(LATEST_SANDBOX_RUN_ARGS_FILE, mode='w') as f:
            f.write(' '.join(sys.argv[2:]))
