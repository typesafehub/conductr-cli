from conductr_cli import validation, screen_utils
from conductr_cli.bytes_util import natural_size
import logging

from conductr_cli.control_protocol import get_agents


@validation.handle_connection_error
@validation.handle_http_error
def agents(args):
    """`conduct agents` command"""

    log = logging.getLogger(__name__)

    raw_data = get_agents(args)

    with_resources_columns = any('resourceAvailable' in entry for entry in raw_data)

    data = [
        {
            'address': 'ADDRESS',
            'roles': 'ROLES',
            'observed': 'OBSERVED BY'
        }
    ]
    if with_resources_columns:
        data[0]['disk-space'] = 'DISK'
        data[0]['memory'] = 'MEM'
        data[0]['nr-of-cpus'] = 'CPUS'

    for entry in raw_data:
        if args.role is None or args.role in entry['roles']:
            data.append({
                'address': entry['address'],
                'roles': ','.join(entry['roles']),
                'observed': ','.join(map(lambda e: e['node']['address'], entry['observedBy']))
            })
            if with_resources_columns:
                if 'resourceAvailable' in entry:
                    data[-1]['disk-space'] = natural_size(entry['resourceAvailable']['diskSpace'])
                    data[-1]['memory'] = natural_size(entry['resourceAvailable']['memory'], binary=True)
                    data[-1]['nr-of-cpus'] = entry['resourceAvailable']['nrOfCpus']
                else:
                    data[-1]['disk-space'] = ''
                    data[-1]['memory'] = ''
                    data[-1]['nr-of-cpus'] = ''

    padding = 2
    column_widths = dict(screen_utils.calc_column_widths(data), **{'padding': ' ' * padding})

    for row in data:
        if with_resources_columns:
            log.screen('''\
{address: <{address_width}}{padding}\
{disk-space: >{disk-space_width}}{padding}\
{memory: >{memory_width}}{padding}\
{nr-of-cpus: >{nr-of-cpus_width}}{padding}\
{roles: <{roles_width}}{padding}\
{observed: <{observed_width}}{padding}'''.format(**dict(row, **column_widths)).rstrip())
        else:
            log.screen('''\
{address: <{address_width}}{padding}\
{roles: <{roles_width}}{padding}\
{observed: <{observed_width}}{padding}'''.format(**dict(row, **column_widths)).rstrip())

    return True
