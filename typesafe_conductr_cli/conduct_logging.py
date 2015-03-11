import json
import sys
from pyhocon.exceptions import ConfigException
from requests import status_codes
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


def pretty_json(s):
    s_json = json.loads(s)
    print(json.dumps(s_json, sort_keys=True, indent=2))


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


def handle_invalid_config(func):
    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ConfigException as err:
            error('Unable to parse bundle.conf.')
            error('{}.', err.args[0])

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_no_file(func):
    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as err:
            error('File not found: {}', err.args[0])

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def raise_for_status_inc_3xx(response):
    """
    raise status when status code is 3xx
    """

    response.raise_for_status()
    if response.status_code >= 300:
        raise HTTPError(status_codes._codes[response.status_code], response=response)
