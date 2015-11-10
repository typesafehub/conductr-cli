from conductr_cli import bundle_utils, conduct_url, validation
import json
import requests
from conductr_cli.http import DEFAULT_HTTP_TIMEOUT


@validation.handle_connection_error
@validation.handle_http_error
def stop(args):
    """`conduct stop` command"""

    path = 'bundles/{}?scale=0'.format(args.bundle)
    url = conduct_url.url(path, args)
    response = requests.put(url, timeout=DEFAULT_HTTP_TIMEOUT)
    validation.raise_for_status_inc_3xx(response)

    if args.verbose:
        validation.pretty_json(response.text)

    response_json = json.loads(response.text)
    bundle_id = response_json['bundleId'] if args.long_ids else bundle_utils.short_id(response_json['bundleId'])

    print('Bundle stop request sent.')
    print('Unload bundle with: conduct unload{} {}'.format(args.cli_parameters, bundle_id))
    print('Print ConductR info with: conduct info{}'.format(args.cli_parameters))
