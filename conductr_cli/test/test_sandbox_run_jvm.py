from conductr_cli.test.cli_test_case import CliTestCase
from conductr_cli import sandbox_run_jvm
from requests.exceptions import HTTPError, ConnectionError
from conductr_cli.exceptions import BindAddressNotFoundError, InstanceCountError, \
    BintrayUnreachableError, SandboxImageNotFoundError
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


class TestObtainSandboxImage(CliTestCase):
    def test_obtain_from_bintray(self):
        mock_load_bintray_credentials = MagicMock(return_value=('username', 'password'))
        mock_bintray_download = \
            MagicMock(side_effect=[(True, 'conductr-1.0.0.tgz', '/cache_dir/conductr-1.0.0.tgz'),
                                   (True, 'conductr-agent-1.0.0.tgz', '/cache_dir/conductr-agent-1.0.0.tgz')])
        mock_os_path_exists = MagicMock(side_effect=[False, False, False, False])
        mock_os_makedirs = MagicMock()
        mock_os_path_basename = MagicMock()
        mock_shutil_unpack_archive = MagicMock()
        mock_os_path_splitext = MagicMock(return_value=('sub_dir', '.tgz'))
        mock_os_listdir = MagicMock(return_value=['some-file-a', 'some-file-b'])
        mock_shutil_move = MagicMock()
        mock_os_rmdir = MagicMock()

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', mock_load_bintray_credentials), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_download', mock_bintray_download), \
                patch('os.path.exists', mock_os_path_exists), \
                patch('os.makedirs', mock_os_makedirs), \
                patch('os.path.basename', mock_os_path_basename), \
                patch('shutil.unpack_archive', mock_shutil_unpack_archive), \
                patch('os.path.splitext', mock_os_path_splitext), \
                patch('os.listdir', mock_os_listdir), \
                patch('shutil.move', mock_shutil_move), \
                patch('os.rmdir', mock_os_rmdir):
            result = sandbox_run_jvm.obtain_sandbox_image('/cache_dir', '1.0.0')
            self.assertEqual(('/cache_dir/core', '/cache_dir/agent'), result)

        mock_load_bintray_credentials.assert_called_once_with()
        core_call = call('/cache_dir', 'lightbend', 'commercial-releases', 'ConductR-Universal',
                         ('Bintray', 'username', 'password'), version='1.0.0')
        agent_call = call('/cache_dir', 'lightbend', 'commercial-releases', 'ConductR-Agent-Universal',
                          ('Bintray', 'username', 'password'), version='1.0.0')
        mock_bintray_download.assert_has_calls([core_call, agent_call])
        mock_os_rmdir.assert_has_calls([call('/cache_dir/core/sub_dir'), call('/cache_dir/agent/sub_dir')])

    def test_bintray_unreachable(self):
        mock_os_path_exists = MagicMock(side_effect=[False, False])
        mock_load_bintray_credentials = MagicMock(side_effect=ConnectionError('test only'))

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', mock_load_bintray_credentials), \
                patch('os.path.exists', mock_os_path_exists):
            self.assertRaises(BintrayUnreachableError, sandbox_run_jvm.obtain_sandbox_image, '/cache_dir', '1.0.0')

        mock_load_bintray_credentials.assert_called_once_with()

    def test_sandbox_image_not_found_on_bintray(self):
        mock_os_path_exists = MagicMock(side_effect=[False, False])
        mock_load_bintray_credentials = MagicMock(return_value=('username', 'password'))
        mock_bintray_download = MagicMock(side_effect=HTTPError('test only'))

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', mock_load_bintray_credentials), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_download', mock_bintray_download), \
                patch('os.path.exists', mock_os_path_exists):
            self.assertRaises(SandboxImageNotFoundError, sandbox_run_jvm.obtain_sandbox_image, '/cache_dir', '1.0.0')

        mock_load_bintray_credentials.assert_called_once_with()
        mock_bintray_download.assert_called_once_with('/cache_dir', 'lightbend', 'commercial-releases',
                                                      'ConductR-Universal', ('Bintray', 'username', 'password'),
                                                      version='1.0.0')

    def test_obtain_from_cache(self):
        mock_load_bintray_credentials = MagicMock()
        mock_bintray_download = MagicMock()
        mock_os_path_exists = MagicMock(side_effect=[True, True, True, True])
        mock_shutil_rmtree = MagicMock()
        mock_os_makedirs = MagicMock()
        mock_os_path_basename = MagicMock()
        mock_shutil_unpack_archive = MagicMock()
        mock_os_path_splitext = MagicMock(return_value=('sub_dir', '.tgz'))
        mock_os_listdir = MagicMock(return_value=['some-file-a', 'some-file-b'])
        mock_shutil_move = MagicMock()
        mock_os_rmdir = MagicMock()

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', mock_load_bintray_credentials), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_download', mock_bintray_download), \
                patch('os.path.exists', mock_os_path_exists), \
                patch('shutil.rmtree', mock_shutil_rmtree), \
                patch('os.makedirs', mock_os_makedirs), \
                patch('os.path.basename', mock_os_path_basename), \
                patch('shutil.unpack_archive', mock_shutil_unpack_archive), \
                patch('os.path.splitext', mock_os_path_splitext), \
                patch('os.listdir', mock_os_listdir), \
                patch('shutil.move', mock_shutil_move), \
                patch('os.rmdir', mock_os_rmdir):
            result = sandbox_run_jvm.obtain_sandbox_image('/cache_dir', '1.0.0')
            self.assertEqual(('/cache_dir/core', '/cache_dir/agent'), result)

        mock_load_bintray_credentials.assert_not_called()
        mock_bintray_download.assert_not_called()
        mock_shutil_rmtree.assert_has_calls([call('/cache_dir/core'), call('/cache_dir/agent')])
        mock_os_rmdir.assert_has_calls([call('/cache_dir/core/sub_dir'), call('/cache_dir/agent/sub_dir')])
