from __future__ import unicode_literals
from conductr_cli import conduct_request, conduct_url, sse_client
from conductr_cli.exceptions import WaitTimeoutError
from datetime import datetime
import json
import logging


def count_installations(bundle_id, args):
    bundles_url = conduct_url.url('bundles', args)
    response = conduct_request.get(args.dcos_mode, conduct_url.conductr_host(args), bundles_url,
                                   auth=args.conductr_auth, verify=args.server_verification_file)
    response.raise_for_status()
    bundles = json.loads(response.text)
    matching_bundles = [bundle for bundle in bundles if bundle['bundleId'] == bundle_id]
    if matching_bundles:
        matching_bundle = matching_bundles[0]
        if 'bundleInstallations' in matching_bundle:
            return len(matching_bundle['bundleInstallations'])

    return 0


def wait_for_uninstallation(bundle_id, args):
    return wait_for_condition(bundle_id, is_uninstalled, 'uninstalled', args)


def wait_for_installation(bundle_id, args):
    return wait_for_condition(bundle_id, is_installed, 'installed', args)


def wait_for_condition(bundle_id, condition, condition_name, args):
    log = logging.getLogger(__name__)
    start_time = datetime.now()

    installed_bundles = count_installations(bundle_id, args)
    last_log_message = None
    if condition(installed_bundles):
        log.info('Bundle {} is {}'.format(bundle_id, condition_name))
        return
    else:
        sse_heartbeat_count_after_event = 0

        log.info('Bundle {} waiting to be {}'.format(bundle_id, condition_name))
        bundle_events_url = conduct_url.url('bundles/events', args)
        sse_events = sse_client.get_events(args.dcos_mode, conduct_url.conductr_host(args), bundle_events_url,
                                           auth=args.conductr_auth, verify=args.server_verification_file)
        for event in sse_events:
            sse_heartbeat_count_after_event += 1

            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > args.wait_timeout:
                raise WaitTimeoutError('Bundle {} waiting to be {}'.format(bundle_id, condition_name))

            # Check for installed bundles every 3 heartbeats from the last received event.
            if event.event or (sse_heartbeat_count_after_event % 3 == 0):
                if event.event:
                    sse_heartbeat_count_after_event = 0

                installed_bundles = count_installations(bundle_id, args)
                if condition(installed_bundles):
                    # Reprint previous message with flush to go to next line
                    if last_log_message:
                        log.progress(last_log_message, flush=True)

                    log.info('Bundle {} {}'.format(bundle_id, condition_name))
                    return
                else:
                    if last_log_message:
                        last_log_message = '{}.'.format(last_log_message)
                    else:
                        last_log_message = 'Bundle {} still waiting to be {}'.format(bundle_id, condition_name)

                    log.progress(last_log_message, flush=False)

        raise WaitTimeoutError('Bundle {} waiting to be {}'.format(bundle_id, condition_name))


def is_installed(number_of_installations):
    return number_of_installations > 0


def is_uninstalled(number_of_installations):
    return number_of_installations <= 0
