from conductr_cli import bundle_utils, conduct_url, validation
import json
import requests
import sys


@validation.handle_connection_error
@validation.handle_http_error
def run(args):
    """`conduct run` command"""

    if args.affinity is not None and args.api_version == '1.0':
        print('ERROR: Affinity feature is only available for v1.1 onwards of ConductR', file=sys.stderr)
        return
    elif args.affinity is not None:
        path = 'bundles/{}?scale={}&affinity={}'.format(args.bundle, args.scale, args.affinity)
    else:
        path = 'bundles/{}?scale={}'.format(args.bundle, args.scale)

    url = conduct_url.url(path, args)
    response = requests.put(url)
    validation.raise_for_status_inc_3xx(response)

    if args.verbose:
        validation.pretty_json(response.text)

    response_json = json.loads(response.text)
    bundle_id = response_json['bundleId'] if args.long_ids else bundle_utils.short_id(response_json['bundleId'])

    print('Bundle run request sent.')
    print('Stop bundle with: conduct stop{} {}'.format(args.cli_parameters, bundle_id))
    print('Print ConductR info with: conduct info{}'.format(args.cli_parameters))
