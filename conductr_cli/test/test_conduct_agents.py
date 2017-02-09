import json

from conductr_cli.test.cli_test_case import CliTestCase
from conductr_cli import conduct_agents
from unittest.mock import MagicMock


class TestConductMembersCommand(CliTestCase):
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
        'role': None
    }

    filtered_by_role_asdf_args = default_args.copy()
    filtered_by_role_asdf_args.update({'role': 'asdf'})

    filtered_by_role_replicator_args = default_args.copy()
    filtered_by_role_replicator_args.update({'role': 'web'})

    example_json = json.loads(
        """
            [
                {
                    "address": "akka.tcp://conductr-agent@127.0.0.1:2552/user/reaper/cluster-client#1363584093",
                    "roles": [
                        "web"
                    ],
                    "observedBy": [
                        {
                            "node": {
                                "uid": "-2007039750",
                                "address": "akka.tcp://conductr@127.0.0.1:9004"
                            }
                        }
                    ]
                }
            ]
        """
    )

    def test_calculate_rows(self):
        example_rows = conduct_agents.calculate_rows(MagicMock(**self.default_args), self.example_json)

        self.assertEqual(example_rows[1], {
            'address': 'akka.tcp://conductr-agent@127.0.0.1:2552/user/reaper/cluster-client#1363584093',
            'roles': 'web'
        })

    def test_include_entry(self):
        self.assertFalse(conduct_agents.include_entry(MagicMock(**self.filtered_by_role_asdf_args), {
            'address': 'akka.tcp://conductr-agent@127.0.0.1:2552/user/reaper/cluster-client#1363584093',
            'roles': 'web'
        }))

        self.assertTrue(conduct_agents.include_entry(MagicMock(**self.filtered_by_role_replicator_args), {
            'address': 'akka.tcp://conductr-agent@127.0.0.1:2552/user/reaper/cluster-client#1363584093',
            'roles': 'web'
        }))
