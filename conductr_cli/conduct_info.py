from conductr_cli import bundle_utils, conduct_url, conduct_logging
import json
import requests


@conduct_logging.handle_connection_error
@conduct_logging.handle_http_error
def info(args):
    """`conduct info` command"""

    url = conduct_url.url('bundles', args)
    response = requests.get(url)
    conduct_logging.raise_for_status_inc_3xx(response)

    if args.verbose:
        conduct_logging.pretty_json(response.text)

    data = [
        {
            'id': ('! ' if bundle.get('hasError', False) else '') + (bundle['bundleId'] if args.long_ids else bundle_utils.short_id(bundle['bundleId'])),
            'name': bundle['attributes']['bundleName'],
            'replications': len(bundle['bundleInstallations']),
            'starting': sum([not execution['isStarted'] for execution in bundle['bundleExecutions']]),
            'executions': sum([execution['isStarted'] for execution in bundle['bundleExecutions']])
        } for bundle in json.loads(response.text)
    ]
    data.insert(0, {'id': 'ID', 'name': 'NAME', 'replications': '#REP', 'starting': '#STR', 'executions': '#RUN'})

    padding = 2
    column_widths = dict(calc_column_widths(data), **{'padding': ' ' * padding})
    has_error = False
    for row in data:
        has_error |= '!' in row['id']
        print('''\
{id: <{id_width}}{padding}\
{name: <{name_width}}{padding}\
{replications: >{replications_width}}{padding}\
{starting: >{starting_width}}{padding}\
{executions: >{executions_width}}'''.format(**dict(row, **column_widths)))

    if has_error:
        print('There are errors: use `conduct events` or `conduct logs` for further information')


def calc_column_widths(data):
    column_widths = {}
    for row in data:
        for column, value in row.items():
            column_len = len(str(value))
            width_key = column + '_width'
            if column_len > column_widths.get(width_key, 0):
                column_widths[width_key] = column_len
    return column_widths
