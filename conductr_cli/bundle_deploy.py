from conductr_cli import bundle_utils, conduct_request, conduct_url, sse_client
from conductr_cli.exceptions import ContinuousDeliveryError, WaitTimeoutError
from datetime import datetime

import hmac
import json
import logging
import base64

STRING_ENCODING = 'UTF-8'
HMAC_DIGEST_MOD = 'SHA256'


def generate_hmac_signature(secret_key, text):
    secret_key_bytes = bytes(secret_key, encoding=STRING_ENCODING)
    text_bytes = bytes(text, encoding=STRING_ENCODING)
    hmac_generator = hmac.new(secret_key_bytes, msg=text_bytes, digestmod=HMAC_DIGEST_MOD)
    signature = hmac_generator.digest()
    return base64.b64encode(signature).decode(STRING_ENCODING)


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


def wait_for_deployment_complete(deployment_id, resolved_version, args):
    log = logging.getLogger(__name__)
    start_time = datetime.now()

    def display_bundle_id(bundle_id):
        return bundle_id if args.long_ids else bundle_utils.short_id(bundle_id)

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
            compatible_bundle_id = display_bundle_id(deployment_event['compatibleBundleId'])
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

    package_name = resolved_version['package_name']
    compatibility_version = resolved_version['compatibility_version']
    bundle_id = display_bundle_id(resolved_version['digest'])
    bundle_shorthand = '{}:{}-{}'.format(package_name, compatibility_version, bundle_id)

    log.info('Deploying {}'.format(bundle_shorthand))

    deployment_events = get_deployment_events(deployment_id, args)

    if deployment_events and is_completed_with_success(deployment_events):
        log.info(log_message(deployment_events))
        return
    elif deployment_events and is_completed_with_failure(deployment_events):
        raise ContinuousDeliveryError('Unable to deploy {} - {}'.format(bundle_shorthand,
                                                                        log_message(deployment_events)))
    else:
        sse_heartbeat_count_after_event = 0

        deployment_events_url = conduct_url.url('deployments/events', args)
        sse_events = sse_client.get_events(args.dcos_mode, conduct_url.conductr_host(args), deployment_events_url,
                                           auth=args.conductr_auth, verify=args.server_verification_file)
        last_events = None
        last_log_message = None
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
                    if last_log_message:
                        log.progress(last_log_message, flush=True)

                    log.info(log_message(deployment_events))
                    return

                elif is_completed_with_failure(deployment_events):
                    # Reprint previous message with flush to go to next line
                    if last_log_message:
                        log.progress(last_log_message, flush=True)

                    raise ContinuousDeliveryError('Unable to deploy {} - {}'.format(bundle_shorthand,
                                                                                    log_message(deployment_events)))
                else:
                    if deployment_events != last_events:
                        last_events = deployment_events

                        # Reprint previous message with flush to go to next line
                        if last_log_message:
                            log.progress(last_log_message, flush=True)

                        last_log_message = log_message(deployment_events)
                        log.progress(last_log_message, flush=False)
                    else:
                        last_log_message = '{}.'.format(last_log_message)
                        log.progress(last_log_message, flush=False)

        raise WaitTimeoutError('Deployment for {} is still waiting to be completed')
