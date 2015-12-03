from __future__ import unicode_literals
from conductr_cli import conduct_url, sse_client
from conductr_cli.exceptions import WaitTimeoutError
from datetime import datetime
import json
import logging
import requests


def count_installations(bundle_id, args):
    bundles_url = conduct_url.url('bundles', args)
    response = requests.get(bundles_url)
    response.raise_for_status()
    bundles = json.loads(response.text)
    matching_bundles = [bundle for bundle in bundles if bundle['bundleId'] == bundle_id]
    if matching_bundles:
        matching_bundle = matching_bundles[0]
        if 'bundleInstallations' in matching_bundle:
            return len(matching_bundle['bundleInstallations'])

    return 0


def wait_for_installation(bundle_id, args):
    log = logging.getLogger(__name__)
    start_time = datetime.now()

    installed_bundles = count_installations(bundle_id, args)
    if installed_bundles > 0:
        log.info('Bundle {} is installed'.format(bundle_id))
        return
    else:
        log.info('Bundle {} waiting to be installed'.format(bundle_id))
        bundle_events_url = conduct_url.url('bundles/events', args)
        sse_events = sse_client.get_events(bundle_events_url)
        for event in sse_events:
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > args.wait_timeout:
                raise WaitTimeoutError('Bundle {} waiting to be installed'.format(bundle_id))

            if event.event and event.event.startswith('bundleInstallation'):
                installed_bundles = count_installations(bundle_id, args)
                if installed_bundles > 0:
                    log.info('Bundle {} installed'.format(bundle_id))
                    return
                else:
                    log.info('Bundle {} still waiting to be installed'.format(bundle_id))

        raise WaitTimeoutError('Bundle {} still waiting to be installed'.format(bundle_id))
