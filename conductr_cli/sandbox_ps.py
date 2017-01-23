from conductr_cli import sandbox_common, screen_utils
import logging


def ps(args):
    log = logging.getLogger(__name__)
    core_info, agent_info = sandbox_common.resolve_conductr_info(args.image_dir)
    pids_info = sandbox_common.find_pids(core_info['extraction_dir'], agent_info['extraction_dir'])

    if args.is_filter_core:
        data = [pid_info for pid_info in pids_info if pid_info['type'] == 'core']
    elif args.is_filter_agent:
        data = [pid_info for pid_info in pids_info if pid_info['type'] == 'agent']
    else:
        data = [pid_info for pid_info in pids_info]

    if args.is_quiet:
        for row in data:
            log.info(row['id'])
    else:
        data.insert(0, {'id': 'PID', 'type': 'TYPE', 'ip': 'IP'})
        padding = 2
        column_widths = dict(screen_utils.calc_column_widths(data), **{'padding': ' ' * padding})
        for row in data:
            log.screen('''\
{id: <{id_width}}{padding}\
{type: >{type_width}}{padding}\
{ip: >{ip_width}}'''.format(**dict(row, **column_widths)).rstrip())

    return True
