from conductr_cli import conduct_logging, conduct_info
import json
import requests


@conduct_logging.handle_connection_error
@conduct_logging.handle_http_error
def logs(args):
    """`conduct logs` command"""

    response = requests.get('{}/logs/{}'.format(args.service, args.bundle))
    conduct_logging.raise_for_status_inc_3xx(response)

    data = [
        {
            'time': event['@cee']['body']['time'],
            'host': event['@cee']['body']['host'],
            'log': event['@cee']['body']['log']
        } for event in json.loads(response.text)
    ]
    data.insert(0, {'time': 'TIME', 'host': 'HOST', 'log': 'LOG'})

    padding = 2
    column_widths = dict(conduct_info.calc_column_widths(data), **{'padding': ' ' * padding})

    for row in data:
        print('''\
{time: <{time_width}}{padding}\
{host: <{host_width}}{padding}\
{log: <{log_width}}{padding}'''.format(**dict(row, **column_widths)))
