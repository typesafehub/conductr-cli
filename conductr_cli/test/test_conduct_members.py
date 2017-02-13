from conductr_cli.test.cli_test_case import CliTestCase, strip_margin
from conductr_cli import conduct_members, logging_setup
from conductr_cli.http import DEFAULT_HTTP_TIMEOUT
from unittest.mock import patch, MagicMock


class TestConductMembersCommand(CliTestCase):
    conductr_auth = ('username', 'password')
    server_verification_file = MagicMock(name='server_verification_file')

    default_url = 'http://127.0.0.1:9005/v2/members'

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

    fake_output = """
        {
          "members": [
            {
              "node": {
                "address": "akka.tcp://conductr@192.168.10.1:9004",
                "uid": -916664159
              },
              "roles": [
                "replicator"
              ],
              "status": "Up"
            },
            {
              "node": {
                "address": "akka.tcp://conductr@192.168.10.2:9004",
                "uid": 1129598726
              },
              "roles": [
                "replicator"
              ],
              "status": "Up"
            },
            {
              "node": {
                "address": "akka.tcp://conductr@192.168.10.3:9004",
                "uid": -543773917
              },
              "roles": [
                "replicator"
              ],
              "status": "Up"
            }
          ],
          "selfNode": {
            "address": "akka.tcp://conductr@192.168.10.1:9004",
            "uid": -916664159
          },
          "unreachable": []
        }
    """

    def test_basic_usage(self):
        self.maxDiff = None

        http_method = self.respond_with(text=self.fake_output)

        stdout = MagicMock()

        input_args = MagicMock(**self.default_args)
        with patch('requests.get', http_method):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_members.members(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})

        self.assertEqual(
            strip_margin("""|UID         ADDRESS                                ROLES       STATUS  REACHABLE
                            |-916664159  akka.tcp://conductr@192.168.10.1:9004  replicator  Up            Yes
                            |1129598726  akka.tcp://conductr@192.168.10.2:9004  replicator  Up            Yes
                            |-543773917  akka.tcp://conductr@192.168.10.3:9004  replicator  Up            Yes
                            |"""),

            self.output(stdout)
        )

    def test_role_no_match(self):
        self.maxDiff = None

        filtered_by_role_asdf_args = self.default_args.copy()
        filtered_by_role_asdf_args.update({'role': 'asdf'})
        http_method = self.respond_with(text=self.fake_output)

        stdout = MagicMock()

        input_args = MagicMock(**filtered_by_role_asdf_args)
        with patch('requests.get', http_method):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_members.members(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})
        self.assertEqual(
            strip_margin("""|UID  ADDRESS  ROLES  STATUS  REACHABLE
                            |"""),

            self.output(stdout)
        )

    def test_role_match(self):
        self.maxDiff = None

        filtered_by_role_replicator_args = self.default_args.copy()
        filtered_by_role_replicator_args.update({'role': 'replicator'})

        http_method = self.respond_with(text=self.fake_output)

        stdout = MagicMock()

        input_args = MagicMock(**filtered_by_role_replicator_args)
        with patch('requests.get', http_method):
            logging_setup.configure_logging(input_args, stdout)
            result = conduct_members.members(input_args)
            self.assertTrue(result)

        http_method.assert_called_with(self.default_url, auth=self.conductr_auth, verify=self.server_verification_file,
                                       timeout=DEFAULT_HTTP_TIMEOUT, headers={'Host': '127.0.0.1'})

        self.assertEqual(
            strip_margin("""|UID         ADDRESS                                ROLES       STATUS  REACHABLE
                            |-916664159  akka.tcp://conductr@192.168.10.1:9004  replicator  Up            Yes
                            |1129598726  akka.tcp://conductr@192.168.10.2:9004  replicator  Up            Yes
                            |-543773917  akka.tcp://conductr@192.168.10.3:9004  replicator  Up            Yes
                            |"""),

            self.output(stdout)
        )
