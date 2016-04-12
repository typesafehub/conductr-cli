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
    # At the time when this comment is being written, we need to pass the Host header when making HTTP request due to
    # a bug with requests python library not working properly when IPv6 address is supplied:
    # https://github.com/kennethreitz/requests/issues/3002
    # The workaround for this problem is to explicitly set the Host header when making HTTP request.
    # This fix is benign and backward compatible as the library would do this when making HTTP request anyway.
    response = requests.delete(url, timeout=DEFAULT_HTTP_TIMEOUT, headers=conduct_url.request_headers(args))
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
