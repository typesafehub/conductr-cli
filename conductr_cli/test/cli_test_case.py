import os
import shutil
import tempfile
from unittest import TestCase
from requests.exceptions import ConnectionError, HTTPError, ReadTimeout
from conductr_cli.ansi_colors import RED, YELLOW, UNDERLINE, ENDC
from unittest.mock import MagicMock


class CliTestCase(TestCase):
    """Provides test case common functionality"""

    @property
    def default_connection_error(self):
        return as_error(strip_margin("""|Error: Unable to contact ConductR.
                               |Error: Reason: test reason
                               |Error: Start the ConductR sandbox with: sandbox run IMAGE_VERSION
                               |"""))

    @staticmethod
    def respond_with(status_code=200, text='', content_type=None):
        reasons = {
            200: 'OK',
            401: 'Unauthorized',
            403: 'Forbidden',
            404: 'Not Found',
            500: 'Error',
            503: 'Service unavailable'
        }

        args = {
            'status_code': status_code,
            'text': text,
            'reason': reasons[status_code]
        }
        if content_type:
            args.update({
                'headers': {
                    'Content-Type': content_type
                }
            })
        response_mock = MagicMock(**args)

        if status_code == 200:
            response_mock.raise_for_status.return_value = None
        else:
            response_mock.raise_for_status.side_effect = HTTPError(response=response_mock)

        http_method = MagicMock(return_value=response_mock)

        return http_method

    def respond_with_file_contents(self, filepath):
        with open(os.path.join(os.path.dirname(__file__), filepath), 'r') as content_file:
            return self.respond_with(text=content_file.read())

    @staticmethod
    def raise_connection_error(reason, url):
        return MagicMock(side_effect=ConnectionError(reason, request=MagicMock(url=url)))

    @staticmethod
    def raise_read_timeout_error(reason, url):
        return MagicMock(side_effect=ReadTimeout(reason, request=MagicMock(url=url)))

    @staticmethod
    def output(logger):
        return ''.join([args[0] for name, args, kwargs in logger.method_calls if len(args) > 0])

    @staticmethod
    def output_bytes(logger):
        out = []

        for name, args, kwargs in logger.method_calls:
            if len(args) > 0:
                out.extend(args[0])

        return bytes(out)


def strip_margin(string, margin_char='|'):
    return '\n'.join([line[line.find(margin_char) + 1:] for line in string.split('\n')])


def as_error(string):
    return string.replace('Error:', '{red}{underline}Error{end}:'.format(red=RED, underline=UNDERLINE, end=ENDC))


def as_warn(string):
    return string.replace('Warning:', '{yellow}{underline}Warning{end}:'.format(yellow=YELLOW, underline=UNDERLINE, end=ENDC))


def create_temp_bundle_with_contents(contents):
    tmpdir = tempfile.mkdtemp()

    unpacked = os.path.join(tmpdir, 'unpacked')
    os.makedirs(unpacked)
    basedir = os.path.join(unpacked, 'bundle-1.0.0')
    os.makedirs(basedir)

    for name, content in contents.items():
        file_name = os.path.join(basedir, name)
        dir_name = os.path.dirname(file_name)
        os.makedirs(dir_name, exist_ok=True)
        with open(file_name, 'w', encoding="utf-8") as file:
            file.write(content)

    return tmpdir, shutil.make_archive(os.path.join(tmpdir, 'bundle'), 'zip', unpacked, 'bundle-1.0.0')


def create_attributes_object(obj):
    class Empty(object):
        pass

    ins = Empty()

    for key in obj:
        setattr(ins, key, obj[key])

    return ins


def create_temp_bundle(bundle_conf):
    return create_temp_bundle_with_contents({'bundle.conf': bundle_conf, 'password.txt': 'monkey'})


def create_mock_logger():
    log_mock = MagicMock()
    log_mock.debug = MagicMock()
    log_mock.verbose = MagicMock()
    log_mock.info = MagicMock()
    log_mock.quiet = MagicMock()
    log_mock.warn = MagicMock()
    log_mock.error = MagicMock()

    get_logger_mock = MagicMock(return_value=log_mock)

    return get_logger_mock, log_mock
