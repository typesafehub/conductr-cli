from conductr_cli import bundle_utils, conduct_url, validation, screen_utils
import json
import logging
import requests
from conductr_cli.http import DEFAULT_HTTP_TIMEOUT


@validation.handle_connection_error
@validation.handle_http_error
def info(args):
    """`conduct info` command"""

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

    data = [
        {
            'id': ('! ' if bundle.get('hasError', False) else '') +
                  (bundle['bundleId'] if args.long_ids else bundle_utils.short_id(bundle['bundleId'])),
            'name': bundle['attributes']['bundleName'],
            'replications': len(bundle['bundleInstallations']),
            'starting': sum([not execution['isStarted'] for execution in bundle['bundleExecutions']]),
            'executions': sum([execution['isStarted'] for execution in bundle['bundleExecutions']])
        } for bundle in json.loads(response.text)
    ]
    data.insert(0, {'id': 'ID', 'name': 'NAME', 'replications': '#REP', 'starting': '#STR', 'executions': '#RUN'})

    padding = 2
    column_widths = dict(screen_utils.calc_column_widths(data), **{'padding': ' ' * padding})
    has_error = False
    for row in data:
        has_error |= '!' in row['id']
        log.screen('''\
{id: <{id_width}}{padding}\
{name: <{name_width}}{padding}\
{replications: >{replications_width}}{padding}\
{starting: >{starting_width}}{padding}\
{executions: >{executions_width}}'''.format(**dict(row, **column_widths)).rstrip())

    if has_error:
        log.screen('There are errors: use `conduct events` or `conduct logs` for further information')

    return True
