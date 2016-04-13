from __future__ import unicode_literals
from conductr_cli import conduct_url, sse_client
from conductr_cli.exceptions import WaitTimeoutError
from datetime import datetime
import json
import logging
import requests


def count_installations(bundle_id, args):
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
    if condition(installed_bundles):
        log.info('Bundle {} is {}'.format(bundle_id, condition_name))
        return
    else:
        log.info('Bundle {} waiting to be {}'.format(bundle_id, condition_name))
        bundle_events_url = conduct_url.url('bundles/events', args)
        sse_events = sse_client.get_events(bundle_events_url, headers=conduct_url.request_headers(args))
        for event in sse_events:
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > args.wait_timeout:
                raise WaitTimeoutError('Bundle {} waiting to be {}'.format(bundle_id, condition_name))

            if event.event and event.event.startswith('bundleInstallation'):
                installed_bundles = count_installations(bundle_id, args)
                if condition(installed_bundles):
                    log.info('Bundle {} {}'.format(bundle_id, condition_name))
                    return
                else:
                    log.info('Bundle {} still waiting to be {}'.format(bundle_id, condition_name))

        raise WaitTimeoutError('Bundle {} still waiting to be {}'.format(bundle_id, condition_name))


def is_installed(number_of_installations):
    return number_of_installations > 0


def is_uninstalled(number_of_installations):
    return number_of_installations <= 0
