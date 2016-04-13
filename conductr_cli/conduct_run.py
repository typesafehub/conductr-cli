from conductr_cli import bundle_utils, conduct_url, validation
from conductr_cli import bundle_scale
import json
import logging
import requests


@validation.handle_connection_error
@validation.handle_http_error
@validation.handle_wait_timeout_error
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
    # At the time when this comment is being written, we need to pass the Host header when making HTTP request due to
    # a bug with requests python library not working properly when IPv6 address is supplied:
    # https://github.com/kennethreitz/requests/issues/3002
    # The workaround for this problem is to explicitly set the Host header when making HTTP request.
    # This fix is benign and backward compatible as the library would do this when making HTTP request anyway.
    response = requests.put(url, headers=conduct_url.request_headers(args))
    validation.raise_for_status_inc_3xx(response)

    if log.is_verbose_enabled():
        log.verbose(validation.pretty_json(response.text))

    response_json = json.loads(response.text)
    bundle_id = response_json['bundleId'] if args.long_ids else bundle_utils.short_id(response_json['bundleId'])

    log.info('Bundle run request sent.')

    if not args.no_wait:
        bundle_scale.wait_for_scale(response_json['bundleId'], args.scale, args)

    log.info('Stop bundle with: conduct stop{} {}'.format(args.cli_parameters, bundle_id))
    log.info('Print ConductR info with: conduct info{}'.format(args.cli_parameters))

    return True
