from conductr_cli.test.cli_test_case import CliTestCase
from conductr_cli import sandbox_run_jvm
from conductr_cli.exceptions import BindAddressNotFoundError, InstanceCountError
from conductr_cli.sandbox_run_jvm import BIND_TEST_PORT
from unittest.mock import call, patch, MagicMock
import ipaddress


class TestRun(CliTestCase):
    addr_range = ipaddress.ip_network('192.168.1.0/24', strict=True)
    default_args = {
        'image_version': '2.0.0',
        'conductr_roles': [],
        'log_level': 'info',
        'nr_of_containers': 1,
        'addr_range': addr_range,
        'no_wait': False
    }

    def test_default_args(self):
        mock_validate_jvm_support = MagicMock()

        bind_addr = MagicMock()
        bind_addrs = [bind_addr]
        mock_find_bind_addrs = MagicMock(return_value=bind_addrs)

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
                patch('conductr_cli.sandbox_run_jvm.find_bind_addrs', mock_find_bind_addrs), \
                patch('conductr_cli.sandbox_run_jvm.obtain_sandbox_image', mock_obtain_sandbox_image), \
                patch('conductr_cli.sandbox_run_jvm.sandbox_stop', mock_sandbox_stop), \
                patch('conductr_cli.sandbox_run_jvm.start_core_instances', mock_start_core_instances), \
                patch('conductr_cli.sandbox_run_jvm.start_agent_instances', mock_start_agent_instances):
            result = sandbox_run_jvm.run(input_args, features)
            self.assertEqual((mock_core_pids, mock_agent_pids), result)

        mock_find_bind_addrs.assert_called_with(1, self.addr_range)
        mock_start_core_instances.assert_called_with(mock_core_extracted_dir, bind_addrs)
        mock_start_agent_instances.assert_called_with(mock_agent_extracted_dir, bind_addrs)

    def test_nr_of_core_agent_instances(self):
        mock_validate_jvm_support = MagicMock()

        bind_addr1 = MagicMock()
        bind_addr2 = MagicMock()
        bind_addr3 = MagicMock()
        bind_addrs = [bind_addr1, bind_addr2, bind_addr3]
        mock_find_bind_addrs = MagicMock(return_value=bind_addrs)

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
                patch('conductr_cli.sandbox_run_jvm.find_bind_addrs', mock_find_bind_addrs), \
                patch('conductr_cli.sandbox_run_jvm.obtain_sandbox_image', mock_obtain_sandbox_image), \
                patch('conductr_cli.sandbox_run_jvm.sandbox_stop', mock_sandbox_stop), \
                patch('conductr_cli.sandbox_run_jvm.start_core_instances', mock_start_core_instances), \
                patch('conductr_cli.sandbox_run_jvm.start_agent_instances', mock_start_agent_instances):
            result = sandbox_run_jvm.run(input_args, features)
            self.assertEqual((mock_core_pids, mock_agent_pids), result)

        mock_find_bind_addrs.assert_called_with(3, self.addr_range)
        mock_start_core_instances.assert_called_with(mock_core_extracted_dir, [bind_addr1])
        mock_start_agent_instances.assert_called_with(mock_agent_extracted_dir, [bind_addr1, bind_addr2, bind_addr3])

    def test_invalid_nr_of_containers(self):
        args = self.default_args.copy()
        args.update({
            'nr_of_containers': 'FOO'
        })
        input_args = MagicMock(**args)
        features = []

        self.assertRaises(InstanceCountError, sandbox_run_jvm.run, input_args, features)


class TestFindBindAddresses(CliTestCase):
    nr_of_instances = 3
    addr_range = ipaddress.ip_network('192.168.1.0/24', strict=True)

    def test_found(self):
        mock_can_bind = MagicMock(return_value=True)
        mock_addr_alias_setup_instructions = MagicMock(return_value="test")

        with patch('conductr_cli.host.can_bind', mock_can_bind), \
                patch('conductr_cli.host.addr_alias_setup_instructions', mock_addr_alias_setup_instructions):
            result = sandbox_run_jvm.find_bind_addrs(self.nr_of_instances, self.addr_range)
            self.assertEqual([
                ipaddress.ip_address('192.168.1.1'),
                ipaddress.ip_address('192.168.1.2'),
                ipaddress.ip_address('192.168.1.3')
            ], result)

        self.assertEqual([
            call(ipaddress.ip_address('192.168.1.1'), BIND_TEST_PORT),
            call(ipaddress.ip_address('192.168.1.2'), BIND_TEST_PORT),
            call(ipaddress.ip_address('192.168.1.3'), BIND_TEST_PORT)
        ], mock_can_bind.call_args_list)

        mock_addr_alias_setup_instructions.assert_not_called()

    def test_not_found(self):
        mock_can_bind = MagicMock(return_value=False)
        mock_addr_alias_setup_instructions = MagicMock(return_value="test")

        with patch('conductr_cli.host.can_bind', mock_can_bind), \
                patch('conductr_cli.host.addr_alias_setup_instructions', mock_addr_alias_setup_instructions):
            self.assertRaises(BindAddressNotFoundError, sandbox_run_jvm.find_bind_addrs, 3, self.addr_range)

        self.assertEqual([
            call(addr, BIND_TEST_PORT) for addr in self.addr_range.hosts()
        ], mock_can_bind.call_args_list)

        mock_addr_alias_setup_instructions.assert_called_once_with(
            [ipaddress.ip_address('192.168.1.1'),
             ipaddress.ip_address('192.168.1.2'),
             ipaddress.ip_address('192.168.1.3')],
            self.addr_range.netmask)

    def test_partial_found(self):
        mock_can_bind = MagicMock(side_effect=[
            True if idx == 0 else False
            for idx, addr in enumerate(self.addr_range.hosts())
        ])
        mock_addr_alias_setup_instructions = MagicMock(return_value="test")

        with patch('conductr_cli.host.can_bind', mock_can_bind), \
                patch('conductr_cli.host.addr_alias_setup_instructions', mock_addr_alias_setup_instructions):
            self.assertRaises(BindAddressNotFoundError, sandbox_run_jvm.find_bind_addrs, 3, self.addr_range)

        self.assertEqual([
            call(addr, BIND_TEST_PORT) for addr in self.addr_range.hosts()
        ], mock_can_bind.call_args_list)

        mock_addr_alias_setup_instructions.assert_called_once_with(
            [ipaddress.ip_address('192.168.1.2'),
             ipaddress.ip_address('192.168.1.3')],
            self.addr_range.netmask)
