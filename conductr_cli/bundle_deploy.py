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


def get_deployment_state(deployment_id, args):
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

    def is_completed_with_success(deployment_state):
        return deployment_state['eventType'] == "deploymentSuccess"

    def is_completed_with_failure(deployment_state):
        return deployment_state['eventType'] == "deploymentFailure"

    def log_message(deployment_state):
        event_type = deployment_state['eventType']
        if event_type == 'deploymentStarted':
            return 'Deployment started'

        elif event_type == 'bundleDownload':
            return 'Downloading bundle'

        elif event_type == 'configDownload':
            compatible_bundle_id = display_bundle_id(deployment_state['compatibleBundleId'])
            return 'Downloading config from bundle {}'.format(compatible_bundle_id)

        elif event_type == 'load':
            return 'Loading bundle with config' if 'configFileName' in deployment_state else 'Loading bundle'

        elif event_type == 'deploy':
            bundle_old = deployment_state['bundleOld']
            bundle_new = deployment_state['bundleNew']
            deploy_progress = 'Deploying - {} old instance vs {} new instance'.format(bundle_old['scale'],
                                                                                      bundle_new['scale'])
            return deploy_progress

        elif event_type == 'deploymentSuccess':
            return 'Success'

        elif event_type == 'deploymentFailure':
            return 'Failure: {}'.format(deployment_state['failure'])

        else:
            return 'Unknown deployment state {}'.format(deployment_state)

    package_name = resolved_version['package_name']
    compatibility_version = resolved_version['compatibility_version']
    bundle_id = display_bundle_id(resolved_version['digest'])
    bundle_shorthand = '{}:{}-{}'.format(package_name, compatibility_version, bundle_id)

    log.info('Deploying {}'.format(bundle_shorthand))

    deployment_state = get_deployment_state(deployment_id, args)

    if deployment_state and is_completed_with_success(deployment_state):
        log.info(log_message(deployment_state))
        return
    elif deployment_state and is_completed_with_failure(deployment_state):
        raise ContinuousDeliveryError('Unable to deploy {} - {}'.format(bundle_shorthand,
                                                                        log_message(deployment_state)))
    else:
        sse_heartbeat_count_after_event = 0

        deployment_events_url = conduct_url.url('deployments/events', args)
        sse_events = sse_client.get_events(args.dcos_mode, conduct_url.conductr_host(args), deployment_events_url,
                                           auth=args.conductr_auth, verify=args.server_verification_file)
        last_deployment_state = None
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

                deployment_state = get_deployment_state(deployment_id, args)

                if is_completed_with_success(deployment_state):
                    # Reprint previous message with flush to go to next line
                    if last_log_message:
                        log.progress(last_log_message, flush=True)

                    log.info(log_message(deployment_state))
                    return

                elif is_completed_with_failure(deployment_state):
                    # Reprint previous message with flush to go to next line
                    if last_log_message:
                        log.progress(last_log_message, flush=True)

                    raise ContinuousDeliveryError('Unable to deploy {} - {}'.format(bundle_shorthand,
                                                                                    log_message(deployment_state)))
                else:
                    if deployment_state != last_deployment_state:
                        last_deployment_state = deployment_state

                        # Reprint previous message with flush to go to next line
                        if last_log_message:
                            log.progress(last_log_message, flush=True)

                        last_log_message = log_message(deployment_state)
                        log.progress(last_log_message, flush=False)
                    else:
                        last_log_message = '{}.'.format(last_log_message)
                        log.progress(last_log_message, flush=False)

        raise WaitTimeoutError('Deployment for {} is still waiting to be completed')
