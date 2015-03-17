from typesafe_conductr_cli import bundle_utils, conduct_info, conduct_url, conduct_logging
import json
import requests
from urllib.parse import urlparse


@conduct_logging.handle_connection_error
@conduct_logging.handle_http_error
def services(args):
    """`conduct services` command"""

    url = conduct_url.url('bundles', args)
    response = requests.get(url)
    conduct_logging.raise_for_status_inc_3xx(response)

    if (args.verbose):
        conduct_logging.pretty_json(response.text)

    data = sorted([
        (
            {
                'service': service,
                'bundle_id': bundle['bundleId'] if args.long_ids else bundle_utils.short_id(bundle['bundleId']),
                'bundle_name': bundle['attributes']['bundleName'],
                'status': 'Running' if execution['isStarted'] else 'Starting'
            }
        )
        for bundle in json.loads(response.text)
        for execution in bundle['bundleExecutions']
        for endpoint_name, endpoint in bundle['bundleConfig']['endpoints'].items()
        for service in endpoint['services']
    ], key=lambda line: line['service'])

    service_endpoints = {}
    for service in data:
        url = urlparse(service['service'])
        try:
            service_endpoints[url.path] |= {service['service']}
        except KeyError:
            service_endpoints[url.path] = {service['service']}
    duplicate_endpoints = [service for (service, endpoint) in service_endpoints.items() if len(endpoint) > 1] if len(service_endpoints) > 0 else []

    data.insert(0, {'service': 'SERVICE', 'bundle_id': 'BUNDLE ID', 'bundle_name': 'BUNDLE NAME', 'status': 'STATUS'})

    padding = 2
    column_widths = dict(conduct_info.calc_column_widths(data), **{'padding': ' ' * padding})
    for row in data:
        print('{service: <{service_width}}{padding}{bundle_id: <{bundle_id_width}}{padding}{bundle_name: <{bundle_name_width}}{padding}{status: <{status_width}}'.format(**dict(row, **column_widths)))

    if len(duplicate_endpoints) > 0:
        print()
        conduct_logging.warning('Multiple endpoints found for the following services: {}'.format(', '.join(duplicate_endpoints)))
        conduct_logging.warning('Service resolution for these services is undefined.')
