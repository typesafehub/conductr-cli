from conductr_cli import validation, conduct_request, conduct_url, screen_utils
from conductr_cli.conduct_url import conductr_host
import json
import logging
from conductr_cli.http import DEFAULT_HTTP_TIMEOUT


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

    data = [
        {
            'address': 'ADDRESS',
            'roles': 'ROLES',
            'observed': 'OBSERVED BY'
        }
    ]

    for entry in raw_data:
        if args.role is None or args.role in entry['roles']:
            data.append({
                'address': entry['address'],
                'roles': ','.join(entry['roles']),
                'observed': ','.join(map(lambda e: e['node']['address'], entry['observedBy']))
            })

    padding = 2
    column_widths = dict(screen_utils.calc_column_widths(data), **{'padding': ' ' * padding})

    for row in data:
        log.screen('''\
{address: <{address_width}}{padding}\
{roles: <{roles_width}}{padding}\
{observed: >{observed_width}}{padding}'''.format(**dict(row, **column_widths)).rstrip())

    return True
