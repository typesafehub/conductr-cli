from conductr_cli import conduct_logging, conduct_info, conduct_url
import json
import requests


@conduct_logging.handle_connection_error
@conduct_logging.handle_http_error
def events(args):
    """`conduct events` command"""

    request_url = conduct_url.url('bundles/{}/events?count={}'.format(args.bundle, args.lines), args)
    response = requests.get(request_url)
    conduct_logging.raise_for_status_inc_3xx(response)

    data = [
        {
            'time': conduct_logging.format_timestamp(event['timestamp'], args),
            'event': event['event'],
            'description': event['description']
        } for event in json.loads(response.text)
    ]
    data.insert(0, {'time': 'TIME', 'event': 'EVENT', 'description': 'DESC'})

    padding = 2
    column_widths = dict(conduct_info.calc_column_widths(data), **{'padding': ' ' * padding})

    for row in data:
        print('''\
{time: <{time_width}}{padding}\
{event: <{event_width}}{padding}\
{description: <{description_width}}{padding}'''.format(**dict(row, **column_widths)))
