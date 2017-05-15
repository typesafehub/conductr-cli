from conductr_cli import validation, conduct_request, conduct_url, screen_utils
from conductr_cli.conduct_url import conductr_host
import json
import logging
from conductr_cli.http import DEFAULT_HTTP_TIMEOUT
from urllib.parse import quote_plus


@validation.handle_connection_error
@validation.handle_http_error
def events(args):
    """`conduct events` command"""

    log = logging.getLogger(__name__)
    bundle_events = get_bundle_events(args, args.lines)
    data = [
        {
            'time': validation.format_timestamp(event['timestamp'], args),
            'event': event['event'],
            'description': event['description']
        } for event in bundle_events
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


def get_bundle_events(args, count):
    request_url = conduct_url.url('bundles/{}/events?count={}'.format(quote_plus(args.bundle), count), args)
    response = conduct_request.get(args.dcos_mode, conductr_host(args), request_url, auth=args.conductr_auth,
                                   verify=args.server_verification_file, timeout=DEFAULT_HTTP_TIMEOUT)
    validation.raise_for_status_inc_3xx(response)
    return json.loads(response.text)
