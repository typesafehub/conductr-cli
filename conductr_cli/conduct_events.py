from conductr_cli import validation, conduct_url, screen_utils
import json
import logging
import requests
from conductr_cli.http import DEFAULT_HTTP_TIMEOUT
from urllib.parse import quote_plus


@validation.handle_connection_error
@validation.handle_http_error
def events(args):
    """`conduct events` command"""

    log = logging.getLogger(__name__)
    request_url = conduct_url.url('bundles/{}/events?count={}'.format(quote_plus(args.bundle), args.lines), args)
    # At the time when this comment is being written, we need to pass the Host header when making HTTP request due to
    # a bug with requests python library not working properly when IPv6 address is supplied:
    # https://github.com/kennethreitz/requests/issues/3002
    # The workaround for this problem is to explicitly set the Host header when making HTTP request.
    # This fix is benign and backward compatible as the library would do this when making HTTP request anyway.
    response = requests.get(request_url, timeout=DEFAULT_HTTP_TIMEOUT, headers=conduct_url.request_headers(args))
    validation.raise_for_status_inc_3xx(response)

    data = [
        {
            'time': validation.format_timestamp(event['timestamp'], args),
            'event': event['event'],
            'description': event['description']
        } for event in json.loads(response.text)
    ]
    data.insert(0, {'time': 'TIME', 'event': 'EVENT', 'description': 'DESC'})

    padding = 2
    column_widths = dict(screen_utils.calc_column_widths(data), **{'padding': ' ' * padding})

    for row in data:
        log.screen('''\
{time: <{time_width}}{padding}\
{event: <{event_width}}{padding}\
{description: <{description_width}}{padding}'''.format(**dict(row, **column_widths)).rstrip())

    return True
