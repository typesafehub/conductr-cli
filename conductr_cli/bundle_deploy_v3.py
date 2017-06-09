from conductr_cli import conduct_url, conduct_request, sse_client
from conductr_cli.bundle_deploy import display_bundle_id
from conductr_cli.exceptions import ContinuousDeliveryError, WaitTimeoutError
from datetime import datetime
import json
import logging


def get_batch_events(deployment_batch_id, args):
    deployment_state_url = conduct_url.url('deployments/batches/{}'.format(deployment_batch_id), args)
    response = conduct_request.get(args.dcos_mode, conduct_url.conductr_host(args), deployment_state_url,
                                   auth=args.conductr_auth, verify=args.server_verification_file)
    if response.status_code == 404:
        return None
    else:
        response.raise_for_status()
        batch_events = json.loads(response.text)
        return batch_events


def get_deployment_events(deployment_batch_id, args):
    deployment_state_url = conduct_url.url('deployments/batches/{}/deployments'.format(deployment_batch_id), args)
    response = conduct_request.get(args.dcos_mode, conduct_url.conductr_host(args), deployment_state_url,
                                   auth=args.conductr_auth, verify=args.server_verification_file)
    if response.status_code == 404:
        return None
    else:
        response.raise_for_status()
        deployment_events = json.loads(response.text)
        return deployment_events


def wait_for_deployment_complete(deployment_batch_id, args):
    log = logging.getLogger(__name__)
    start_time = datetime.now()

    def is_batch_completed_with_failure(events):
        for event in events:
            if event['eventType'] == 'deploymentFailure':
                return True

        return False

    def get_batch_event_sequence(batch_event):
        return batch_event['deploymentBatchSequence']

    def log_message_batch(batch_events):
        latest_event = sorted(batch_events, key=get_batch_event_sequence)[-1]
        return display_batch_event(latest_event)

    def get_scheduled_lock_step_deployments(batch_events):
        if batch_events:
            return [
                scheduled_deployment
                for event in batch_events if event['eventType'] == 'scheduleLockStepDeployments'
                for scheduled_deployment in event['scheduledDeployments']
            ]
        else:
            return None

    def get_scheduled_simple_deployment(batch_events):
        if batch_events:
            return [event for event in batch_events if event['eventType'] == 'scheduleSimpleDeployment']
        else:
            return None

    def get_deployment_event_sequence(deployment_event):
        return deployment_event['deploymentSequence']

    def get_deployment_event_timestamp(deployment_event):
        return deployment_event['timestamp']

    def log_message_deployment(args, deployment_events):
        latest_events_to_display = [display_deploy_event(args, event) for event in deployment_events]
        return '\n'.join(latest_events_to_display)

    def find_latest_deployment_events(deployments):
        latest_events = []
        if deployments:
            for deployment in deployments:
                latest_event = sorted(deployment['events'], key=get_deployment_event_sequence)[-1]
                latest_events.append(latest_event)

            latest_events = sorted(latest_events, key=get_deployment_event_timestamp)
        return latest_events

    def find_deployment_events_to_display(events_new, events_existing):
        return [event for event in events_new if event not in events_existing]

    def is_completed(deployment_events):
        deployment_count = len(deployment_events)

        completed_count = 0
        all_successful = True
        for entry in deployment_events:
            for event in entry['events']:
                if event['eventType'] == 'deploymentSuccess':
                    completed_count += 1
                elif event['eventType'] == 'deploymentFailure':
                    completed_count += 1
                    all_successful = False

        return completed_count == deployment_count, all_successful

    def is_completed_with_success(deployment_events):
        all_completed, all_successful = is_completed(deployment_events)
        return all_completed and all_successful

    def has_deployment_failure(deployment_events):
        all_completed, all_successful = is_completed(deployment_events)
        return not all_successful

    log.info('Deployment batch id: {}'.format(deployment_batch_id))

    batch_events = get_batch_events(deployment_batch_id, args)
    if batch_events and is_batch_completed_with_failure(batch_events):
        error_message = log_message_batch(batch_events)
        raise ContinuousDeliveryError(error_message)
    else:
        latest_state = None
        scheduled_deployments = []
        wait_timeout = args.wait_timeout
        sse_heartbeat_count_after_event = 0

        deployment_events_url = conduct_url.url('deployments/events', args)
        sse_events = sse_client.get_events(args.dcos_mode, conduct_url.conductr_host(args), deployment_events_url,
                                           auth=args.conductr_auth, verify=args.server_verification_file)
        for event in sse_events:
            sse_heartbeat_count_after_event += 1

            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > wait_timeout:
                raise WaitTimeoutError('Deployment is still waiting to be completed')

            # Check for deployment state every 3 heartbeats from the last received event.
            if event.event or (sse_heartbeat_count_after_event % 3 == 0):
                if event.event:
                    sse_heartbeat_count_after_event = 0

                if not scheduled_deployments:
                    batch_events = get_batch_events(deployment_batch_id, args)
                    scheduled_lock_step_deployments = get_scheduled_lock_step_deployments(batch_events)
                    scheduled_simple_deployment = get_scheduled_simple_deployment(batch_events)

                    if scheduled_lock_step_deployments:
                        # Increase the wait timeout to match the number of deployments
                        wait_timeout = args.wait_timeout * len(scheduled_lock_step_deployments)

                        # Display the targeted bundles
                        log.progress('Targeting the following bundles',
                                     flush=True,
                                     next_line=(latest_state is not None))
                        for scheduled_lock_step_deployment in scheduled_lock_step_deployments:
                            target_bundle_id = display_bundle_id(args, scheduled_lock_step_deployment['targetBundleId'])
                            log.progress('  {}'.format(target_bundle_id), flush=True)

                        scheduled_deployments = scheduled_lock_step_deployments

                        # Reset the latest state for tracking deployment events
                        latest_state = None

                    elif scheduled_simple_deployment:
                        log.progress('Deployment scheduled',
                                     flush=True,
                                     next_line=(latest_state is not None))

                        scheduled_deployments = scheduled_simple_deployment

                        # Reset the latest state for tracking deployment events
                        latest_state = None
                    elif batch_events and is_batch_completed_with_failure(batch_events):
                        log.progress('\n', flush=False, line_end='')
                        error_message = log_message_batch(batch_events)
                        raise ContinuousDeliveryError(error_message)
                    elif batch_events != latest_state:
                        log.progress(log_message_batch(batch_events),
                                     flush=False,
                                     line_end='',
                                     next_line=(latest_state is not None))
                        latest_state = batch_events

                    else:
                        log.progress('.', flush=False, line_end='')

                else:
                    deployments = get_deployment_events(deployment_batch_id, args)
                    if deployments:
                        if is_completed_with_success(deployments):
                            # Reprint previous message with flush to go to next line
                            log.progress('Success',
                                         flush=True,
                                         next_line=(latest_state is not None))
                            return

                        elif has_deployment_failure(deployments):
                            deployment_events_current = find_latest_deployment_events(deployments)
                            deployment_events_previous = find_latest_deployment_events(latest_state)

                            deployment_events_to_display = find_deployment_events_to_display(deployment_events_current,
                                                                                             deployment_events_previous)
                            log.progress('\n', flush=False, line_end='')

                            error_message = log_message_deployment(args, deployment_events_to_display)
                            raise ContinuousDeliveryError(error_message)

                        elif deployments != latest_state:
                            deployment_events_current = find_latest_deployment_events(deployments)
                            deployment_events_previous = find_latest_deployment_events(latest_state)

                            deployment_events_to_display = find_deployment_events_to_display(deployment_events_current,
                                                                                             deployment_events_previous)
                            log.progress(log_message_deployment(args, deployment_events_to_display),
                                         flush=False,
                                         line_end='',
                                         next_line=(latest_state is not None))
                            latest_state = deployments
                        else:
                            log.progress('.', flush=False, line_end='')

    raise WaitTimeoutError('Deployment for {} is still waiting to be completed')


