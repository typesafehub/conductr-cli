import json

from conductr_cli.test.cli_test_case import CliTestCase
from conductr_cli import conduct_members
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
    filtered_by_role_replicator_args.update({'role': 'replicator'})

    example_json = json.loads(
        """
            {
                "selfNode": {
                    "address": "akka.tcp://conductr@127.0.0.1:9004",
                    "uid": -2007039750
                },
                "members": [
                    {
                        "node": {
                            "address": "akka.tcp://conductr@127.0.0.1:9004",
                            "uid": -2007039750
                        },
                        "status": "Up",
                        "roles": [
                            "replicator"
                        ]
                    },
                    {
                        "node": {
                            "address": "akka.tcp://conductr@127.0.0.2:9004",
                            "uid": 1902649436
                        },
                        "status": "Up",
                        "roles": [
                            "replicator"
                        ]
                    }
                ],
                "unreachable": [
                    {
                        "node": {
                            "address": "akka.tcp://conductr@127.0.0.2:9004",
                            "uid": 1902649436
                        },
                        "observedBy": [
                            {
                                "address": "akka.tcp://conductr@127.0.0.1:9004",
                                "uid": -2007039750
                            }
                        ]
                    }
                ]
            }
        """
    )

    def test_calculate_rows(self):
        example_rows = conduct_members.calculate_rows(MagicMock(**self.default_args), self.example_json)

        self.assertEqual(example_rows[1], {
            'address': 'akka.tcp://conductr@127.0.0.1:9004',
            'uid': -2007039750,
            'roles': 'replicator',
            'status': 'Up',
            'reachable': 'Yes'
        })

        self.assertEqual(example_rows[2], {
            'address': 'akka.tcp://conductr@127.0.0.2:9004',
            'uid': 1902649436,
            'roles': 'replicator',
            'status': 'Up',
            'reachable': 'No'
        })

    def test_include_entry(self):
        self.assertFalse(conduct_members.include_entry(MagicMock(**self.filtered_by_role_asdf_args), {
            'node': {
                'address': 'akka.tcp://conductr@127.0.0.1:9004',
                'uid': -2007039750
            },
            'status': 'Up',
            'roles': ['replicator']
        }))

        self.assertTrue(conduct_members.include_entry(MagicMock(**self.filtered_by_role_replicator_args), {
            'node': {
                'address': 'akka.tcp://conductr@127.0.0.1:9004',
                'uid': -2007039750
            },
            'status': 'Up',
            'roles': ['replicator']
        }))
