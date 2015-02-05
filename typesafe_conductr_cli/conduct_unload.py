from typesafe_conductr_cli import conduct_url, conduct_logging
import requests


@conduct_logging.handle_connection_error
@conduct_logging.handle_http_error
def unload(args):
    """`conduct unload` command"""

    path = 'bundles/{}'.format(args.bundle)
    url = conduct_url.url(path, args)
    response = requests.delete(url)
    response.raise_for_status()

    if (args.verbose):
        conduct_logging.pretty_json(response.text)

    print('Bundle unload request sent.')
    print('Print ConductR info with: conduct info{}'.format(args.cli_parameters))
