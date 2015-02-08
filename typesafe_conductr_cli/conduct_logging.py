import json
import sys
from requests.exceptions import ConnectionError, HTTPError


# print to stderr
def error(message, *objs):
    print('ERROR: {}'.format(message.format(*objs)), file=sys.stderr)


def warning(message, *objs):
    print('WARNING: {}'.format(message.format(*objs)), file=sys.stdout)


def connection_error(err, args):
    error('Unable to contact Typesafe ConductR.')
    error('Reason: {}'.format(err.args[0]))
    error('Make sure it can be accessed at {}:{}.'.format(args[0].ip, args[0].port))


def handle_connection_error(func):
    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ConnectionError as err:
            connection_error(err, args)

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_http_error(func):
    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HTTPError as err:
            error('{} {}', err.response.status_code, err.response.reason)
            if err.response.text != '':
                error(err.response.text)

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def pretty_json(s):
    s_json = json.loads(s)
    print(json.dumps(s_json, sort_keys=True, indent=2))
