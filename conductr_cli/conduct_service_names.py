from conductr_cli import bundle_utils, conduct_request, conduct_url, validation, screen_utils
from conductr_cli.http import DEFAULT_HTTP_TIMEOUT
from conductr_cli.conduct_url import conductr_host
import json
import logging
from urllib.parse import urlparse


@validation.handle_connection_error
@validation.handle_http_error
def service_names(args):
    """`conduct service-names` command"""

    log = logging.getLogger(__name__)
    url = conduct_url.url('bundles', args)
    response = conduct_request.get(args.dcos_mode, conductr_host(args), url, timeout=DEFAULT_HTTP_TIMEOUT)
    validation.raise_for_status_inc_3xx(response)

    if log.is_verbose_enabled():
        log.verbose(validation.pretty_json(response.text))

    def execution_status(bundle_executions):
        for execution in bundle_executions:
            if execution['isStarted']:
                return 'Running'
        return 'Starting'

    def get_service_name_from_service_uri(service_uri):
        paths = urlparse(service_uri).path.split('/')
        if len(paths) > 1:
            return paths[1]
        else:
            return ''

    data_from_service_uri = [
        (
            {
                'service_name': get_service_name_from_service_uri(service_uri),
                'service_uri': service_uri,
                'bundle_id': bundle['bundleId'] if args.long_ids else bundle_utils.short_id(
                    bundle['bundleId']),
                'bundle_name': bundle['attributes']['bundleName'],
                'status': execution_status(bundle['bundleExecutions'])
            }
        )
        for bundle in json.loads(response.text) if bundle['bundleExecutions']
        for endpoint_name, endpoint in bundle['bundleConfig']['endpoints'].items() if 'services' in endpoint
        for service_uri in endpoint['services']
    ]

    data_from_service_name = [
        (
            {
                'service_name': endpoint['serviceName'],
                'service_uri': None,
                'bundle_id': bundle['bundleId'] if args.long_ids else bundle_utils.short_id(
                    bundle['bundleId']),
                'bundle_name': bundle['attributes']['bundleName'],
                'status': execution_status(bundle['bundleExecutions'])
            }
        )
        for bundle in json.loads(response.text) if bundle['bundleExecutions']
        for endpoint_name, endpoint in bundle['bundleConfig']['endpoints'].items() if 'serviceName' in endpoint
    ]

    data = data_from_service_uri + data_from_service_name
    data = sorted([entry for entry in data if entry['service_name']], key=lambda line: line['service_name'])

    service_endpoints = {}
    for service in data:
        url = urlparse(service['service_uri'])
        if not (url.path == '' or url.path == '/'):
            try:
                service_endpoints[url.path] |= {service['service_uri']}
            except KeyError:
                service_endpoints[url.path] = {service['service_uri']}
    duplicate_endpoints = [service for (service, endpoint) in service_endpoints.items() if len(endpoint) > 1] \
        if len(service_endpoints) > 0 else []

    data.insert(0, {'service_name': 'SERVICE NAME', 'bundle_id': 'BUNDLE ID', 'bundle_name': 'BUNDLE NAME', 'status': 'STATUS'})

    padding = 2
    column_widths = dict(screen_utils.calc_column_widths(data), **{'padding': ' ' * padding})
    for row in data:
        log.screen(
            '{service_name: <{service_name_width}}{padding}'
            '{bundle_id: <{bundle_id_width}}{padding}'
            '{bundle_name: <{bundle_name_width}}{padding}'
            '{status: <{status_width}}'.format(**dict(row, **column_widths)).rstrip())

    if len(duplicate_endpoints) > 0:
        log.screen('')
        log.warning('Multiple endpoints found for the following services: {}'.format(', '.join(duplicate_endpoints)))
        log.warning('Service resolution for these services is undefined.')

    return True