def display_batch_event(batch_event):
    event_type = batch_event['eventType']
    if event_type == 'requestAccepted':
        return 'Deployment request accepted'
    elif event_type == 'bundleDownload':
        return 'Downloading bundle'
    elif event_type == 'resolveCompatibleBundle':
        return 'Resolving compatible bundle'
    elif event_type == 'scheduleLockStepDeployments':
        return 'Scheduling deployments'
    elif event_type == 'deploymentFailure':
        return 'Failure: {}'.format(batch_event['failure'])
    else:
        return 'Batch event {}'.format(batch_event)


def display_deploy_event(args, deploy_event):
    event_type = deploy_event['eventType']

    if 'deploymentTarget' in deploy_event:
        target_bundle_id = deploy_event['deploymentTarget']['bundleId']
        prefix = '[{}] '.format(display_bundle_id(args, target_bundle_id))
    else:
        prefix = ''

    if event_type == 'deploymentScheduled':
        return '{}Deployment scheduled'.format(prefix)

    elif event_type == 'deploymentStarted':
        return '{}Deployment started'.format(prefix)

    elif event_type == 'configDownload':
        return '{}Downloading config'.format(prefix)

    elif event_type == 'load':
        message = 'Loading bundle with config' if 'configFileName' in deploy_event else 'Loading bundle'
        return '{}{}'.format(prefix, message)

    elif event_type == 'deployLockStep':
        bundle_old = deploy_event['bundleOld']
        bundle_new = deploy_event['bundleNew']
        deploy_progress = '{}Deploying - {} old instance vs {} new instance'.format(prefix,
                                                                                    bundle_old['scale'],
                                                                                    bundle_new['scale'])
        return deploy_progress

    elif event_type == 'deploySimple':
        return '{}Deploying new instance'.format(prefix)

    elif event_type == 'deploymentSuccess':
        return '{}Success'.format(prefix)

    elif event_type == 'deploymentFailure':
        return '{}Failure: {}'.format(prefix, deploy_event['failure'])

    else:
        return 'Deploy event {}'.format(deploy_event)
