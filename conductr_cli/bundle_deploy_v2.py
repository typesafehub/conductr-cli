from conductr_cli import conduct_request, conduct_url, sse_client
from conductr_cli.bundle_deploy import display_bundle_id
from conductr_cli.exceptions import ContinuousDeliveryError, WaitTimeoutError
from datetime import datetime

import json
import logging


def get_deployment_events(deployment_id, args):
    deployment_state_url = conduct_url.url('deployments/{}'.format(deployment_id), args)
    response = conduct_request.get(args.dcos_mode, conduct_url.conductr_host(args), deployment_state_url,
                                   auth=args.conductr_auth, verify=args.server_verification_file)
    if response.status_code == 404:
        return None
    else:
        response.raise_for_status()
        deployment_state = json.loads(response.text)
        return deployment_state


def wait_for_deployment_complete(deployment_id, args):
    log = logging.getLogger(__name__)
    start_time = datetime.now()

    def is_completed_with_success(deployment_events):
        for event in deployment_events:
            if event['eventType'] == 'deploymentSuccess':
                return True

        return False

    def is_completed_with_failure(deployment_events):
        for event in deployment_events:
            if event['eventType'] == 'deploymentFailure':
                return True

        return False

    def display_deployment_event(deployment_event):
        event_type = deployment_event['eventType']
        if event_type == 'deploymentStarted':
            return 'Deployment started'

        elif event_type == 'bundleDownload':
            return 'Downloading bundle'

        elif event_type == 'configDownload':
            compatible_bundle_id = display_bundle_id(args, deployment_event['compatibleBundleId'])
            return 'Downloading config from bundle {}'.format(compatible_bundle_id)

        elif event_type == 'load':
            return 'Loading bundle with config' if 'configFileName' in deployment_event else 'Loading bundle'

        elif event_type == 'deploy':
            bundle_old = deployment_event['bundleOld']
            bundle_new = deployment_event['bundleNew']
            deploy_progress = 'Deploying - {} old instance vs {} new instance'.format(bundle_old['scale'],
                                                                                      bundle_new['scale'])
            return deploy_progress

        elif event_type == 'deploymentSuccess':
            return 'Success'

        elif event_type == 'deploymentFailure':
            return 'Failure: {}'.format(deployment_event['failure'])

        else:
            return 'Unknown deployment state {}'.format(deployment_event)

    def get_event_sequence(deployment_event):
        return deployment_event['deploymentSequence']

    def log_message(deployment_events):
        latest_event = sorted(deployment_events, key=get_event_sequence)[-1]
        return display_deployment_event(latest_event)

    log.info('Deployment id: {}'.format(deployment_id))

    deployment_events = get_deployment_events(deployment_id, args)

    if deployment_events and is_completed_with_success(deployment_events):
        log.info(log_message(deployment_events))
        return
    elif deployment_events and is_completed_with_failure(deployment_events):
        error_message = log_message(deployment_events)
        raise ContinuousDeliveryError(error_message)
    else:
        sse_heartbeat_count_after_event = 0

        deployment_events_url = conduct_url.url('deployments/events', args)
        sse_events = sse_client.get_events(args.dcos_mode, conduct_url.conductr_host(args), deployment_events_url,
                                           auth=args.conductr_auth, verify=args.server_verification_file)
        last_events = None
        for event in sse_events:
            sse_heartbeat_count_after_event += 1

            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > args.wait_timeout:
                raise WaitTimeoutError('Deployment is still waiting to be completed')

            # Check for deployment state every 3 heartbeats from the last received event.
            if event.event or (sse_heartbeat_count_after_event % 3 == 0):
                if event.event:
                    sse_heartbeat_count_after_event = 0

                deployment_events = get_deployment_events(deployment_id, args)

                if is_completed_with_success(deployment_events):
                    # Reprint previous message with flush to go to next line
                    log.progress(log_message(deployment_events),
                                 flush=True,
                                 next_line=(last_events is not None))
                    return

                elif is_completed_with_failure(deployment_events):
                    log.progress('\n', flush=False, line_end='')
                    error_message = log_message(deployment_events)
                    raise ContinuousDeliveryError(error_message)
                else:
                    if deployment_events != last_events:
                        log.progress(log_message(deployment_events),
                                     flush=False,
                                     line_end='',
                                     next_line=(last_events is not None))
                        last_events = deployment_events
                    else:
                        log.progress('.', flush=False, line_end='')

        raise WaitTimeoutError('Deployment for {} is still waiting to be completed')
