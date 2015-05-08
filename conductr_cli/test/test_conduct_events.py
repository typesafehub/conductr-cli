from unittest import TestCase
from conductr_cli.test.cli_test_case import CliTestCase, strip_margin
from conductr_cli import conduct_events

try:
    from unittest.mock import patch, MagicMock  # 3.3 and beyond
except ImportError:
    from mock import patch, MagicMock


class TestConductEventsCommand(TestCase, CliTestCase):

    default_args = {
        'service': 'http://127.0.0.1:9210',
        'bundle': 'ab8f513'
    }

    default_url = 'http://127.0.0.1:9210/events/ab8f513'

    def test_no_events(self):
        http_method = self.respond_with(text='{}')
        stdout = MagicMock()

        with patch('requests.get', http_method), patch('sys.stdout', stdout):
            conduct_events.events(MagicMock(**self.default_args))

        http_method.assert_called_with(self.default_url)
        self.assertEqual(
            strip_margin("""|TIME  EVENT  DESC
                            |"""),
            self.output(stdout))

    def test_multiple_events(self):
        http_method = self.respond_with(text="""[
            {
                "@cee": {
                    "head": {
                        "contentType": "conductr.loadScheduler.loadBundleRequested"
                    },
                    "body": {
                        "time": "Today 12:54:30",
                        "requestId": "req123",
                        "bundleName": "bundle-name",
                        "message": "Load bundle requested: requestId=req123, bundleName=bundle-name"
                    },
                    "tag": "conductr.loadScheduler.loadBundleRequested"
                }
            },
            {
                "@cee": {
                    "head": {
                        "contentType": "conductr.loadExecutor.bundleWritten"
                    },
                    "body": {
                        "time": "Today 12:54:36",
                        "requestId": "req123",
                        "bundleName": "bundle-name",
                        "message": "Bundle written: requestId=req123, bundleName=bundle-name"
                    },
                    "tag": "conductr.loadExecutor.bundleWritten"
                }
            }
        ]""")
        stdout = MagicMock()

        with patch('requests.get', http_method), patch('sys.stdout', stdout):
            conduct_events.events(MagicMock(**self.default_args))

        http_method.assert_called_with(self.default_url)
        self.assertEqual(
            strip_margin("""|TIME            EVENT                                       DESC
                            |Today 12:54:30  conductr.loadScheduler.loadBundleRequested  Load bundle requested: requestId=req123, bundleName=bundle-name
                            |Today 12:54:36  conductr.loadExecutor.bundleWritten         Bundle written: requestId=req123, bundleName=bundle-name
                            |"""),
            self.output(stdout))

    def test_failure_invalid_address(self):
        http_method = self.raise_connection_error('test reason', self.default_url)
        stderr = MagicMock()

        with patch('requests.get', http_method), patch('sys.stderr', stderr):
            conduct_events.events(MagicMock(**self.default_args))

        http_method.assert_called_with(self.default_url)
        self.assertEqual(
            self.default_connection_error.format(self.default_url),
            self.output(stderr))
