from conductr_cli import bundle_utils, conduct_request, conduct_url, validation, bundle_scale
from conductr_cli.conduct_url import conductr_host
import json
import logging
from conductr_cli.http import DEFAULT_HTTP_TIMEOUT


@validation.handle_connection_error
@validation.handle_http_error
@validation.handle_wait_timeout_error
def stop(args):
    """`conduct stop` command"""

    log = logging.getLogger(__name__)
    path = 'bundles/{}?scale=0'.format(args.bundle)
    url = conduct_url.url(path, args)
    response = conduct_request.put(args.dcos_mode, conductr_host(args), url, auth=args.conductr_auth,
                                   verify=args.server_verification_file, timeout=DEFAULT_HTTP_TIMEOUT)
    validation.raise_for_status_inc_3xx(response)

    if log.is_verbose_enabled():
        log.verbose(validation.pretty_json(response.text))

    response_json = json.loads(response.text)
    bundle_id = response_json['bundleId'] if args.long_ids else bundle_utils.short_id(response_json['bundleId'])

    log.info('Bundle stop request sent.')

    if not args.no_wait:
        bundle_scale.wait_for_scale(response_json['bundleId'], 0, wait_for_is_active=False, args=args)

    if not args.disable_instructions:
        log.info('Unload bundle with:       {} unload{} {}'.format(args.command, args.cli_parameters, bundle_id))
        log.info('Print ConductR info with: {} info{}'.format(args.command, args.cli_parameters))
        log.info('Print bundle info with:   {} info{} {}'.format(args.command, args.cli_parameters, bundle_id))

    return True
