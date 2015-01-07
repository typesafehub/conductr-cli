import conduct_logging
import conduct_url
import json
import requests


# `conduct info` command
def info(args):
    url = conduct_url.url('bundles', args)
    response = requests.get(url)
    response.raise_for_status()

    if (args.verbose):
        conduct_logging.pretty_json(response.text)

    data = [
        {
            'id': bundle['bundleId'],
            'executions': len(bundle['bundleExecutions'])
        } for bundle in json.loads(response.text)
    ]
    data.insert(0, {'id': 'ID', 'executions': '#RUN'})

    padding = 2
    column_widths = {}
    for row in data:
        for column, value in row.items():
            column_len = len(str(value)) + padding
            if (column_len > column_widths.get(column, 0)):
                column_widths[column + "_width"] = column_len

    for row in data:
        print("{id: <{id_width}}{executions: <{executions_width}}".format(**dict(row, **column_widths)))
