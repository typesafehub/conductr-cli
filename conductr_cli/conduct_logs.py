from conductr_cli import validation, conduct_request, conduct_url, screen_utils
from conductr_cli.conduct_url import conductr_host
from conductr_cli.constants import LOGS_FOLLOW_ERROR_SLEEP_SECONDS, LOGS_FOLLOW_SLEEP_SECONDS
from conductr_cli.http import DEFAULT_HTTP_TIMEOUT
from urllib.parse import quote_plus
import itertools
import json
import logging
import time


@validation.handle_connection_error
@validation.handle_http_error
def logs(args):
    """`conduct logs` command"""

    log = logging.getLogger(__name__)

    if args.follow:
        old_data = []

        # we infinite-loop which will run the program until we receive a signal (e.g. CTRL-C)
        # by using itertools.count(), we can control the number of executions for testing via mocks
        for _ in itertools.count():
            data = fetch_log_data_ignore_errors(args)

            if data is False:
                time.sleep(LOGS_FOLLOW_ERROR_SLEEP_SECONDS)
            else:
                new_data, truncated = new_lines(old_data, data)

                if truncated:
                    log.warning('Unable to reconcile logs; some lines may not be shown')

                for row in new_data:
                    log.screen('{0} {1} {2}'.format(row['time'], row['host'], row['log'].rstrip()))

                if len(new_data) > 0:
                    old_data = data

                time.sleep(LOGS_FOLLOW_SLEEP_SECONDS)
    else:
        data = fetch_log_data(args)
        data.insert(0, {'time': 'TIME', 'host': 'HOST', 'log': 'LOG'})

        padding = 2
        column_widths = dict(screen_utils.calc_column_widths(data), **{'padding': ' ' * padding})

        for row in data:
            log.screen('''\
{time: <{time_width}}{padding}\
{host: <{host_width}}{padding}\
{log: <{log_width}}{padding}'''.format(**dict(row, **column_widths)).rstrip())

    return True


def fetch_log_data(args):
    log = logging.getLogger(__name__)

    request_url = conduct_url.url('bundles/{}/logs?count={}'.format(quote_plus(args.bundle), args.lines), args)

    response = conduct_request.get(args.dcos_mode, conductr_host(args), request_url, auth=args.conductr_auth,
                                   verify=args.server_verification_file, timeout=DEFAULT_HTTP_TIMEOUT)

    if log.is_verbose_enabled():
        log.verbose(response.text)

    validation.raise_for_status_inc_3xx(response)

    return [
        {
            'time': validation.format_timestamp(event['timestamp'], args),
            'host': event['host'],
            'log': event['message']
        } for event in json.loads(response.text)
    ]


@validation.handle_connection_error
@validation.handle_http_error
def fetch_log_data_ignore_errors(args):
    return fetch_log_data(args)


def new_lines(old, new):
    """
    Given a list of lines that were last printed and the latest fetched, returns the unique lines
    and whether we may have lost any lines.

    :param old: list of old lines
    :param new: list of new lines
    :return: (new lines, True if logs may have been lost, False if not)
    """
    i = len(old) - 1
    answer = new, len(old) > 0 and len(new) > 0

    while i >= 0:
        new_index = len(old) - i

        if old[i:] == new[0:new_index]:
            answer = (new[new_index:], False)

        i -= 1

    return answer
