from typesafe_conductr_cli import conduct_info, conduct_url, conduct_logging
import json
import requests


@conduct_logging.handle_connection_error
@conduct_logging.handle_http_error
def services(args):
    """`conduct services` command"""

    url = conduct_url.url('bundles', args)
    response = requests.get(url)
    response.raise_for_status()

    if (args.verbose):
        conduct_logging.pretty_json(response.text)

    data_and_service_names = [
        (
            {
                'protocol': endpoint['protocol'],
                'service': str(endpoint['servicePort']) + endpoint['serviceName'],
                'bundle_id': bundle['bundleId'],
                'bundle_name': bundle['attributes']['bundleName'],
                'status': 'Running' if execution['isStarted'] else 'Starting'
            },
            endpoint['serviceName']
        )
        for bundle in json.loads(response.text)
        for execution in bundle['bundleExecutions']
        for component, endpoints in execution['endpoints'].items()
        for endpoint_name, endpoint in endpoints.items()
    ]
    data, service_names = [list(tuple) for tuple in zip(*sorted(data_and_service_names, key=lambda line: line[1]))]
    data.insert(0, {'protocol': 'PROTO', 'service': 'SERVICE', 'bundle_id': 'BUNDLE ID', 'bundle_name': 'BUNDLE NAME', 'status': 'STATUS'})

    duplicate_service_names = sorted(set([name for name in service_names if service_names.count(name) > 1]))

    column_widths = conduct_info.calc_column_widths(data)
    for row in data:
        print('{protocol: <{protocol_width}}{service: <{service_width}}{bundle_id: <{bundle_id_width}}{bundle_name: <{bundle_name_width}}{status: <{status_width}}'.format(**dict(row, **column_widths)))

    if len(duplicate_service_names) > 0:
        print()
        conduct_logging.warning('Multiple endpoints found for the following services: {}'.format(', '.join(duplicate_service_names)))
        conduct_logging.warning('Service resolution for these services is undefined.')
