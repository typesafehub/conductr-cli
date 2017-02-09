from conductr_cli import validation, conduct_request, conduct_url, screen_utils
from conductr_cli.conduct_url import conductr_host
import json
import logging
from conductr_cli.http import DEFAULT_HTTP_TIMEOUT


def calculate_row(entry):
    return {
        'address': entry['address'],
        'roles': ','.join(entry['roles'])
    }


def calculate_rows(args, raw_data):
    data = [
        {
            'address': 'ADDRESS',
            'roles': 'ROLES'
        }
    ]

    for entry in raw_data:
        if include_entry(args, entry):
            data.append(calculate_row(entry))

    return data


def format_rows(rows):
    padding = 2
    column_widths = dict(screen_utils.calc_column_widths(rows), **{'padding': ' ' * padding})

    formatted = []

    for row in rows:
        formatted.append('''\
{address: <{address_width}}{padding}\
{roles: >{roles_width}}{padding}'''.format(**dict(row, **column_widths)).rstrip())

    return formatted


def include_entry(args, entry):
    return args.role is None or args.role in entry['roles']


@validation.handle_connection_error
@validation.handle_http_error
def agents(args):
    """`conduct agents` command"""

    log = logging.getLogger(__name__)

    request_url = conduct_url.url('agents', args)
    response = conduct_request.get(args.dcos_mode, conductr_host(args), request_url, auth=args.conductr_auth,
                                   verify=args.server_verification_file, timeout=DEFAULT_HTTP_TIMEOUT)

    validation.raise_for_status_inc_3xx(response)

    if log.is_verbose_enabled():
        log.verbose(validation.pretty_json(response.text))

    raw_data = json.loads(response.text)

    rows = calculate_rows(args, raw_data)
    formatted_rows = format_rows(rows)

    for line in formatted_rows:
        log.screen(line)

    return True
