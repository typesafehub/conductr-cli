from conductr_cli import conduct_request, conduct_url, validation, bundle_installation
from conductr_cli.conduct_url import conductr_host
import json
import logging
from conductr_cli.http import DEFAULT_HTTP_TIMEOUT


@validation.handle_connection_error
@validation.handle_http_error
def unload(args):
    """`conduct unload` command"""

    log = logging.getLogger(__name__)
    path = 'bundles/{}'.format(args.bundle)
    url = conduct_url.url(path, args)
    response = conduct_request.delete(args.dcos_mode, conductr_host(args), url, auth=args.conductr_auth,
                                      verify=args.server_verification_file, timeout=DEFAULT_HTTP_TIMEOUT)
    validation.raise_for_status_inc_3xx(response)

    if log.is_verbose_enabled():
        log.verbose(validation.pretty_json(response.text))

    log.info('Bundle unload request sent.')

    response_json = json.loads(response.text)
    if not args.no_wait:
        bundle_installation.wait_for_uninstallation(response_json['bundleId'], args)

    if not args.disable_instructions:
        log.info('Print ConductR info with: {} info{}'.format(args.command, args.cli_parameters))

    if not log.is_info_enabled() and log.is_quiet_enabled():
        log.quiet(response_json['bundleId'])

    return True
