from conductr_cli.test.cli_test_case import CliTestCase, strip_margin
from conductr_cli import conduct_agents, logging_setup
from conductr_cli.http import DEFAULT_HTTP_TIMEOUT
from unittest.mock import patch, MagicMock


class TestConductAgentsCommand(CliTestCase):
    conductr_auth = ('username', 'password')
    server_verification_file = MagicMock(name='server_verification_file')

    default_url = 'http://127.0.0.1:9005/v2/agents'

    default_args = {
        'dcos_mode': False,
        'scheme': 'http',
        'host': '127.0.0.1',
        'port': 9005,
        'base_path': '/',
        'api_version': '2',
        'verbose': False,
        'quiet': False,
        'long_ids': False,
        'conductr_auth': conductr_auth,
        'server_verification_file': server_verification_file,
        'role': None
    }

    fake_output_with_resources = """
        [
          {
            "address": "akka.tcp://conductr-agent@192.168.10.1:2552/user/reaper/cluster-client#-596247188",
            "observedBy": [
              {
                "node": {
                  "address": "akka.tcp://conductr@192.168.10.2:9004",
                  "uid": "1129598726"
                }
              }
            ],
            "resourceAvailable": {
              "diskSpace": 130841165824,
              "memory": 5028888576,
              "nrOfCpus": 4
            },
            "roles": [
              "web",
              "data"
            ]
          },
          {
            "address": "akka.tcp://conductr-agent@192.168.10.2:2552/user/reaper/cluster-client#-775189131",
            "observedBy": [
              {
                "node": {
                  "address": "akka.tcp://conductr@192.168.10.2:9004",
                  "uid": "1129598726"
                }
              }
            ],
            "resourceAvailable": {
              "diskSpace": 60841165824,
              "memory": 3028888576,
              "nrOfCpus": 8
            },
            "roles": [
              "web"
            ]
          },
          {
            "address": "akka.tcp://conductr-agent@192.168.10.3:2552/user/reaper/cluster-client#1858099110",
            "observedBy": [
              {
                "node": {
                  "address": "akka.tcp://conductr@192.168.10.2:9004",
                  "uid": "1129598726"
                }
              }
            ],
            "resourceAvailable": {
              "diskSpace": 160841165824,
              "memory": 4028888576,
              "nrOfCpus": 2
            },
            "roles": [
              "web",
              "data"
            ]
          }
        ]
    """

    fake_output_with_partial_resources = """
        [
          {
            "address": "akka.tcp://conductr-agent@192.168.10.1:2552/user/reaper/cluster-client#-596247188",
            "observedBy": [
              {
                "node": {
                  "address": "akka.tcp://conductr@192.168.10.2:9004",
                  "uid": "1129598726"
                }
              }
            ],
            "resourceAvailable": {
              "diskSpace": 130841165824,
              "memory": 5028888576,
              "nrOfCpus": 4
            },
            "roles": [
              "web",
              "data"
            ]
          },
          {
            "address": "akka.tcp://conductr-agent@192.168.10.2:2552/user/reaper/cluster-client#-775189131",
            "observedBy": [
              {
                "node": {
                  "address": "akka.tcp://conductr@192.168.10.2:9004",
                  "uid": "1129598726"
                }
              }
            ],
            "roles": [
              "web"
            ]
          },
          {
            "address": "akka.tcp://conductr-agent@192.168.10.3:2552/user/reaper/cluster-client#1858099110",
            "observedBy": [
              {
                "node": {
                  "address": "akka.tcp://conductr@192.168.10.2:9004",
                  "uid": "1129598726"
                }
              }
            ],
            "resourceAvailable": {
              "diskSpace": 160841165824,
              "memory": 4028888576,
              "nrOfCpus": 2
            },
            "roles": [
              "web",
              "data"
            ]
          }
        ]
    """

    fake_output_without_resources = """
        [
          {
            "address": "akka.tcp://conductr-agent@192.168.10.1:2552/user/reaper/cluster-client#-596247188",
            "observedBy": [
              {
                "node": {
                  "address": "akka.tcp://conductr@192.168.10.2:9004",
                  "uid": "1129598726"
                }
              }
            ],
            "roles": [
              "web",
              "data"
            ]
          },
          {
            "address": "akka.tcp://conductr-agent@192.168.10.2:2552/user/reaper/cluster-client#-775189131",
            "observedBy": [
              {
                "node": {
                  "address": "akka.tcp://conductr@192.168.10.2:9004",
                  "uid": "1129598726"
                }
              }
            ],
            "roles": [
              "web"
            ]
          },
          {
            "address": "akka.tcp://conductr-agent@192.168.10.3:2552/user/reaper/cluster-client#1858099110",
            "observedBy": [
              {
                "node": {
                  "address": "akka.tcp://conductr@192.168.10.2:9004",
                  "uid": "1129598726"
                }
              }
            ],
            "roles": [
              "web",
              "data"
            ]
          }
        ]
    """

    def test_basic_usage_without_resources(self):
        self.maxDiff = None

        http_method = self.respond_with(text=self.fake_output_without_resources)

        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_agents.agents(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})

        self.assertEqual(
            strip_margin("""|ADDRESS                                                                            ROLES     OBSERVED BY
                            |akka.tcp://conductr-agent@192.168.10.1:2552/user/reaper/cluster-client#-596247188  web,data  akka.tcp://conductr@192.168.10.2:9004
                            |akka.tcp://conductr-agent@192.168.10.2:2552/user/reaper/cluster-client#-775189131  web       akka.tcp://conductr@192.168.10.2:9004
                            |akka.tcp://conductr-agent@192.168.10.3:2552/user/reaper/cluster-client#1858099110  web,data  akka.tcp://conductr@192.168.10.2:9004
                            |"""),
            self.output(stdout))

    def test_basic_usage_with_resources(self):
        self.maxDiff = None

        http_method = self.respond_with(text=self.fake_output_with_resources)

        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_agents.agents(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})

        self.assertEqual(
            strip_margin("""|ADDRESS                                                                                DISK      MEM  CPUS  ROLES     OBSERVED BY
                            |akka.tcp://conductr-agent@192.168.10.1:2552/user/reaper/cluster-client#-596247188  130.8 GB  4.7 GiB     4  web,data  akka.tcp://conductr@192.168.10.2:9004
                            |akka.tcp://conductr-agent@192.168.10.2:2552/user/reaper/cluster-client#-775189131   60.8 GB  2.8 GiB     8  web       akka.tcp://conductr@192.168.10.2:9004
                            |akka.tcp://conductr-agent@192.168.10.3:2552/user/reaper/cluster-client#1858099110  160.8 GB  3.8 GiB     2  web,data  akka.tcp://conductr@192.168.10.2:9004
                            |"""),
            self.output(stdout))

    def test_basic_usage_with_partial_resources(self):
        self.maxDiff = None

        http_method = self.respond_with(text=self.fake_output_with_partial_resources)

        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_agents.agents(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})

        self.assertEqual(
            strip_margin("""|ADDRESS                                                                                DISK      MEM  CPUS  ROLES     OBSERVED BY
                            |akka.tcp://conductr-agent@192.168.10.1:2552/user/reaper/cluster-client#-596247188  130.8 GB  4.7 GiB     4  web,data  akka.tcp://conductr@192.168.10.2:9004
                            |akka.tcp://conductr-agent@192.168.10.2:2552/user/reaper/cluster-client#-775189131                           web       akka.tcp://conductr@192.168.10.2:9004
                            |akka.tcp://conductr-agent@192.168.10.3:2552/user/reaper/cluster-client#1858099110  160.8 GB  3.8 GiB     2  web,data  akka.tcp://conductr@192.168.10.2:9004
                            |"""),
            self.output(stdout))

    def test_role_no_match(self):
        self.maxDiff = None

        filtered_by_role_asdf_args = self.default_args.copy()
        filtered_by_role_asdf_args.update({'role': 'asdf'})
        http_method = self.respond_with(text=self.fake_output_with_resources)

        stdout = MagicMock()

        input_args = MagicMock(**filtered_by_role_asdf_args)
        with patch('requests.get', http_method):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_agents.agents(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})
        self.assertEqual(
            strip_margin("""|ADDRESS  DISK  MEM  CPUS  ROLES  OBSERVED BY
                            |"""),
            self.output(stdout))

    def test_role_match(self):
        self.maxDiff = None

        filtered_by_role_web_args = self.default_args.copy()
        filtered_by_role_web_args.update({'role': 'web'})

        http_method = self.respond_with(text=self.fake_output_with_resources)

        stdout = MagicMock()

        input_args = MagicMock(**filtered_by_role_web_args)
        with patch('requests.get', http_method):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_agents.agents(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})
        self.assertEqual(
            strip_margin("""|ADDRESS                                                                                DISK      MEM  CPUS  ROLES     OBSERVED BY
                            |akka.tcp://conductr-agent@192.168.10.1:2552/user/reaper/cluster-client#-596247188  130.8 GB  4.7 GiB     4  web,data  akka.tcp://conductr@192.168.10.2:9004
                            |akka.tcp://conductr-agent@192.168.10.2:2552/user/reaper/cluster-client#-775189131   60.8 GB  2.8 GiB     8  web       akka.tcp://conductr@192.168.10.2:9004
                            |akka.tcp://conductr-agent@192.168.10.3:2552/user/reaper/cluster-client#1858099110  160.8 GB  3.8 GiB     2  web,data  akka.tcp://conductr@192.168.10.2:9004
                            |"""),
            self.output(stdout))

    def test_role_match_data(self):
        self.maxDiff = None

        filtered_by_role_web_args = self.default_args.copy()
        filtered_by_role_web_args.update({'role': 'data'})

        http_method = self.respond_with(text=self.fake_output_with_resources)

        stdout = MagicMock()

        input_args = MagicMock(**filtered_by_role_web_args)
        with patch('requests.get', http_method):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_agents.agents(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})
        self.assertEqual(
            strip_margin("""|ADDRESS                                                                                DISK      MEM  CPUS  ROLES     OBSERVED BY
                            |akka.tcp://conductr-agent@192.168.10.1:2552/user/reaper/cluster-client#-596247188  130.8 GB  4.7 GiB     4  web,data  akka.tcp://conductr@192.168.10.2:9004
                            |akka.tcp://conductr-agent@192.168.10.3:2552/user/reaper/cluster-client#1858099110  160.8 GB  3.8 GiB     2  web,data  akka.tcp://conductr@192.168.10.2:9004
                            |"""),
            self.output(stdout))
