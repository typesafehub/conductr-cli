from typesafe_conductr_cli import bundle_id, conduct_url, conduct_logging
import json
import requests


@conduct_logging.handle_connection_error
@conduct_logging.handle_http_error
def info(args):
    """`conduct info` command"""

    url = conduct_url.url('bundles', args)
    response = requests.get(url)
    response.raise_for_status()

    if (args.verbose):
        conduct_logging.pretty_json(response.text)

    data = [
        {
            'id': bundle['bundleId'] if args.long_ids else bundle_id.shorten(bundle['bundleId']),
            'name': bundle['attributes']['bundleName'],
            'replications': len(bundle['bundleInstallations']),
            'starting': sum([not execution['isStarted'] for execution in bundle['bundleExecutions']]),
            'executions': sum([execution['isStarted'] for execution in bundle['bundleExecutions']])
        } for bundle in json.loads(response.text)
    ]
    data.insert(0, {'id': 'ID', 'name': 'NAME', 'replications': '#REP', 'starting': '#STR', 'executions': '#RUN'})

    column_widths = calc_column_widths(data)
    for row in data:
        print('{id: <{id_width}}{name: <{name_width}}{replications: <{replications_width}}{starting: <{starting_width}}{executions: <{executions_width}}'.format(**dict(row, **column_widths)))


def calc_column_widths(data):
    padding = 2
    column_widths = {}
    for row in data:
        for column, value in row.items():
            column_len = len(str(value)) + padding
            width_key = column + '_width'
            if (column_len > column_widths.get(width_key, 0)):
                column_widths[width_key] = column_len
    return column_widths
