from unittest import TestCase
from unittest.mock import patch, MagicMock
from typesafe_conductr_cli.test.cli_test_case import CliTestCase
from typesafe_conductr_cli import conduct_info


class TestConductInfoCommand(TestCase, CliTestCase):

    default_args = {
        'ip': '127.0.0.1',
        'port': 9005,
        'verbose': False,
        'long_ids': False
    }

    default_url = 'http://127.0.0.1:9005/bundles'

    def test_no_bundles(self):
        http_method = self.respond_with(text='[]')
        stdout = MagicMock()

        with patch('requests.get', http_method), patch('sys.stdout', stdout):
            conduct_info.info(MagicMock(**self.default_args))

        http_method.assert_called_with(self.default_url)
        self.assertEqual(
            self.strip_margin("""|ID  NAME  #REP  #STR  #RUN
                                 |"""),
            self.output(stdout))

    def test_stopped_bundle(self):
        http_method = self.respond_with(text="""[
            {
                "attributes": { "bundleName": "test-bundle" },
                "bundleId": "45e0c477d3e5ea92aa8d85c0d8f3e25c",
                "bundleExecutions": [],
                "bundleInstallations": [1]
            }
        ]""")
        stdout = MagicMock()

        with patch('requests.get', http_method), patch('sys.stdout', stdout):
            conduct_info.info(MagicMock(**self.default_args))

        http_method.assert_called_with(self.default_url)
        self.assertEqual(
            self.strip_margin("""|ID       NAME         #REP  #STR  #RUN
                                 |45e0c47  test-bundle  1     0     0
                                 |"""),
            self.output(stdout))

    def test_one_running_one_starting_one_stopped(self):
        http_method = self.respond_with(text="""[
            {
                "attributes": { "bundleName": "test-bundle-1" },
                "bundleId": "45e0c477d3e5ea92aa8d85c0d8f3e25c",
                "bundleExecutions": [{"isStarted": true}],
                "bundleInstallations": [1]
            },
            {
                "attributes": { "bundleName": "test-bundle-2" },
                "bundleId": "45e0c477d3e5ea92aa8d85c0d8f3e25c-c52e3f8d0c58d8aa29ae5e3d774c0e54",
                "bundleExecutions": [{"isStarted": false}],
                "bundleInstallations": [1]
            },
            {
                "attributes": { "bundleName": "test-bundle-3" },
                "bundleId": "45e0c477d3e5ea92aa8d85c0d8f3e25c",
                "bundleExecutions": [],
                "bundleInstallations": [1]
            }
        ]""")
        stdout = MagicMock()

        with patch('requests.get', http_method), patch('sys.stdout', stdout):
            conduct_info.info(MagicMock(**self.default_args))

        http_method.assert_called_with(self.default_url)
        self.assertEqual(
            self.strip_margin("""|ID               NAME           #REP  #STR  #RUN
                                 |45e0c47          test-bundle-1  1     0     1
                                 |45e0c47-c52e3f8  test-bundle-2  1     1     0
                                 |45e0c47          test-bundle-3  1     0     0
                                 |"""),
            self.output(stdout))

    def test_one_running_one_stopped_verbose(self):
        http_method = self.respond_with(text="""[
            {
                "attributes": { "bundleName": "test-bundle-1" },
                "bundleId": "45e0c477d3e5ea92aa8d85c0d8f3e25c",
                "bundleExecutions": [{"isStarted": true},{"isStarted": true},{"isStarted": true}],
                "bundleInstallations": [1,2,3]
            },
            {
                "attributes": { "bundleName": "test-bundle-2" },
                "bundleId": "c52e3f8d0c58d8aa29ae5e3d774c0e54",
                "bundleExecutions": [],
                "bundleInstallations": [1,2,3]
            }
        ]""")
        stdout = MagicMock()

        with patch('requests.get', http_method), patch('sys.stdout', stdout):
            args = self.default_args.copy()
            args.update({'verbose': True})
            conduct_info.info(MagicMock(**args))

        http_method.assert_called_with(self.default_url)
        self.assertEqual(
            self.strip_margin("""|[
                                 |  {
                                 |    "attributes": {
                                 |      "bundleName": "test-bundle-1"
                                 |    },
                                 |    "bundleExecutions": [
                                 |      {
                                 |        "isStarted": true
                                 |      },
                                 |      {
                                 |        "isStarted": true
                                 |      },
                                 |      {
                                 |        "isStarted": true
                                 |      }
                                 |    ],
                                 |    "bundleId": "45e0c477d3e5ea92aa8d85c0d8f3e25c",
                                 |    "bundleInstallations": [
                                 |      1,
                                 |      2,
                                 |      3
                                 |    ]
                                 |  },
                                 |  {
                                 |    "attributes": {
                                 |      "bundleName": "test-bundle-2"
                                 |    },
                                 |    "bundleExecutions": [],
                                 |    "bundleId": "c52e3f8d0c58d8aa29ae5e3d774c0e54",
                                 |    "bundleInstallations": [
                                 |      1,
                                 |      2,
                                 |      3
                                 |    ]
                                 |  }
                                 |]
                                 |ID       NAME           #REP  #STR  #RUN
                                 |45e0c47  test-bundle-1  3     0     3
                                 |c52e3f8  test-bundle-2  3     0     0
                                 |"""),
            self.output(stdout))

    def test_long_ids(self):
        http_method = self.respond_with(text="""[
            {
                "attributes": { "bundleName": "test-bundle" },
                "bundleId": "45e0c477d3e5ea92aa8d85c0d8f3e25c",
                "bundleExecutions": [],
                "bundleInstallations": [1]
            }
        ]""")
        stdout = MagicMock()

        with patch('requests.get', http_method), patch('sys.stdout', stdout):
            args = self.default_args.copy()
            args.update({'long_ids': True})
            conduct_info.info(MagicMock(**args))

        http_method.assert_called_with(self.default_url)
        self.assertEqual(
            self.strip_margin("""|ID                                NAME         #REP  #STR  #RUN
                                 |45e0c477d3e5ea92aa8d85c0d8f3e25c  test-bundle  1     0     0
                                 |"""),
            self.output(stdout))

    def test_failure_invalid_address(self):
        http_method = self.raise_connection_error('test reason')
        stderr = MagicMock()

        with patch('requests.get', http_method), patch('sys.stderr', stderr):
            conduct_info.info(MagicMock(**self.default_args))

        http_method.assert_called_with(self.default_url)
        self.assertEqual(
            self.default_connection_error.format(self.default_args['ip'], self.default_args['port']),
            self.output(stderr))
