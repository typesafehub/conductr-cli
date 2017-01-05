from conductr_cli.test.cli_test_case import CliTestCase
from conductr_cli import sandbox_run_jvm
from conductr_cli.exceptions import InstanceCountError
from unittest.mock import patch, MagicMock
import ipaddress


class TestRun(CliTestCase):
    network_interface = 'lo0'
    addr_range = ipaddress.ip_network('192.168.1.0/24', strict=True)
    default_args = {
        'image_version': '2.0.0',
        'conductr_roles': [],
        'log_level': 'info',
        'nr_of_containers': 1,
        'interface': network_interface,
        'addr_range': addr_range,
        'no_wait': False
    }

    def test_default_args(self):
        # TODO: remove each of these mocks and update this test with the implementation
        mock_validate_jvm_support = MagicMock()
        mock_validate_address_aliases = MagicMock()

        mock_core_extracted_dir = MagicMock()
        mock_agent_extracted_dir = MagicMock()
        mock_obtain_sandbox_image = MagicMock(return_value=(mock_core_extracted_dir, mock_agent_extracted_dir))

        mock_sandbox_stop = MagicMock()

        mock_core_pids = MagicMock()
        mock_start_core_instances = MagicMock(return_value=mock_core_pids)

        mock_agent_pids = MagicMock()
        mock_start_agent_instances = MagicMock(return_value=mock_agent_pids)

        input_args = MagicMock(**self.default_args)
        features = []

        with patch('conductr_cli.sandbox_run_jvm.validate_jvm_support', mock_validate_jvm_support), \
                patch('conductr_cli.sandbox_run_jvm.validate_address_aliases', mock_validate_address_aliases), \
                patch('conductr_cli.sandbox_run_jvm.obtain_sandbox_image', mock_obtain_sandbox_image), \
                patch('conductr_cli.sandbox_run_jvm.sandbox_stop', mock_sandbox_stop), \
                patch('conductr_cli.sandbox_run_jvm.start_core_instances', mock_start_core_instances), \
                patch('conductr_cli.sandbox_run_jvm.start_agent_instances', mock_start_agent_instances):
            result = sandbox_run_jvm.run(input_args, features)
            self.assertEqual((mock_core_pids, mock_agent_pids), result)

        mock_validate_address_aliases.assert_called_with(1, self.network_interface, self.addr_range)
        mock_start_core_instances.assert_called_with(mock_core_extracted_dir, 1, self.addr_range)
        mock_start_agent_instances.assert_called_with(mock_agent_extracted_dir, 1, self.addr_range)

    def test_nr_of_core_agent_instances(self):
        # TODO: remove each of these mocks and update this test with the implementation
        mock_validate_jvm_support = MagicMock()
        mock_validate_address_aliases = MagicMock()

        mock_core_extracted_dir = MagicMock()
        mock_agent_extracted_dir = MagicMock()
        mock_obtain_sandbox_image = MagicMock(return_value=(mock_core_extracted_dir, mock_agent_extracted_dir))

        mock_sandbox_stop = MagicMock()

        mock_core_pids = MagicMock()
        mock_start_core_instances = MagicMock(return_value=mock_core_pids)

        mock_agent_pids = MagicMock()
        mock_start_agent_instances = MagicMock(return_value=mock_agent_pids)

        args = self.default_args.copy()
        args.update({
            'nr_of_containers': '1:3'
        })
        input_args = MagicMock(**args)
        features = []

        with patch('conductr_cli.sandbox_run_jvm.validate_jvm_support', mock_validate_jvm_support), \
                patch('conductr_cli.sandbox_run_jvm.validate_address_aliases', mock_validate_address_aliases), \
                patch('conductr_cli.sandbox_run_jvm.obtain_sandbox_image', mock_obtain_sandbox_image), \
                patch('conductr_cli.sandbox_run_jvm.sandbox_stop', mock_sandbox_stop), \
                patch('conductr_cli.sandbox_run_jvm.start_core_instances', mock_start_core_instances), \
                patch('conductr_cli.sandbox_run_jvm.start_agent_instances', mock_start_agent_instances):
            result = sandbox_run_jvm.run(input_args, features)
            self.assertEqual((mock_core_pids, mock_agent_pids), result)

        mock_validate_address_aliases.assert_called_with(3, self.network_interface, self.addr_range)
        mock_start_core_instances.assert_called_with(mock_core_extracted_dir, 1, self.addr_range)
        mock_start_agent_instances.assert_called_with(mock_agent_extracted_dir, 3, self.addr_range)

    def test_invalid_nr_of_containers(self):
        args = self.default_args.copy()
        args.update({
            'nr_of_containers': 'FOO'
        })
        input_args = MagicMock(**args)
        features = []

        self.assertRaises(InstanceCountError, sandbox_run_jvm.run, input_args, features)
