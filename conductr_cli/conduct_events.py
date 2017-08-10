import logging

from conductr_cli import validation, screen_utils, control_protocol


@validation.handle_connection_error
@validation.handle_http_error
def events(args):
    """`conduct events` command"""

    log = logging.getLogger(__name__)
    bundle_events = control_protocol.get_bundle_events(args, args.lines)
    data = [
        {
            'time': validation.format_timestamp(event['timestamp'], args),
            'event': event['event'],
            'description': event['description']
        } for event in bundle_events
    ]
    data.insert(0, {'time': 'TIME', 'event': 'EVENT', 'description': 'DESC'})

    padding = 2
    column_widths = dict(screen_utils.calc_column_widths(data), **{'padding': ' ' * padding})

    for row in data:
        log.screen('''\
{time: <{time_width}}{padding}\
{event: <{event_width}}{padding}\
{description: <{description_width}}{padding}'''.format(**dict(row, **column_widths)).rstrip())

    return True
