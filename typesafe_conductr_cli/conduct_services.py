from typesafe_conductr_cli import bundle_utils, conduct_info, conduct_url, conduct_logging
import json
import requests


@conduct_logging.handle_connection_error
@conduct_logging.handle_http_error
def services(args):
    """`conduct services` command"""

    url = conduct_url.url('bundles', args)
    response = requests.get(url)
    conduct_logging.raise_for_status_inc_3xx(response)

    if (args.verbose):
        conduct_logging.pretty_json(response.text)

    data_and_services = [
        (
            {
                'protocol': endpoint['protocol'],
                'service': str(endpoint['servicePort']) + endpoint['serviceName'],
                'bundle_id': bundle['bundleId'] if args.long_ids else bundle_utils.short_id(bundle['bundleId']),
                'bundle_name': bundle['attributes']['bundleName'],
                'status': 'Running' if execution['isStarted'] else 'Starting'
            },
            {
                'port': endpoint['servicePort'],
                'name': endpoint['serviceName']
            }
        )
        for bundle in json.loads(response.text)
        for execution in bundle['bundleExecutions']
        for endpoint_name, endpoint in bundle['bundleConfig']['endpoints'].items()
    ]
    data, services = [list(tuple) for tuple in zip(*sorted(data_and_services, key=lambda line: line[1]['name']))] if len(data_and_services) > 0 else ([], [])
    data.insert(0, {'protocol': 'PROTO', 'service': 'SERVICE', 'bundle_id': 'BUNDLE ID', 'bundle_name': 'BUNDLE NAME', 'status': 'STATUS'})

    def duplicates(service):
        return [other['name'] for other in services if service['name'] == other['name'] and service['port'] != other['port']]

    duplicate_services = sorted(set([service['name'] for service in services if len(duplicates(service)) > 0]))

    column_widths = conduct_info.calc_column_widths(data)
    for row in data:
        print('{protocol: <{protocol_width}}{service: <{service_width}}{bundle_id: <{bundle_id_width}}{bundle_name: <{bundle_name_width}}{status: <{status_width}}'.format(**dict(row, **column_widths)))

    if len(duplicate_services) > 0:
        print()
        conduct_logging.warning('Multiple endpoints found for the following services: {}'.format(', '.join(duplicate_services)))
        conduct_logging.warning('Service resolution for these services is undefined.')
