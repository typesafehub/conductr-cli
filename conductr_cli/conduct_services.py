from conductr_cli import bundle_utils, conduct_url, validation, screen_utils
import json
import logging
import requests
from urllib.parse import urlparse
from conductr_cli.http import DEFAULT_HTTP_TIMEOUT


@validation.handle_connection_error
@validation.handle_http_error
def services(args):
    """`conduct services` command"""

    log = logging.getLogger(__name__)
    url = conduct_url.url('bundles', args)
    # At the time when this comment is being written, we need to pass the Host header when making HTTP request due to
    # a bug with requests python library not working properly when IPv6 address is supplied:
    # https://github.com/kennethreitz/requests/issues/3002
    # The workaround for this problem is to explicitly set the Host header when making HTTP request.
    # This fix is benign and backward compatible as the library would do this when making HTTP request anyway.
    response = requests.get(url, timeout=DEFAULT_HTTP_TIMEOUT, headers=conduct_url.request_headers(args))
    validation.raise_for_status_inc_3xx(response)

    if log.is_verbose_enabled():
        log.verbose(validation.pretty_json(response.text))

    data = sorted([
                  (
                      {
                          'service': service,
                          'bundle_id': bundle['bundleId'] if args.long_ids else bundle_utils.short_id(
                              bundle['bundleId']),
                          'bundle_name': bundle['attributes']['bundleName'],
                          'status': 'Running' if execution['isStarted'] else 'Starting'
                      }
                  )
                  for bundle in json.loads(response.text)
                  for execution in bundle['bundleExecutions']
                  for endpoint_name, endpoint in bundle['bundleConfig']['endpoints'].items() if 'services' in endpoint
                  for service in endpoint['services']
                  ], key=lambda line: line['service'])

    service_endpoints = {}
    for service in data:
        url = urlparse(service['service'])
        if not (url.path == '' or url.path == '/'):
            try:
                service_endpoints[url.path] |= {service['service']}
            except KeyError:
                service_endpoints[url.path] = {service['service']}
    duplicate_endpoints = [service for (service, endpoint) in service_endpoints.items() if len(endpoint) > 1] \
        if len(service_endpoints) > 0 else []

    data.insert(0, {'service': 'SERVICE', 'bundle_id': 'BUNDLE ID', 'bundle_name': 'BUNDLE NAME', 'status': 'STATUS'})

    padding = 2
    column_widths = dict(screen_utils.calc_column_widths(data), **{'padding': ' ' * padding})
    for row in data:
        log.screen(
            '{service: <{service_width}}{padding}'
            '{bundle_id: <{bundle_id_width}}{padding}'
            '{bundle_name: <{bundle_name_width}}{padding}'
            '{status: <{status_width}}'.format(**dict(row, **column_widths)).rstrip())

    if len(duplicate_endpoints) > 0:
        log.screen('')
        log.warning('Multiple endpoints found for the following services: {}'.format(', '.join(duplicate_endpoints)))
        log.warning('Service resolution for these services is undefined.')

    return True
