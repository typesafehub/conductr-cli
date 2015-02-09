from typesafe_conductr_cli import bundle_id, conduct_url, conduct_logging
import json
import requests


@conduct_logging.handle_connection_error
@conduct_logging.handle_http_error
def run(args):
    """`conduct run` command"""

    path = 'bundles/{}?scale={}'.format(args.bundle, args.scale)
    url = conduct_url.url(path, args)
    response = requests.put(url)
    response.raise_for_status()

    if (args.verbose):
        conduct_logging.pretty_json(response.text)

    response_json = json.loads(response.text)
    bundleId = response_json['bundleId'] if args.long_ids else bundle_id.shorten(response_json['bundleId'])

    print('Bundle run request sent.')
    print('Stop bundle with: conduct stop{} {}'.format(args.cli_parameters, bundleId))
    print('Print ConductR info with: conduct info{}'.format(args.cli_parameters))
