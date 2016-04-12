from __future__ import unicode_literals
from conductr_cli import conduct_url, sse_client
from conductr_cli.exceptions import WaitTimeoutError
from datetime import datetime
import json
import logging
import requests


def get_scale(bundle_id, args):
    bundles_url = conduct_url.url('bundles', args)
    # At the time when this comment is being written, we need to pass the Host header when making HTTP request due to
    # a bug with requests python library not working properly when IPv6 address is supplied:
    # https://github.com/kennethreitz/requests/issues/3002
    # The workaround for this problem is to explicitly set the Host header when making HTTP request.
    # This fix is benign and backward compatible as the library would do this when making HTTP request anyway.
    response = requests.get(bundles_url, headers=conduct_url.request_headers(args))
    response.raise_for_status()
    bundles = json.loads(response.text)
    matching_bundles = [bundle for bundle in bundles if bundle['bundleId'] == bundle_id]
    if matching_bundles:
        matching_bundle = matching_bundles[0]
        if 'bundleExecutions' in matching_bundle:
            started_executions = [bundle_execution
                                  for bundle_execution in matching_bundle['bundleExecutions']
                                  if bundle_execution['isStarted']]
            return len(started_executions)

    return 0


def wait_for_scale(bundle_id, expected_scale, args):
    log = logging.getLogger(__name__)
    start_time = datetime.now()

    bundle_scale = get_scale(bundle_id, args)
    if bundle_scale == expected_scale:
        log.info('Bundle {} expected scale {} is met'.format(bundle_id, expected_scale))
        return
    else:
        log.info('Bundle {} waiting to reach expected scale {}'.format(bundle_id, expected_scale))
        bundle_events_url = conduct_url.url('bundles/events', args)
        sse_events = sse_client.get_events(bundle_events_url, headers=conduct_url.request_headers(args))
        for event in sse_events:
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > args.wait_timeout:
                raise WaitTimeoutError('Bundle {} waiting to reach expected scale {}'.format(bundle_id, expected_scale))

            if event.event and event.event.startswith('bundleExecution'):
                bundle_scale = get_scale(bundle_id, args)
                if bundle_scale == expected_scale:
                    log.info('Bundle {} expected scale {} is met'.format(bundle_id, expected_scale))
                    return
                else:
                    log.info('Bundle {} has scale {}, expected {}'.format(bundle_id, bundle_scale, expected_scale))

        raise WaitTimeoutError('Bundle {} waiting to reach expected scale {}'.format(bundle_id, expected_scale))
