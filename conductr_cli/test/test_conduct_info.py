from conductr_cli.test.cli_test_case import CliTestCase, strip_margin
from conductr_cli import conduct_info, logging_setup
from conductr_cli.http import DEFAULT_HTTP_TIMEOUT
from unittest.mock import patch, MagicMock


class TestConductInfoCommand(CliTestCase):

    conductr_auth = ('username', 'password')
    server_verification_file = MagicMock(name='server_verification_file')

    default_args = {
        'dcos_mode': False,
        'scheme': 'http',
        'host': '127.0.0.1',
        'port': 9005,
        'base_path': '/',
        'api_version': '1',
        'verbose': False,
        'quiet': False,
        'long_ids': False,
        'conductr_auth': conductr_auth,
        'server_verification_file': server_verification_file
    }

    default_url = 'http://127.0.0.1:9005/bundles'

    license = {
        'user': 'cc64df31-ec6b-4e08-bb6b-3216721a56b@lightbend',
        'maxConductrAgents': 3,
        'conductrVersions': ['2.1.*'],
        'grants': ['akka-sbr', 'cinnamon', 'conductr'],
    }

    def test_no_bundles(self):
        mock_get_license = MagicMock(return_value=self.license)
        http_method = self.respond_with(text='[]')
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.license.get_license', mock_get_license):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_info.info(input_args)
            self.assertTrue(result)

        mock_get_license.assert_called_once_with(input_args)
        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})
        self.assertEqual(
            strip_margin("""|
                            |Licensed To: cc64df31-ec6b-4e08-bb6b-3216721a56b@lightbend
                            |Max ConductR agents: 3
                            |ConductR Version(s): 2.1.*
                            |Grants: akka-sbr, cinnamon, conductr
                            |
                            |ID  NAME  #REP  #STR  #RUN
                            |"""),
            self.output(stdout))

    def test_no_bundles_without_license(self):
        mock_get_license = MagicMock(return_value=None)
        http_method = self.respond_with(text='[]')
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.license.get_license', mock_get_license):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_info.info(input_args)
            self.assertTrue(result)

        mock_get_license.assert_called_once_with(input_args)
        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})
        self.assertEqual(
            strip_margin("""|
                            |UNLICENSED - please use "conduct load-license" to use more than one agent. Additional agents are freely available for registered users.
                            |Max ConductR agents: 1
                            |Grants: conductr, cinnamon, akka-sbr
                            |
                            |ID  NAME  #REP  #STR  #RUN
                            |"""),
            self.output(stdout))

    def test_no_bundles_quiet(self):
        mock_get_license = MagicMock(return_value=self.license)
        http_method = self.respond_with(text='[]')
        stdout = MagicMock()

        args = self.default_args.copy()
        args.update({'quiet': True})
        input_args = MagicMock(**args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.license.get_license', mock_get_license):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_info.info(input_args)
            self.assertTrue(result)

        mock_get_license.assert_not_called()
        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})
        self.assertEqual('', self.output(stdout))

    def test_stopped_bundle(self):
        mock_get_license = MagicMock(return_value=self.license)
        http_method = self.respond_with(text="""[
            {
                "attributes": { "bundleName": "test-bundle" },
                "bundleId": "45e0c477d3e5ea92aa8d85c0d8f3e25c",
                "bundleExecutions": [],
                "bundleInstallations": [1]
            }
        ]""")
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.license.get_license', mock_get_license):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_info.info(input_args)
            self.assertTrue(result)

        mock_get_license.assert_called_once_with(input_args)
        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})
        self.assertEqual(
            strip_margin("""|
                            |Licensed To: cc64df31-ec6b-4e08-bb6b-3216721a56b@lightbend
                            |Max ConductR agents: 3
                            |ConductR Version(s): 2.1.*
                            |Grants: akka-sbr, cinnamon, conductr
                            |
                            |ID       NAME         #REP  #STR  #RUN
                            |45e0c47  test-bundle     1     0     0
                            |"""),
            self.output(stdout))

    def test_one_running_one_starting_one_stopped(self):
        mock_get_license = MagicMock(return_value=self.license)
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

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.license.get_license', mock_get_license):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_info.info(input_args)
            self.assertTrue(result)

        mock_get_license.assert_called_once_with(input_args)
        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})
        self.assertEqual(
            strip_margin("""|
                            |Licensed To: cc64df31-ec6b-4e08-bb6b-3216721a56b@lightbend
                            |Max ConductR agents: 3
                            |ConductR Version(s): 2.1.*
                            |Grants: akka-sbr, cinnamon, conductr
                            |
                            |ID               NAME           #REP  #STR  #RUN
                            |45e0c47          test-bundle-1     1     0     1
                            |45e0c47-c52e3f8  test-bundle-2     1     1     0
                            |45e0c47          test-bundle-3     1     0     0
                            |"""),
            self.output(stdout))

    def test_one_running_one_starting_one_stopped_quiet(self):
        mock_get_license = MagicMock(return_value=self.license)
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

        args = self.default_args.copy()
        args.update({'quiet': True})
        input_args = MagicMock(**args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.license.get_license', mock_get_license):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_info.info(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})
        self.assertEqual(
            strip_margin("""|45e0c47
                            |45e0c47-c52e3f8
                            |45e0c47
                            |"""),
            self.output(stdout))

    def test_one_running_one_stopped_verbose(self):
        mock_get_license = MagicMock(return_value=self.license)
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

        args = self.default_args.copy()
        args.update({'verbose': True})
        input_args = MagicMock(**args)

        with patch('requests.get', http_method), \
                patch('conductr_cli.license.get_license', mock_get_license):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_info.info(input_args)
            self.assertTrue(result)

        mock_get_license.assert_called_once_with(input_args)
        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})

        self.maxDiff = None
        self.assertEqual(
            strip_margin("""|[
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
                            |
                            |Licensed To: cc64df31-ec6b-4e08-bb6b-3216721a56b@lightbend
                            |Max ConductR agents: 3
                            |ConductR Version(s): 2.1.*
                            |Grants: akka-sbr, cinnamon, conductr
                            |
                            |ID       NAME           #REP  #STR  #RUN
                            |45e0c47  test-bundle-1     3     0     3
                            |c52e3f8  test-bundle-2     3     0     0
                            |"""),
            self.output(stdout))

    def test_long_ids(self):
        mock_get_license = MagicMock(return_value=self.license)
        http_method = self.respond_with(text="""[
            {
                "attributes": { "bundleName": "test-bundle" },
                "bundleId": "45e0c477d3e5ea92aa8d85c0d8f3e25c",
                "bundleExecutions": [],
                "bundleInstallations": [1]
            }
        ]""")
        stdout = MagicMock()

        args = self.default_args.copy()
        args.update({'long_ids': True})
        input_args = MagicMock(**args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.license.get_license', mock_get_license):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_info.info(input_args)
            self.assertTrue(result)

        mock_get_license.assert_called_once_with(input_args)
        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})
        self.assertEqual(
            strip_margin("""|
                            |Licensed To: cc64df31-ec6b-4e08-bb6b-3216721a56b@lightbend
                            |Max ConductR agents: 3
                            |ConductR Version(s): 2.1.*
                            |Grants: akka-sbr, cinnamon, conductr
                            |
                            |ID                                NAME         #REP  #STR  #RUN
                            |45e0c477d3e5ea92aa8d85c0d8f3e25c  test-bundle     1     0     0
                            |"""),
            self.output(stdout))

    def test_long_ids_quiet(self):
        mock_get_license = MagicMock(return_value=self.license)
        http_method = self.respond_with(text="""[
            {
                "attributes": { "bundleName": "test-bundle" },
                "bundleId": "45e0c477d3e5ea92aa8d85c0d8f3e25c",
                "bundleExecutions": [],
                "bundleInstallations": [1]
            }
        ]""")
        stdout = MagicMock()

        args = self.default_args.copy()
        args.update({
            'long_ids': True,
            'quiet': True
        })
        input_args = MagicMock(**args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.license.get_license', mock_get_license):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_info.info(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})
        self.assertEqual(
            strip_margin("""|45e0c477d3e5ea92aa8d85c0d8f3e25c
                            |"""),
            self.output(stdout))

    def test_double_digits(self):
        mock_get_license = MagicMock(return_value=self.license)
        http_method = self.respond_with(text="""[
            {
                "attributes": { "bundleName": "test-bundle" },
                "bundleId": "45e0c477d3e5ea92aa8d85c0d8f3e25c",
                "bundleExecutions": [],
                "bundleInstallations": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            }
        ]""")
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.license.get_license', mock_get_license):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_info.info(input_args)
            self.assertTrue(result)

        mock_get_license.assert_called_once_with(input_args)
        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})
        self.assertEqual(
            strip_margin("""|
                            |Licensed To: cc64df31-ec6b-4e08-bb6b-3216721a56b@lightbend
                            |Max ConductR agents: 3
                            |ConductR Version(s): 2.1.*
                            |Grants: akka-sbr, cinnamon, conductr
                            |
                            |ID       NAME         #REP  #STR  #RUN
                            |45e0c47  test-bundle    10     0     0
                            |"""),
            self.output(stdout))

    def test_has_error(self):
        mock_get_license = MagicMock(return_value=self.license)
        http_method = self.respond_with(text="""[
            {
                "attributes": { "bundleName": "test-bundle" },
                "bundleId": "45e0c477d3e5ea92aa8d85c0d8f3e25c",
                "bundleExecutions": [],
                "bundleInstallations": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "hasError": true
            }
        ]""")
        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.license.get_license', mock_get_license):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_info.info(input_args)
            self.assertTrue(result)

        mock_get_license.assert_called_once_with(input_args)
        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})
        self.assertEqual(
            strip_margin("""|
                            |Licensed To: cc64df31-ec6b-4e08-bb6b-3216721a56b@lightbend
                            |Max ConductR agents: 3
                            |ConductR Version(s): 2.1.*
                            |Grants: akka-sbr, cinnamon, conductr
                            |
                            |ID         NAME         #REP  #STR  #RUN
                            |! 45e0c47  test-bundle    10     0     0
                            |There are errors: use `conduct events` or `conduct logs` for further information
                            |"""),
            self.output(stdout))

    def test_has_error_quiet(self):
        mock_get_license = MagicMock(return_value=self.license)
        http_method = self.respond_with(text="""[
            {
                "attributes": { "bundleName": "test-bundle" },
                "bundleId": "45e0c477d3e5ea92aa8d85c0d8f3e25c",
                "bundleExecutions": [],
                "bundleInstallations": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "hasError": true
            }
        ]""")
        stdout = MagicMock()

        args = self.default_args.copy()
        args.pop('quiet', True)
        input_args = MagicMock(**args)

        with patch('requests.get', http_method), \
                patch('conductr_cli.license.get_license', mock_get_license):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_info.info(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})
        self.assertEqual(
            strip_margin("""|! 45e0c47
                            |"""),
            self.output(stdout))

    def test_failure_invalid_address(self):
        mock_get_license = MagicMock(return_value=self.license)
        http_method = self.raise_connection_error('test reason', self.default_url)
        stderr = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.license.get_license', mock_get_license):
            logging_setup.configure_logging(input_args, err_output=stderr)
            result = conduct_info.info(input_args)
            self.assertFalse(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})
        self.assertEqual(
            self.default_connection_error.format(self.default_url),
            self.output(stderr))

    def test_ip(self):
        mock_get_license = MagicMock(return_value=self.license)

        args = {}
        args.update(self.default_args)
        args.pop('host')
        args.update({'ip': '10.0.0.1'})

        default_url = 'http://10.0.0.1:9005/bundles'

        http_method = self.respond_with(text='[]')
        stdout = MagicMock()

        input_args = MagicMock(**args)
        with patch('requests.get', http_method), \
                patch('conductr_cli.license.get_license', mock_get_license):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_info.info(input_args)
            self.assertTrue(result)

        mock_get_license.assert_called_once_with(input_args)
        http_method.assert_called_with(default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '10.0.0.1'})
        self.assertEqual(
            strip_margin("""|
                            |Licensed To: cc64df31-ec6b-4e08-bb6b-3216721a56b@lightbend
                            |Max ConductR agents: 3
                            |ConductR Version(s): 2.1.*
                            |Grants: akka-sbr, cinnamon, conductr
                            |
                            |ID  NAME  #REP  #STR  #RUN
                            |"""),
            self.output(stdout))
