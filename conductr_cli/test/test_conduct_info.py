from conductr_cli.test.cli_test_case import CliTestCase, as_error, strip_margin
from conductr_cli import conduct_info, logging_setup
from conductr_cli.http import DEFAULT_HTTP_TIMEOUT
from unittest.mock import patch, MagicMock
import arrow


class TestConductInfoShowAllBundlesCommand(CliTestCase):

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
        'server_verification_file': server_verification_file,
        'bundle': None
    }

    default_url = 'http://127.0.0.1:9005/bundles'

    license = {
        'user': 'cc64df31-ec6b-4e08-bb6b-3216721a56b@lightbend',
        'maxConductrAgents': 3,
        'conductrVersions': ['2.1.*'],
        'grants': ['akka-sbr', 'cinnamon', 'conductr'],
        'isLicensed': True
    }

    default_license = {
        'user': 'unknown',
        'maxConductrAgents': 1,
        'conductrVersions': ['2.1.*'],
        'grants': ['akka-sbr', 'cinnamon', 'conductr'],
        'isLicensed': False
    }

    def test_no_bundles(self):
        mock_get_license = MagicMock(return_value=(True, self.license))
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
            strip_margin("""|Licensed To: cc64df31-ec6b-4e08-bb6b-3216721a56b@lightbend
                            |Max ConductR agents: 3
                            |ConductR Version(s): 2.1.*
                            |Grants: akka-sbr, cinnamon, conductr
                            |
                            |ID  NAME  TAG  #REP  #STR  #RUN  ROLES
                            |"""),
            self.output(stdout))

    def test_no_bundles_unlicensed(self):
        mock_get_license = MagicMock(return_value=(True, self.default_license))
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
            strip_margin("""|UNLICENSED - please use "conduct load-license" to use more agents. Additional agents are freely available for registered users.
                            |Licensed To: unknown
                            |Max ConductR agents: 1
                            |ConductR Version(s): 2.1.*
                            |Grants: akka-sbr, cinnamon, conductr
                            |
                            |ID  NAME  TAG  #REP  #STR  #RUN  ROLES
                            |"""),
            self.output(stdout))

    def test_no_bundles_no_license_enpoints(self):
        mock_get_license = MagicMock(return_value=(False, None))
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
            strip_margin("""|ID  NAME  TAG  #REP  #STR  #RUN  ROLES
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
        mock_get_license = MagicMock(return_value=(True, self.license))
        http_method = self.respond_with(text="""[
            {
                "attributes": {
                  "bundleName": "test-bundle",
                  "compatibilityVersion": "1",
                  "roles": ["tester"],
                  "tags": ["1.0.0"]
                },
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
            strip_margin("""|Licensed To: cc64df31-ec6b-4e08-bb6b-3216721a56b@lightbend
                            |Max ConductR agents: 3
                            |ConductR Version(s): 2.1.*
                            |Grants: akka-sbr, cinnamon, conductr
                            |
                            |ID       NAME           TAG  #REP  #STR  #RUN  ROLES
                            |45e0c47  test-bundle  1.0.0     1     0     0  tester
                            |"""),
            self.output(stdout))

    def test_one_running_one_starting_one_stopped(self):
        mock_get_license = MagicMock(return_value=(True, self.license))
        http_method = self.respond_with(text="""[
            {
                "attributes": {
                    "bundleName": "test-bundle-1",
                    "compatibilityVersion": "1",
                    "roles": [],
                    "tags": ["1.0.0"]
                },
                "bundleId": "45e0c477d3e5ea92aa8d85c0d8f3e25c",
                "bundleExecutions": [{"isStarted": true}],
                "bundleInstallations": [1]
            },
            {
                "attributes": {
                    "bundleName": "test-bundle-2",
                    "compatibilityVersion": "10",
                    "roles": ["tester", "load-test", "another"],
                    "tags": ["10.0.0"]
                },
                "bundleId": "45e0c477d3e5ea92aa8d85c0d8f3e25c-c52e3f8d0c58d8aa29ae5e3d774c0e54",
                "bundleExecutions": [{"isStarted": false}],
                "bundleInstallations": [1]
            },
            {
                "attributes": {
                    "bundleName": "test-bundle-3",
                    "compatibilityVersion": "8",
                    "roles": ["tester"],
                    "tags": ["8.0.0"]
                },
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
        self.maxDiff = None
        self.assertEqual(
            strip_margin("""|Licensed To: cc64df31-ec6b-4e08-bb6b-3216721a56b@lightbend
                            |Max ConductR agents: 3
                            |ConductR Version(s): 2.1.*
                            |Grants: akka-sbr, cinnamon, conductr
                            |
                            |ID               NAME              TAG  #REP  #STR  #RUN  ROLES
                            |45e0c47          test-bundle-1   1.0.0     1     0     1
                            |45e0c47-c52e3f8  test-bundle-2  10.0.0     1     1     0  another, load-test, tester
                            |45e0c47          test-bundle-3   8.0.0     1     0     0  tester
                            |"""),
            self.output(stdout))

    def test_one_running_one_starting_one_stopped_quiet(self):
        mock_get_license = MagicMock(return_value=(True, self.license))
        http_method = self.respond_with(text="""[
            {
                "attributes": {
                    "bundleName": "test-bundle-1",
                    "compatibilityVersion": "1",
                    "roles": ["test"],
                    "tags": ["1.0.0"]
                },
                "bundleId": "45e0c477d3e5ea92aa8d85c0d8f3e25c",
                "bundleExecutions": [{"isStarted": true}],
                "bundleInstallations": [1]
            },
            {
                "attributes": {
                    "bundleName": "test-bundle-2",
                    "compatibilityVersion": "1",
                    "roles": ["test"],
                    "tags": ["1.0.0"]
                },
                "bundleId": "45e0c477d3e5ea92aa8d85c0d8f3e25c-c52e3f8d0c58d8aa29ae5e3d774c0e54",
                "bundleExecutions": [{"isStarted": false}],
                "bundleInstallations": [1]
            },
            {
                "attributes": {
                    "bundleName": "test-bundle-3",
                    "compatibilityVersion": "1",
                    "roles": ["test"],
                    "tags": ["1.0.0"]
                },
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
        mock_get_license = MagicMock(return_value=(True, self.license))
        http_method = self.respond_with(text="""[
            {
                "attributes": {
                    "bundleName": "test-bundle-1",
                    "compatibilityVersion": "1",
                    "roles": [],
                    "tags": ["1.0.0"]
                },
                "bundleId": "45e0c477d3e5ea92aa8d85c0d8f3e25c",
                "bundleExecutions": [{"isStarted": true},{"isStarted": true},{"isStarted": true}],
                "bundleInstallations": [1,2,3]
            },
            {
                "attributes": {
                    "bundleName": "test-bundle-2",
                    "compatibilityVersion": "1",
                    "roles": ["beta", "load-test"],
                    "tags": ["1.0.0"]
                },
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
                            |      "bundleName": "test-bundle-1",
                            |      "compatibilityVersion": "1",
                            |      "roles": [],
                            |      "tags": [
                            |        "1.0.0"
                            |      ]
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
                            |      "bundleName": "test-bundle-2",
                            |      "compatibilityVersion": "1",
                            |      "roles": [
                            |        "beta",
                            |        "load-test"
                            |      ],
                            |      "tags": [
                            |        "1.0.0"
                            |      ]
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
                            |Licensed To: cc64df31-ec6b-4e08-bb6b-3216721a56b@lightbend
                            |Max ConductR agents: 3
                            |ConductR Version(s): 2.1.*
                            |Grants: akka-sbr, cinnamon, conductr
                            |
                            |ID       NAME             TAG  #REP  #STR  #RUN  ROLES
                            |45e0c47  test-bundle-1  1.0.0     3     0     3
                            |c52e3f8  test-bundle-2  1.0.0     3     0     0  beta, load-test
                            |"""),
            self.output(stdout))

    def test_long_ids(self):
        mock_get_license = MagicMock(return_value=(True, self.license))
        http_method = self.respond_with(text="""[
            {
                "attributes": {
                  "bundleName": "test-bundle",
                  "compatibilityVersion": "1",
                  "tags": ["1.0.0"],
                  "roles": ["front-end", "public-facing", "api"]
                },
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
        self.maxDiff = None
        self.assertEqual(
            strip_margin("""|Licensed To: cc64df31-ec6b-4e08-bb6b-3216721a56b@lightbend
                            |Max ConductR agents: 3
                            |ConductR Version(s): 2.1.*
                            |Grants: akka-sbr, cinnamon, conductr
                            |
                            |ID                                NAME           TAG  #REP  #STR  #RUN  ROLES
                            |45e0c477d3e5ea92aa8d85c0d8f3e25c  test-bundle  1.0.0     1     0     0  api, front-end, public-facing
                            |"""),
            self.output(stdout))

    def test_long_ids_quiet(self):
        mock_get_license = MagicMock(return_value=(True, self.license))
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
        mock_get_license = MagicMock(return_value=(True, self.license))
        http_method = self.respond_with(text="""[
            {
                "attributes": {
                    "bundleName": "test-bundle",
                    "compatibilityVersion": "1",
                    "tags": ["1.0.0"],
                    "roles": ["test"]
                },
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
            strip_margin("""|Licensed To: cc64df31-ec6b-4e08-bb6b-3216721a56b@lightbend
                            |Max ConductR agents: 3
                            |ConductR Version(s): 2.1.*
                            |Grants: akka-sbr, cinnamon, conductr
                            |
                            |ID       NAME           TAG  #REP  #STR  #RUN  ROLES
                            |45e0c47  test-bundle  1.0.0    10     0     0  test
                            |"""),
            self.output(stdout))

    def test_multiple_tags(self):
        mock_get_license = MagicMock(return_value=(True, self.license))
        http_method = self.respond_with(text="""[
            {
                "attributes": {
                  "bundleName": "test-bundle",
                  "compatibilityVersion": "1",
                  "roles": ["tester"],
                  "tags": ["1.0.0", "latest"]
                },
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
            strip_margin("""|Licensed To: cc64df31-ec6b-4e08-bb6b-3216721a56b@lightbend
                            |Max ConductR agents: 3
                            |ConductR Version(s): 2.1.*
                            |Grants: akka-sbr, cinnamon, conductr
                            |
                            |ID       NAME           TAG  #REP  #STR  #RUN  ROLES
                            |45e0c47  test-bundle  1.0.0     1     0     0  tester
                            |"""),
            self.output(stdout))

    def test_empty_tags(self):
        mock_get_license = MagicMock(return_value=(True, self.license))
        http_method = self.respond_with(text="""[
            {
                "attributes": {
                  "bundleName": "test-bundle",
                  "compatibilityVersion": "1",
                  "tags": [],
                  "roles": ["tester"]
                },
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
            strip_margin("""|Licensed To: cc64df31-ec6b-4e08-bb6b-3216721a56b@lightbend
                            |Max ConductR agents: 3
                            |ConductR Version(s): 2.1.*
                            |Grants: akka-sbr, cinnamon, conductr
                            |
                            |ID       NAME         TAG  #REP  #STR  #RUN  ROLES
                            |45e0c47  test-bundle          1     0     0  tester
                            |"""),
            self.output(stdout))

    def test_no_tags(self):
        mock_get_license = MagicMock(return_value=(True, self.license))
        http_method = self.respond_with(text="""[
            {
                "attributes": {
                  "bundleName": "test-bundle",
                  "compatibilityVersion": "1",
                  "roles": ["tester"]
                },
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
            strip_margin("""|Licensed To: cc64df31-ec6b-4e08-bb6b-3216721a56b@lightbend
                            |Max ConductR agents: 3
                            |ConductR Version(s): 2.1.*
                            |Grants: akka-sbr, cinnamon, conductr
                            |
                            |ID       NAME         VER  #REP  #STR  #RUN  ROLES
                            |45e0c47  test-bundle   v1     1     0     0  tester
                            |"""),
            self.output(stdout))

    def test_has_error(self):
        mock_get_license = MagicMock(return_value=(True, self.license))
        http_method = self.respond_with(text="""[
            {
                "attributes": {
                    "bundleName": "test-bundle",
                    "compatibilityVersion": "1",
                    "tags": ["1.0.0"],
                    "roles": ["test"]
                },
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
            strip_margin("""|Licensed To: cc64df31-ec6b-4e08-bb6b-3216721a56b@lightbend
                            |Max ConductR agents: 3
                            |ConductR Version(s): 2.1.*
                            |Grants: akka-sbr, cinnamon, conductr
                            |
                            |ID         NAME           TAG  #REP  #STR  #RUN  ROLES
                            |! 45e0c47  test-bundle  1.0.0    10     0     0  test
                            |There are errors: use `conduct events` or `conduct logs` for further information
                            |"""),
            self.output(stdout))

    def test_has_error_quiet(self):
        mock_get_license = MagicMock(return_value=(True, self.license))
        http_method = self.respond_with(text="""[
            {
                "attributes": {
                    "bundleName": "test-bundle",
                    "compatibilityVersion": "1",
                    "roles": ["test"]
                },
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
        mock_get_license = MagicMock(return_value=(True, self.license))
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
        mock_get_license = MagicMock(return_value=(True, self.license))

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
            strip_margin("""|Licensed To: cc64df31-ec6b-4e08-bb6b-3216721a56b@lightbend
                            |Max ConductR agents: 3
                            |ConductR Version(s): 2.1.*
                            |Grants: akka-sbr, cinnamon, conductr
                            |
                            |ID  NAME  TAG  #REP  #STR  #RUN  ROLES
                            |"""),
            self.output(stdout))


class TestConductInfoInspectBundleCommand(CliTestCase):
    maxDiff = None

    default_url = 'http://127.0.0.1:9005/bundles'

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

    def test_running_bundle_with_http_and_tcp_acls(self):
        http_method = self.respond_with_file_contents('data/conduct_info_inspect/bundle_with_acls.json')
        stdout = MagicMock()
        stderr = MagicMock()
        mock_arrow_now = MagicMock(return_value=arrow.get('2017-04-05T12:15:54.000'))

        args = self.default_args.copy()
        args.update({'bundle': 'path-tester'})
        input_args = MagicMock(**args)

        with patch('requests.get', http_method), \
                patch('arrow.now', mock_arrow_now):
            logging_setup.configure_logging(input_args, stdout, stderr)
            result = conduct_info.info(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})

        expected_result = strip_margin(
            """|BUNDLE ATTRIBUTES
               |-----------------
               |Bundle Id              cb96704
               |Bundle Name            path-tester
               |Compatibility Version  1
               |System                 path-tester
               |System Version         1
               |Tags                   1.0.0
               |Nr of CPUs             0.1
               |Memory                 402653184
               |Disk Space             200000000
               |Roles                  ptester
               |Bundle Digest          cb96704f739ddfa36ddb9fabdfc4259238a5b4d8f3d4bc8f1fd34bdcc8e1bcae
               |Error                  No
               |
               |BUNDLE SCALE
               |------------
               |Nr of Reschedules  0
               |Scale              1
               |
               |BUNDLE INSTALLATIONS
               |--------------------
               |Host    192.168.10.3
               |Bundle  /Users/felixsatyaputra/.conductr/images/tmp/conductr/192.168.10.3/bundles/cb96704f739ddfa36ddb9fabdfc4259238a5b4d8f3d4bc8f1fd34bdcc8e1bcae.zip
               |
               |Host    192.168.10.2
               |Bundle  /Users/felixsatyaputra/.conductr/images/tmp/conductr/192.168.10.2/bundles/cb96704f739ddfa36ddb9fabdfc4259238a5b4d8f3d4bc8f1fd34bdcc8e1bcae.zip
               |
               |Host    192.168.10.1
               |Bundle  /Users/felixsatyaputra/.conductr/images/tmp/conductr/192.168.10.1/bundles/cb96704f739ddfa36ddb9fabdfc4259238a5b4d8f3d4bc8f1fd34bdcc8e1bcae.zip
               |
               |BUNDLE EXECUTIONS
               |-----------------
               |ENDPOINT  HOST          PID  STARTED           UPTIME  BIND_PORT  HOST_PORT
               |ptest     192.168.10.1    0      Yes  2d, 2h, 11m, 4s      10822      10822
               |ptunnel   192.168.10.1    0      Yes  2d, 2h, 11m, 4s      10007      10007
               |
               |HTTP ACLS
               |---------
               |METHOD  PATH                             REWRITE             STATUS
               |GET     ^/fee/(.*)/fi/(.*)/fo/(.*)/fum$  /boom/\\1-\\2-\\3/box  Running
               |GET     ^/boom/(.*)/box$                                     Running
               |GET     ^/bacon                          /burger             Running
               |GET     ^/tree                                               Running
               |GET     /foo                             /baz                Running
               |GET     /baz                                                 Running
               |
               |TCP ACLS
               |--------
               |TCP/PORT  STATUS
               |3303      Running
               |5601      Running
               |12101     Running
               |
               |SERVICE NAMES
               |-------------
               |SERVICE NAME  STATUS
               |path-tester   Running
               |ptunnel       Running
               |
               |""")
        self.assertEqual(expected_result, self.output(stdout))

        self.assertEqual('', self.output(stderr))

    def test_running_bundle_with_service_uris_v1(self):
        http_method = self.respond_with_file_contents('data/conduct_info_inspect/bundle_with_service_uris_v1.json')
        stdout = MagicMock()
        stderr = MagicMock()

        args = self.default_args.copy()
        args.update({'bundle': 'eslite'})
        input_args = MagicMock(**args)

        with patch('requests.get', http_method):
            logging_setup.configure_logging(input_args, stdout, stderr)
            result = conduct_info.info(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})

        self.maxDiff = None
        expected_result = strip_margin(
            """|BUNDLE ATTRIBUTES
               |-----------------
               |Bundle Id      55436ba
               |Bundle Name    eslite
               |System         eslite
               |Nr of CPUs     0.1
               |Memory         33554432
               |Disk Space     200000000
               |Roles          elasticsearch
               |Bundle Digest  55436ba8468dad03313a2bfd6cdd77077a79d8046abb2944c922cfa9e9c5d0b6
               |Error          No
               |
               |BUNDLE SCALE
               |------------
               |Scale  1
               |
               |BUNDLE INSTALLATIONS
               |--------------------
               |Host    172.17.0.2
               |Bundle  /tmp/55436ba8468dad03313a2bfd6cdd77077a79d8046abb2944c922cfa9e9c5d0b6.zip
               |
               |BUNDLE EXECUTIONS
               |-----------------
               |ENDPOINT        HOST            PID  STARTED   UPTIME  BIND_PORT  HOST_PORT
               |akka-remote     172.17.0.2  Unknown      Yes  Unknown      10917      10917
               |elastic-search  172.17.0.2  Unknown      Yes  Unknown      10007      10007
               |
               |SERVICE NAMES
               |-------------
               |SERVICE NAME    STATUS
               |elastic-search  Running
               |
               |""")
        self.assertEqual(expected_result, self.output(stdout))

        self.assertEqual('', self.output(stderr))

    def test_running_bundle_with_service_uris_v2(self):
        http_method = self.respond_with_file_contents('data/conduct_info_inspect/bundle_with_service_uris_v2.json')
        stdout = MagicMock()
        stderr = MagicMock()
        mock_arrow_now = MagicMock(return_value=arrow.get('2017-04-03T12:15:54.000'))

        args = self.default_args.copy()
        args.update({'bundle': 'eslite'})
        input_args = MagicMock(**args)

        with patch('requests.get', http_method), \
                patch('arrow.now', mock_arrow_now):
            logging_setup.configure_logging(input_args, stdout, stderr)
            result = conduct_info.info(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})

        self.maxDiff = None
        expected_result = strip_margin(
            """|BUNDLE ATTRIBUTES
               |-----------------
               |Bundle Id              55436ba
               |Bundle Name            eslite
               |Compatibility Version  1
               |System                 eslite
               |System Version         1
               |Tags                   1.0.0
               |Nr of CPUs             0.1
               |Memory                 33554432
               |Disk Space             200000000
               |Roles                  elasticsearch
               |Bundle Digest          55436ba8468dad03313a2bfd6cdd77077a79d8046abb2944c922cfa9e9c5d0b6
               |Error                  No
               |
               |BUNDLE SCALE
               |------------
               |Scale  1
               |
               |BUNDLE INSTALLATIONS
               |--------------------
               |Host    172.17.0.2
               |Bundle  /tmp/55436ba8468dad03313a2bfd6cdd77077a79d8046abb2944c922cfa9e9c5d0b6.zip
               |
               |BUNDLE EXECUTIONS
               |-----------------
               |ENDPOINT        HOST        PID  STARTED       UPTIME  BIND_PORT  HOST_PORT
               |akka-remote     172.17.0.2    0      Yes  2h, 11m, 4s      10917      10917
               |elastic-search  172.17.0.2    0      Yes  2h, 11m, 4s      10007      10007
               |
               |SERVICE NAMES
               |-------------
               |SERVICE NAME    STATUS
               |elastic-search  Running
               |
               |""")
        self.assertEqual(expected_result, self.output(stdout))

        self.assertEqual('', self.output(stderr))

    def test_find_by_bundle_id(self):
        http_method = self.respond_with_file_contents('data/conduct_info_inspect/bundle_with_acls.json')
        stdout = MagicMock()
        stderr = MagicMock()
        mock_arrow_now = MagicMock(return_value=arrow.get('2017-04-03T12:15:54.000'))

        args = self.default_args.copy()
        args.update({'bundle': 'cb96704'})
        input_args = MagicMock(**args)

        with patch('requests.get', http_method), \
                patch('arrow.now', mock_arrow_now):
            logging_setup.configure_logging(input_args, stdout, stderr)
            result = conduct_info.info(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})

        self.maxDiff = None
        expected_result = strip_margin(
            """|BUNDLE ATTRIBUTES
               |-----------------
               |Bundle Id              cb96704
               |Bundle Name            path-tester
               |Compatibility Version  1
               |System                 path-tester
               |System Version         1
               |Tags                   1.0.0
               |Nr of CPUs             0.1
               |Memory                 402653184
               |Disk Space             200000000
               |Roles                  ptester
               |Bundle Digest          cb96704f739ddfa36ddb9fabdfc4259238a5b4d8f3d4bc8f1fd34bdcc8e1bcae
               |Error                  No
               |
               |BUNDLE SCALE
               |------------
               |Nr of Reschedules  0
               |Scale              1
               |
               |BUNDLE INSTALLATIONS
               |--------------------
               |Host    192.168.10.3
               |Bundle  /Users/felixsatyaputra/.conductr/images/tmp/conductr/192.168.10.3/bundles/cb96704f739ddfa36ddb9fabdfc4259238a5b4d8f3d4bc8f1fd34bdcc8e1bcae.zip
               |
               |Host    192.168.10.2
               |Bundle  /Users/felixsatyaputra/.conductr/images/tmp/conductr/192.168.10.2/bundles/cb96704f739ddfa36ddb9fabdfc4259238a5b4d8f3d4bc8f1fd34bdcc8e1bcae.zip
               |
               |Host    192.168.10.1
               |Bundle  /Users/felixsatyaputra/.conductr/images/tmp/conductr/192.168.10.1/bundles/cb96704f739ddfa36ddb9fabdfc4259238a5b4d8f3d4bc8f1fd34bdcc8e1bcae.zip
               |
               |BUNDLE EXECUTIONS
               |-----------------
               |ENDPOINT  HOST          PID  STARTED       UPTIME  BIND_PORT  HOST_PORT
               |ptest     192.168.10.1    0      Yes  2h, 11m, 4s      10822      10822
               |ptunnel   192.168.10.1    0      Yes  2h, 11m, 4s      10007      10007
               |
               |HTTP ACLS
               |---------
               |METHOD  PATH                             REWRITE             STATUS
               |GET     ^/fee/(.*)/fi/(.*)/fo/(.*)/fum$  /boom/\\1-\\2-\\3/box  Running
               |GET     ^/boom/(.*)/box$                                     Running
               |GET     ^/bacon                          /burger             Running
               |GET     ^/tree                                               Running
               |GET     /foo                             /baz                Running
               |GET     /baz                                                 Running
               |
               |TCP ACLS
               |--------
               |TCP/PORT  STATUS
               |3303      Running
               |5601      Running
               |12101     Running
               |
               |SERVICE NAMES
               |-------------
               |SERVICE NAME  STATUS
               |path-tester   Running
               |ptunnel       Running
               |
               |""")
        self.assertEqual(expected_result, self.output(stdout))

        self.assertEqual('', self.output(stderr))

    def test_find_by_bundle_id_long(self):
        http_method = self.respond_with_file_contents('data/conduct_info_inspect/bundle_with_acls.json')
        stdout = MagicMock()
        stderr = MagicMock()
        mock_arrow_now = MagicMock(return_value=arrow.get('2017-04-03T10:15:54.000'))

        args = self.default_args.copy()
        args.update({
            'bundle': 'cb96704f739ddfa36ddb9fabdfc42592',
            'long_ids': True,
        })
        input_args = MagicMock(**args)

        with patch('requests.get', http_method), \
                patch('arrow.now', mock_arrow_now):
            logging_setup.configure_logging(input_args, stdout, stderr)
            result = conduct_info.info(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})

        self.maxDiff = None
        expected_result = strip_margin(
            """|BUNDLE ATTRIBUTES
               |-----------------
               |Bundle Id              cb96704f739ddfa36ddb9fabdfc42592
               |Bundle Name            path-tester
               |Compatibility Version  1
               |System                 path-tester
               |System Version         1
               |Tags                   1.0.0
               |Nr of CPUs             0.1
               |Memory                 402653184
               |Disk Space             200000000
               |Roles                  ptester
               |Bundle Digest          cb96704f739ddfa36ddb9fabdfc4259238a5b4d8f3d4bc8f1fd34bdcc8e1bcae
               |Error                  No
               |
               |BUNDLE SCALE
               |------------
               |Nr of Reschedules  0
               |Scale              1
               |
               |BUNDLE INSTALLATIONS
               |--------------------
               |Host    192.168.10.3
               |Bundle  /Users/felixsatyaputra/.conductr/images/tmp/conductr/192.168.10.3/bundles/cb96704f739ddfa36ddb9fabdfc4259238a5b4d8f3d4bc8f1fd34bdcc8e1bcae.zip
               |
               |Host    192.168.10.2
               |Bundle  /Users/felixsatyaputra/.conductr/images/tmp/conductr/192.168.10.2/bundles/cb96704f739ddfa36ddb9fabdfc4259238a5b4d8f3d4bc8f1fd34bdcc8e1bcae.zip
               |
               |Host    192.168.10.1
               |Bundle  /Users/felixsatyaputra/.conductr/images/tmp/conductr/192.168.10.1/bundles/cb96704f739ddfa36ddb9fabdfc4259238a5b4d8f3d4bc8f1fd34bdcc8e1bcae.zip
               |
               |BUNDLE EXECUTIONS
               |-----------------
               |ENDPOINT  HOST          PID  STARTED   UPTIME  BIND_PORT  HOST_PORT
               |ptest     192.168.10.1    0      Yes  11m, 4s      10822      10822
               |ptunnel   192.168.10.1    0      Yes  11m, 4s      10007      10007
               |
               |HTTP ACLS
               |---------
               |METHOD  PATH                             REWRITE             STATUS
               |GET     ^/fee/(.*)/fi/(.*)/fo/(.*)/fum$  /boom/\\1-\\2-\\3/box  Running
               |GET     ^/boom/(.*)/box$                                     Running
               |GET     ^/bacon                          /burger             Running
               |GET     ^/tree                                               Running
               |GET     /foo                             /baz                Running
               |GET     /baz                                                 Running
               |
               |TCP ACLS
               |--------
               |TCP/PORT  STATUS
               |3303      Running
               |5601      Running
               |12101     Running
               |
               |SERVICE NAMES
               |-------------
               |SERVICE NAME  STATUS
               |path-tester   Running
               |ptunnel       Running
               |
               |""")
        self.assertEqual(expected_result, self.output(stdout))

        self.assertEqual('', self.output(stderr))

    def test_find_by_bundle_id_config_digest(self):
        http_method = self.respond_with_file_contents('data/conduct_info_inspect/bundle_with_acls.json')
        stdout = MagicMock()
        stderr = MagicMock()
        mock_arrow_now = MagicMock(return_value=arrow.get('2017-04-03T12:15:54.000'))

        args = self.default_args.copy()
        args.update({'bundle': 'bdfa43d-e5f3504'})
        input_args = MagicMock(**args)

        with patch('requests.get', http_method), \
                patch('arrow.now', mock_arrow_now):
            logging_setup.configure_logging(input_args, stdout, stderr)
            result = conduct_info.info(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})

        self.maxDiff = None
        expected_result = strip_margin(
            """|BUNDLE ATTRIBUTES
               |-----------------
               |Bundle Id              bdfa43d-e5f3504
               |Bundle Name            conductr-haproxy
               |Compatibility Version  2
               |System                 conductr-haproxy
               |System Version         2
               |Tags                   2.0.0
               |Nr of CPUs             0.1
               |Memory                 402653184
               |Disk Space             35000000
               |Roles                  haproxy
               |Bundle Digest          bdfa43d7ade7456af30a95e9ef4bce863d3029dc58b6824f5783881297d1983b
               |Configuration Digest   e5f35046d59c27f4cfeebcc026f3e3b76e027b15223a8961b59d728e559402e2
               |Error                  No
               |
               |BUNDLE SCALE
               |------------
               |Nr of Reschedules  0
               |Scale              1
               |
               |BUNDLE INSTALLATIONS
               |--------------------
               |Host                  192.168.10.2
               |Bundle                /Users/felixsatyaputra/.conductr/images/tmp/conductr/192.168.10.2/bundles/bdfa43d7ade7456af30a95e9ef4bce863d3029dc58b6824f5783881297d1983b.zip
               |Bundle configuration  /Users/felixsatyaputra/.conductr/images/tmp/conductr/192.168.10.2/bundles/e5f35046d59c27f4cfeebcc026f3e3b76e027b15223a8961b59d728e559402e2.zip
               |
               |Host                  192.168.10.1
               |Bundle                /Users/felixsatyaputra/.conductr/images/tmp/conductr/192.168.10.1/bundles/bdfa43d7ade7456af30a95e9ef4bce863d3029dc58b6824f5783881297d1983b.zip
               |Bundle configuration  /Users/felixsatyaputra/.conductr/images/tmp/conductr/192.168.10.1/bundles/e5f35046d59c27f4cfeebcc026f3e3b76e027b15223a8961b59d728e559402e2.zip
               |
               |Host                  192.168.10.3
               |Bundle                /Users/felixsatyaputra/.conductr/images/tmp/conductr/192.168.10.3/bundles/bdfa43d7ade7456af30a95e9ef4bce863d3029dc58b6824f5783881297d1983b.zip
               |Bundle configuration  /Users/felixsatyaputra/.conductr/images/tmp/conductr/192.168.10.3/bundles/e5f35046d59c27f4cfeebcc026f3e3b76e027b15223a8961b59d728e559402e2.zip
               |
               |BUNDLE EXECUTIONS
               |-----------------
               |ENDPOINT  HOST          PID  STARTED       UPTIME  BIND_PORT  HOST_PORT
               |status    192.168.10.2    0      Yes  2h, 11m, 4s       9009       9009
               |
               |""")
        self.assertEqual(expected_result, self.output(stdout))

        self.assertEqual('', self.output(stderr))

    def test_find_by_bundle_id_config_digest_long(self):
        http_method = self.respond_with_file_contents('data/conduct_info_inspect/bundle_with_acls.json')
        stdout = MagicMock()
        stderr = MagicMock()
        mock_arrow_now = MagicMock(return_value=arrow.get('2017-04-03T12:15:54.000'))

        args = self.default_args.copy()
        args.update({
            'bundle': 'bdfa43d7ade7456af30a95e9ef4bce86-e5f35046d59c27f4cfeebcc026f3e3b7',
            'long_ids': True
        })
        input_args = MagicMock(**args)

        with patch('requests.get', http_method), \
                patch('arrow.now', mock_arrow_now):
            logging_setup.configure_logging(input_args, stdout, stderr)
            result = conduct_info.info(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})

        self.maxDiff = None
        expected_result = strip_margin(
            """|BUNDLE ATTRIBUTES
               |-----------------
               |Bundle Id              bdfa43d7ade7456af30a95e9ef4bce86-e5f35046d59c27f4cfeebcc026f3e3b7
               |Bundle Name            conductr-haproxy
               |Compatibility Version  2
               |System                 conductr-haproxy
               |System Version         2
               |Tags                   2.0.0
               |Nr of CPUs             0.1
               |Memory                 402653184
               |Disk Space             35000000
               |Roles                  haproxy
               |Bundle Digest          bdfa43d7ade7456af30a95e9ef4bce863d3029dc58b6824f5783881297d1983b
               |Configuration Digest   e5f35046d59c27f4cfeebcc026f3e3b76e027b15223a8961b59d728e559402e2
               |Error                  No
               |
               |BUNDLE SCALE
               |------------
               |Nr of Reschedules  0
               |Scale              1
               |
               |BUNDLE INSTALLATIONS
               |--------------------
               |Host                  192.168.10.2
               |Bundle                /Users/felixsatyaputra/.conductr/images/tmp/conductr/192.168.10.2/bundles/bdfa43d7ade7456af30a95e9ef4bce863d3029dc58b6824f5783881297d1983b.zip
               |Bundle configuration  /Users/felixsatyaputra/.conductr/images/tmp/conductr/192.168.10.2/bundles/e5f35046d59c27f4cfeebcc026f3e3b76e027b15223a8961b59d728e559402e2.zip
               |
               |Host                  192.168.10.1
               |Bundle                /Users/felixsatyaputra/.conductr/images/tmp/conductr/192.168.10.1/bundles/bdfa43d7ade7456af30a95e9ef4bce863d3029dc58b6824f5783881297d1983b.zip
               |Bundle configuration  /Users/felixsatyaputra/.conductr/images/tmp/conductr/192.168.10.1/bundles/e5f35046d59c27f4cfeebcc026f3e3b76e027b15223a8961b59d728e559402e2.zip
               |
               |Host                  192.168.10.3
               |Bundle                /Users/felixsatyaputra/.conductr/images/tmp/conductr/192.168.10.3/bundles/bdfa43d7ade7456af30a95e9ef4bce863d3029dc58b6824f5783881297d1983b.zip
               |Bundle configuration  /Users/felixsatyaputra/.conductr/images/tmp/conductr/192.168.10.3/bundles/e5f35046d59c27f4cfeebcc026f3e3b76e027b15223a8961b59d728e559402e2.zip
               |
               |BUNDLE EXECUTIONS
               |-----------------
               |ENDPOINT  HOST          PID  STARTED       UPTIME  BIND_PORT  HOST_PORT
               |status    192.168.10.2    0      Yes  2h, 11m, 4s       9009       9009
               |
               |""")
        self.assertEqual(expected_result, self.output(stdout))

        self.assertEqual('', self.output(stderr))

    def test_bundle_no_endpoint(self):
        http_method = self.respond_with_file_contents('data/conduct_info_inspect/bundle_without_endpoint.json')
        stdout = MagicMock()
        stderr = MagicMock()
        mock_arrow_now = MagicMock(return_value=arrow.get('2017-04-03T12:15:54.000'))

        args = self.default_args.copy()
        args.update({
            'bundle': 'bundle-no-endpoint'
        })
        input_args = MagicMock(**args)

        with patch('requests.get', http_method), \
                patch('arrow.now', mock_arrow_now):
            logging_setup.configure_logging(input_args, stdout, stderr)
            result = conduct_info.info(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})

        self.maxDiff = None
        expected_result = strip_margin(
            """|BUNDLE ATTRIBUTES
               |-----------------
               |Bundle Id              7f58747
               |Bundle Name            bundle-no-endpoint
               |Compatibility Version  1
               |System                 bundle-no-endpoint
               |System Version         0.1.0
               |Tags                   tag
               |Nr of CPUs             1
               |Memory                 8000000
               |Disk Space             10000000
               |Roles                  test
               |Bundle Digest          7f5874760a2a949d1860d4185ab70437c51094821a2e8c229d2ee7e3e8279edf
               |Error                  No
               |
               |BUNDLE SCALE
               |------------
               |Nr of Reschedules  0
               |Scale              1
               |
               |BUNDLE INSTALLATIONS
               |--------------------
               |Host    192.168.10.1
               |Bundle  /Users/felixsatyaputra/.conductr/images/tmp/conductr/192.168.10.1/bundles/7f5874760a2a949d1860d4185ab70437c51094821a2e8c229d2ee7e3e8279edf.zip
               |
               |BUNDLE EXECUTIONS
               |-----------------
               |HOST            PID  STARTED        UPTIME
               |192.168.10.1  53684      Yes  8h, 58m, 39s
               |
               |""")
        self.assertEqual(expected_result, self.output(stdout))

        self.assertEqual('', self.output(stderr))

    def test_stopped_bundle_multiple_tags(self):
        http_method = self.respond_with_file_contents('data/conduct_info_inspect/bundle_with_acls.json')
        stdout = MagicMock()
        stderr = MagicMock()

        args = self.default_args.copy()
        args.update({'bundle': 'conductr-elasticsearch'})
        input_args = MagicMock(**args)

        with patch('requests.get', http_method):
            logging_setup.configure_logging(input_args, stdout, stderr)
            result = conduct_info.info(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})

        expected_result = strip_margin(
            """|BUNDLE ATTRIBUTES
               |-----------------
               |Bundle Id              85dd265
               |Bundle Name            conductr-elasticsearch
               |Compatibility Version  1
               |System                 conductr-elasticsearch
               |System Version         1
               |Tags                   1.0.0, latest
               |Nr of CPUs             0.1
               |Memory                 1572864000
               |Disk Space             100000000
               |Roles                  elasticsearch
               |Bundle Digest          85dd2657bf86e5ed817c6cbe9d4c18e3a6c30eb3146383fc65357b65f11cb550
               |Error                  No
               |
               |BUNDLE INSTALLATIONS
               |--------------------
               |Host    192.168.10.2
               |Bundle  /Users/felixsatyaputra/.conductr/images/tmp/conductr/192.168.10.2/bundles/85dd2657bf86e5ed817c6cbe9d4c18e3a6c30eb3146383fc65357b65f11cb550.zip
               |
               |Host    192.168.10.1
               |Bundle  /Users/felixsatyaputra/.conductr/images/tmp/conductr/192.168.10.1/bundles/85dd2657bf86e5ed817c6cbe9d4c18e3a6c30eb3146383fc65357b65f11cb550.zip
               |
               |Host    192.168.10.3
               |Bundle  /Users/felixsatyaputra/.conductr/images/tmp/conductr/192.168.10.3/bundles/85dd2657bf86e5ed817c6cbe9d4c18e3a6c30eb3146383fc65357b65f11cb550.zip
               |
               |""")
        self.assertEqual(expected_result, self.output(stdout))

        self.assertEqual('', self.output(stderr))

    def test_multiple_bundles_found(self):
        http_method = self.respond_with_file_contents('data/conduct_info_inspect/bundle_with_acls.json')
        stdout = MagicMock()
        stderr = MagicMock()

        args = self.default_args.copy()
        args.update({'bundle': 'cond'})
        input_args = MagicMock(**args)

        with patch('requests.get', http_method):
            logging_setup.configure_logging(input_args, stdout, stderr)
            result = conduct_info.info(input_args)
            self.assertFalse(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})

        self.assertEqual('', self.output(stdout))

        expected_error = as_error(strip_margin("""|Error: Specified Bundle ID/name: cond resulted in multiple Bundle IDs: ['85dd265', 'bdfa43d-e5f3504']
                                                  |"""))
        self.assertEqual(expected_error, self.output(stderr))

    def test_no_bundles_found(self):
        http_method = self.respond_with_file_contents('data/conduct_info_inspect/bundle_with_acls.json')
        stdout = MagicMock()
        stderr = MagicMock()

        args = self.default_args.copy()
        args.update({'bundle': 'something-invalid'})
        input_args = MagicMock(**args)

        with patch('requests.get', http_method):
            logging_setup.configure_logging(input_args, stdout, stderr)
            result = conduct_info.info(input_args)
            self.assertFalse(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})

        self.assertEqual('', self.output(stdout))

        expected_error = as_error(strip_margin("""|Error: Unable to find bundle something-invalid
                                                  |"""))
        self.assertEqual(expected_error, self.output(stderr))
