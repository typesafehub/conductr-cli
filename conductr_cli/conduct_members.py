from conductr_cli import validation, screen_utils
import logging

from conductr_cli.control_protocol import get_members


@validation.handle_connection_error
@validation.handle_http_error
def members(args):
    """`conduct members` command"""

    log = logging.getLogger(__name__)

    raw_data = get_members(args)

    data = [
        {
            'address': 'ADDRESS',
            'uid': 'UID',
            'roles': 'ROLES',
            'status': 'STATUS',
            'reachable': 'REACHABLE'
        }
    ]

    unreachable_nodes = []

    for entry in raw_data['unreachable']:
        unreachable_nodes.append(entry['node'])

    for entry in raw_data['members']:
        if args.role is None or args.role in entry['roles']:
            data.append({
                'address': entry['node']['address'],
                'uid': entry['node']['uid'],
                'roles': ','.join(entry['roles']),
                'status': entry['status'],
                'reachable': 'Yes' if entry['node'] not in unreachable_nodes else 'No'
            })

    padding = 2
    column_widths = dict(screen_utils.calc_column_widths(data), **{'padding': ' ' * padding})

    for row in data:
        log.screen('''\
{uid: <{uid_width}}{padding}\
{address: <{address_width}}{padding}\
{roles: <{roles_width}}{padding}\
{status: <{status_width}}{padding}\
{reachable: >{reachable_width}}'''.format(**dict(row, **column_widths)).rstrip())

    return True
