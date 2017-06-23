from conductr_cli import validation, conduct_request, conduct_url, screen_utils
from conductr_cli.conduct_url import conductr_host
from conductr_cli.bytes_util import natural_size
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
