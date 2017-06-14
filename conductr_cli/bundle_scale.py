from __future__ import unicode_literals
from conductr_cli import conduct_events, conduct_logs, conduct_request, conduct_url, sse_client
from conductr_cli.exceptions import BundleScaleError, WaitTimeoutError
from datetime import datetime
from requests import HTTPError
import json
import logging


IGNORE_ERROR_FIRST_SECONDS = 10  # The number of seconds where bundle error will be ignored


def get_scale(bundle_id, wait_for_is_active, args):
    bundles_url = conduct_url.url('bundles', args)
    response = conduct_request.get(args.dcos_mode, conduct_url.conductr_host(args), bundles_url,
                                   auth=args.conductr_auth, verify=args.server_verification_file)
    response.raise_for_status()
    bundles = json.loads(response.text)
    matching_bundles = [bundle for bundle in bundles if bundle['bundleId'] == bundle_id]
    if matching_bundles:
        matching_bundle = matching_bundles[0]
        has_error = matching_bundle['hasError']
        if 'bundleExecutions' in matching_bundle:
            started_executions = [bundle_execution
                                  for bundle_execution in matching_bundle['bundleExecutions']
                                  if not wait_for_is_active or bundle_execution['isStarted']]
            return len(started_executions), has_error

    return 0, False


def wait_for_scale(bundle_id, expected_scale, wait_for_is_active, args):
    log = logging.getLogger(__name__)
    start_time = datetime.now()

    (bundle_scale, has_error) = get_scale(bundle_id, wait_for_is_active, args)
    # Ignore initial error to wait for the bundle to start and correct itself.
    if bundle_scale == expected_scale:
        log.info('Bundle {} expected scale {} is met'.format(bundle_id, expected_scale))
        return
    else:
        sse_heartbeat_count_after_event = 0

        log.info('Bundle {} waiting to reach expected scale {}'.format(bundle_id, expected_scale))
        bundle_events_url = conduct_url.url('bundles/events', args)
        sse_events = sse_client.get_events(args.dcos_mode, conduct_url.conductr_host(args), bundle_events_url,
                                           auth=args.conductr_auth, verify=args.server_verification_file)
        last_scale = -1
        last_log_message = None
        for event in sse_events:
            sse_heartbeat_count_after_event += 1

            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > args.wait_timeout:
                raise WaitTimeoutError('Bundle {} waiting to reach expected scale {}'.format(bundle_id, expected_scale))

            # Check for bundle scale every 3 heartbeats from the last received event.
            if event.event or (sse_heartbeat_count_after_event % 3 == 0):
                if event.event:
                    sse_heartbeat_count_after_event = 0

                (bundle_scale, has_error) = get_scale(bundle_id, wait_for_is_active, args)

                # Ignore error as long as the time elapsed is below threshold specified by IGNORE_ERROR_FIRST_SECONDS.
                # This is done to allow the CLI to wait for the bundle to start and correct its error.
                ignore_error = elapsed <= IGNORE_ERROR_FIRST_SECONDS

                if has_error and not ignore_error:
                    # Reprint previous message with flush to go to next line
                    if last_log_message:
                        log.progress(last_log_message, flush=True)

                    display_bundle_scale_error_message(bundle_id, args)

                    raise BundleScaleError(bundle_id)
                elif bundle_scale == expected_scale:
                    # Reprint previous message with flush to go to next line
                    if last_log_message:
                        log.progress(last_log_message, flush=True)

                    log.info('Bundle {} expected scale {} is met'.format(bundle_id, expected_scale))
                    return
                else:
                    if bundle_scale > last_scale:
                        last_scale = bundle_scale

                        # Reprint previous message with flush to go to next line
                        if last_log_message:
                            log.progress(last_log_message, flush=True)

                        last_log_message = 'Bundle {} has scale {}, expected {}'.format(bundle_id, bundle_scale, expected_scale)
                        log.progress(last_log_message, flush=False)
                    else:
                        last_log_message = '{}.'.format(last_log_message)
                        log.progress(last_log_message, flush=False)

        raise WaitTimeoutError('Bundle {} waiting to reach expected scale {}'.format(bundle_id, expected_scale))


def display_bundle_scale_error_message(bundle_id, args):
    log = logging.getLogger(__name__)

    log.error('Failure to scale bundle {}'.format(bundle_id))

    if is_consolidated_logging_enabled(args):
        log.info('')
        # Trying to call events and logs using `conduct_main.run()` causes some problem with declaring validation
        # handlers (i.e. @validation.handle_bndl_create_error) raised within unit test.
        log.info('Check latest bundle events with:')
        log.info('  conduct events {}'.format(bundle_id))
        log.info('Current bundle events:')
        conduct_events.events(args)
        log.info('')

        log.info('Check latest bundle logs with:')
        log.info('  conduct logs {}'.format(bundle_id))
        log.info('Current bundle logs:')
        conduct_logs.logs(args)
        log.info('')

        log.error('Bundle {} has error'.format(bundle_id))
        log.info('')
        log.info('Inspect the latest bundle events and logs using:')
        log.info('  conduct events {}'.format(bundle_id))
        log.info('  conduct logs {}'.format(bundle_id))
    else:
        log.error('Bundle {} has error'.format(bundle_id))
        log.warning('Please enable consolidated logging to view bundle events and logs')
        log.info('Once enabled, inspect the latest bundle events and logs using:')
        log.info('  conduct events {}'.format(bundle_id))
        log.info('  conduct logs {}'.format(bundle_id))


def is_consolidated_logging_enabled(args):
    try:
        conduct_events.get_bundle_events(args, count=1)
        return True
    except HTTPError as e:
        if e.response.status_code == 503:
            return False
        else:
            raise e
