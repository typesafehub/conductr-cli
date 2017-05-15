from conductr_cli import bundle_utils, bundle_scale, conduct_request, conduct_url, validation
from conductr_cli.conduct_url import conductr_host
import json
import logging


@validation.handle_connection_error
@validation.handle_http_error
@validation.handle_wait_timeout_error
@validation.handle_bundle_scale_error
def run(args):
    """`conduct run` command"""

    log = logging.getLogger(__name__)

    if args.affinity is not None and args.api_version == '1':
        log.error('Affinity feature is only available for v1.1 onwards of ConductR')
        return
    elif args.affinity is not None:
        path = 'bundles/{}?scale={}&affinity={}'.format(args.bundle, args.scale, args.affinity)
    else:
        path = 'bundles/{}?scale={}'.format(args.bundle, args.scale)

    url = conduct_url.url(path, args)
    response = conduct_request.put(args.dcos_mode, conductr_host(args), url, auth=args.conductr_auth,
                                   verify=args.server_verification_file)
    validation.raise_for_status_inc_3xx(response)

    if log.is_verbose_enabled():
        log.verbose(validation.pretty_json(response.text))

    response_json = json.loads(response.text)
    bundle_id = response_json['bundleId'] if args.long_ids else bundle_utils.short_id(response_json['bundleId'])

    log.info('Bundle run request sent.')

    if not args.no_wait:
        bundle_scale.wait_for_scale(response_json['bundleId'], args.scale, wait_for_is_active=True, args=args)

    if not args.disable_instructions:
        log.info('Stop bundle with:         {} stop{} {}'.format(args.command, args.cli_parameters, bundle_id))
        log.info('Print ConductR info with: {} info{}'.format(args.command, args.cli_parameters))
        log.info('Print bundle info with:   {} info{} {}'.format(args.command, args.cli_parameters, bundle_id))

    return True
