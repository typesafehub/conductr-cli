from conductr_cli import conduct_main, conduct_request, conduct_url, validation, sandbox_features, \
    sandbox_run_docker, sandbox_run_jvm
from conductr_cli.http import DEFAULT_HTTP_TIMEOUT
from conductr_cli.sandbox_common import major_version
from conductr_cli.screen_utils import headline
from requests.exceptions import ConnectionError

import logging
import os
import time


# Will retry 30 times, every two seconds
DEFAULT_WAIT_RETRIES = 30
DEFAULT_WAIT_RETRY_INTERVAL = 2.0


@validation.handle_connection_error
@validation.handle_http_error
@validation.handle_instance_count_error
@validation.handle_bind_address_not_found_error
@validation.handle_sandbox_image_not_found_error
@validation.handle_bintray_credentials_error
@validation.handle_bintray_unreachable_error
@validation.handle_jvm_validation_error
def run(args):
    """`sandbox run` command"""
    is_conductr_v1 = major_version(args.image_version) == 1
    features = sandbox_features.collect_features(args.features, args.image_version)

    if is_conductr_v1:
        run_result = sandbox_run_docker.run(args, features)
    else:
        run_result = sandbox_run_jvm.run(args, features)

    is_started, wait_timeout = wait_for_start(args, run_result)
    if is_started:
        if not is_conductr_v1:
            start_proxy(run_result.nr_of_proxy_instances)
        for feature in features:
            feature.start()

    if is_conductr_v1:
        sandbox_run_docker.log_run_attempt(args, run_result, is_started, wait_timeout)
    else:
        sandbox_run_jvm.log_run_attempt(args, run_result, is_started, wait_timeout)

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


def start_proxy(nr_of_instances):
    log = logging.getLogger(__name__)
    bundle_name = 'conductr-haproxy'
    configuration_name = 'conductr-haproxy-dev-mode'
    log.info(headline('Starting HAProxy'))
    log.info('Deploying bundle {} with configuration {}'.format(bundle_name, configuration_name))
    conduct_main.run(['load', bundle_name, configuration_name, '--disable-instructions'], configure_logging=False)
    conduct_main.run(['run', bundle_name, '--scale', str(nr_of_instances), '--disable-instructions'], configure_logging=False)
