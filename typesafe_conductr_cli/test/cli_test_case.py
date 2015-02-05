import os
from unittest.mock import MagicMock
from requests.exceptions import ConnectionError, HTTPError


class CliTestCase():
    """Provides test case common functionality"""

    @property
    def default_connection_error(self):
        return self.strip_margin("""|ERROR: Unable to contact Typesafe ConductR.
                                    |ERROR: Reason: test reason
                                    |ERROR: Make sure it can be accessed at {}:{}.
                                    |""")

    def respond_with(self, status_code=200, text=''):
        reasons = {
            200: 'OK',
            404: 'Not Found'
        }

        response_mock = MagicMock(
            status_code=status_code,
            text=text,
            reason=reasons[status_code])

        if status_code == 200:
            response_mock.raise_for_status.return_value = None
        else:
            response_mock.raise_for_status.side_effect = HTTPError(response=response_mock)

        http_method = MagicMock(return_value=response_mock)

        return http_method

    def respond_with_file_contents(self, filepath):
        with open(os.path.join(os.path.dirname(__file__), filepath), 'r') as content_file:
            return self.respond_with(text=content_file.read())

    def raise_connection_error(self, reason):
        return MagicMock(side_effect=ConnectionError(reason))

    def output(self, logger):
        return ''.join([args[0].rstrip(' ') for name, args, kwargs in logger.method_calls])

    def strip_margin(self, string, marginChar='|'):
        return '\n'.join([line[line.index(marginChar) + 1:] for line in string.split('\n')])
