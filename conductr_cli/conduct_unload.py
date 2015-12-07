from conductr_cli import conduct_url, validation, bundle_installation
import json
import logging
import requests
from conductr_cli.http import DEFAULT_HTTP_TIMEOUT


@validation.handle_connection_error
@validation.handle_http_error
def unload(args):
    """`conduct unload` command"""

    log = logging.getLogger(__name__)
    path = 'bundles/{}'.format(args.bundle)
    url = conduct_url.url(path, args)
    response = requests.delete(url, timeout=DEFAULT_HTTP_TIMEOUT)
    validation.raise_for_status_inc_3xx(response)

    if log.is_verbose_enabled():
        log.verbose(validation.pretty_json(response.text))

    log.info('Bundle unload request sent.')

    response_json = json.loads(response.text)
    if not args.no_wait:
        bundle_installation.wait_for_uninstallation(response_json['bundleId'], args)

    log.info('Print ConductR info with: conduct info{}'.format(args.cli_parameters))

    if not log.is_info_enabled() and log.is_quiet_enabled():
        log.quiet(response_json['bundleId'])

    return True
