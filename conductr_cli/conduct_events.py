from conductr_cli import conduct_logging, conduct_info
import json
import requests


@conduct_logging.handle_connection_error
@conduct_logging.handle_http_error
def events(args):
    """`conduct events` command"""

    response = requests.get('{}/events/{}'.format(args.service, args.bundle))
    conduct_logging.raise_for_status_inc_3xx(response)

    data = [
        {
            'time': event['@cee']['body']['time'],
            'event': event['@cee']['head']['contentType'],
            'description': event['@cee']['body']['message']
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
