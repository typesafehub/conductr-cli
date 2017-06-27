from conductr_cli.test.cli_test_case import CliTestCase, as_warn, strip_margin
from conductr_cli import logging_setup, sandbox_run_jvm, sandbox_features
from conductr_cli.constants import DEFAULT_LICENSE_FILE, FEATURE_PROVIDE_PROXYING
from conductr_cli.exceptions import BindAddressNotFound, InstanceCountError, BintrayUnreachableError, \
    SandboxImageFetchError, SandboxImageNotFoundError, SandboxImageNotAvailableOfflineError, \
    SandboxUnsupportedOsError, SandboxUnsupportedOsArchError, JavaCallError, JavaUnsupportedVendorError, \
    JavaUnsupportedVersionError, JavaVersionParseError, LicenseValidationError, HostnameLookupError, \
    BintrayCredentialsNotFoundError
from conductr_cli.sandbox_features import LoggingFeature
from conductr_cli.sandbox_run_jvm import BIND_TEST_PORT
from requests.exceptions import HTTPError, ConnectionError
from unittest.mock import call, patch, MagicMock
from urllib.error import URLError
import ipaddress
import json
import semver
import subprocess
import io


class TestRun(CliTestCase):

    addr_range = ipaddress.ip_network('192.168.1.0/24', strict=True)
    tmp_dir = '~/.conductr/image/tmp'
    default_args = {
        'image_version': '2.0.0',
        'conductr_roles': [],
        'log_level': 'info',
        'nr_of_containers': 1,
        'addr_range': addr_range,
        'offline_mode': False,
        'tmp_dir': tmp_dir,
        'envs': [],
        'envs_core': [],
        'envs_agent': [],
        'args': [],
        'args_core': [],
        'args_agent': []
    }

    def test_default_args(self):
        mock_validate_jvm_support = MagicMock()
        mock_validate_hostname_lookup = MagicMock()
        mock_validate_64bit_support = MagicMock()
        mock_validate_bintray_credentials = MagicMock()
        mock_cleanup_tmp_dir = MagicMock()

        bind_addr = MagicMock()
        bind_addrs = [bind_addr]
        mock_find_bind_addrs = MagicMock(return_value=bind_addrs)

        mock_core_extracted_dir = MagicMock()
        mock_agent_extracted_dir = MagicMock()
        mock_upgrade_requirement = MagicMock()
        mock_obtain_sandbox_image = MagicMock(return_value=(mock_core_extracted_dir,
                                                            mock_agent_extracted_dir,
                                                            mock_upgrade_requirement))

        mock_sandbox_stop = MagicMock()

        mock_core_pids = MagicMock()
        mock_start_core_instances = MagicMock(return_value=mock_core_pids)

        mock_wait_for_start = MagicMock()

        mock_validate_license = MagicMock()

        mock_agent_pids = MagicMock()
        mock_start_agent_instances = MagicMock(return_value=mock_agent_pids)

        input_args = MagicMock(**self.default_args)
        features = []

        with patch('conductr_cli.sandbox_run_jvm.validate_jvm_support', mock_validate_jvm_support), \
                patch('conductr_cli.sandbox_run_jvm.validate_hostname_lookup', mock_validate_hostname_lookup), \
                patch('conductr_cli.sandbox_run_jvm.validate_64bit_support', mock_validate_64bit_support), \
                patch('conductr_cli.sandbox_run_jvm.validate_bintray_credentials', mock_validate_bintray_credentials), \
                patch('conductr_cli.sandbox_run_jvm.cleanup_tmp_dir', mock_cleanup_tmp_dir), \
                patch('conductr_cli.sandbox_run_jvm.find_bind_addrs', mock_find_bind_addrs), \
                patch('conductr_cli.sandbox_run_jvm.obtain_sandbox_image', mock_obtain_sandbox_image), \
                patch('conductr_cli.sandbox_stop.stop', mock_sandbox_stop), \
                patch('conductr_cli.sandbox_run_jvm.start_core_instances', mock_start_core_instances), \
                patch('conductr_cli.sandbox_common.wait_for_start', mock_wait_for_start), \
                patch('conductr_cli.license_validation.validate_license', mock_validate_license), \
                patch('conductr_cli.sandbox_run_jvm.start_agent_instances', mock_start_agent_instances):
            result = sandbox_run_jvm.run(input_args, features)
            expected_result = sandbox_run_jvm.SandboxRunResult(mock_core_pids, bind_addrs,
                                                               mock_agent_pids, bind_addrs,
                                                               wait_for_conductr=False,
                                                               license_validation_error=None,
                                                               sandbox_upgrade_requirements=mock_upgrade_requirement)
            self.assertEqual(expected_result, result)

        mock_sandbox_stop.assert_called_once_with(input_args)
        mock_validate_jvm_support.assert_called_once_with()
        mock_validate_hostname_lookup.assert_called_once_with()
        mock_validate_64bit_support.assert_called_once_with()
        mock_validate_bintray_credentials.assert_called_once_with('2.0.0', False)
        mock_cleanup_tmp_dir.assert_called_once_with(self.tmp_dir)
        mock_find_bind_addrs.assert_called_with(1, self.addr_range)
        mock_start_core_instances.assert_called_with(mock_core_extracted_dir,
                                                     self.tmp_dir,
                                                     [],
                                                     [],
                                                     [],
                                                     [],
                                                     bind_addrs,
                                                     [],
                                                     features,
                                                     'info')
        expected_args = sandbox_run_jvm.WaitForConductrArgs(bind_addr)
        mock_wait_for_start.assert_called_once_with(expected_args)
        mock_validate_license.assert_called_once_with('2.0.0', bind_addr, 1, DEFAULT_LICENSE_FILE)
        mock_start_agent_instances.assert_called_with(mock_agent_extracted_dir,
                                                      self.tmp_dir,
                                                      [],
                                                      [],
                                                      [],
                                                      [],
                                                      bind_addrs,
                                                      bind_addrs,
                                                      [],
                                                      features,
                                                      'info')

    def test_nr_of_core_agent_instances(self):
        mock_validate_jvm_support = MagicMock()
        mock_validate_64bit_support = MagicMock()
        mock_validate_hostname_lookup = MagicMock()
        mock_validate_bintray_credentials = MagicMock()
        mock_cleanup_tmp_dir = MagicMock()

        bind_addr1 = MagicMock()
        bind_addr2 = MagicMock()
        bind_addr3 = MagicMock()
        bind_addrs = [bind_addr1, bind_addr2, bind_addr3]
        mock_find_bind_addrs = MagicMock(return_value=bind_addrs)

        mock_core_extracted_dir = MagicMock()
        mock_agent_extracted_dir = MagicMock()
        mock_upgrade_requirement = MagicMock()
        mock_obtain_sandbox_image = MagicMock(return_value=(mock_core_extracted_dir,
                                                            mock_agent_extracted_dir,
                                                            mock_upgrade_requirement))

        mock_sandbox_stop = MagicMock()

        mock_core_pids = MagicMock()
        mock_start_core_instances = MagicMock(return_value=mock_core_pids)

        mock_wait_for_start = MagicMock()

        mock_validate_license = MagicMock()

        mock_agent_pids = MagicMock()
        mock_start_agent_instances = MagicMock(return_value=mock_agent_pids)

        args = self.default_args.copy()
        args.update({
            'nr_of_instances': '1:3'
        })
        input_args = MagicMock(**args)
        features = []

        with patch('conductr_cli.sandbox_run_jvm.validate_jvm_support', mock_validate_jvm_support), \
                patch('conductr_cli.sandbox_run_jvm.validate_hostname_lookup', mock_validate_hostname_lookup), \
                patch('conductr_cli.sandbox_run_jvm.validate_64bit_support', mock_validate_64bit_support), \
                patch('conductr_cli.sandbox_run_jvm.validate_bintray_credentials', mock_validate_bintray_credentials), \
                patch('conductr_cli.sandbox_run_jvm.cleanup_tmp_dir', mock_cleanup_tmp_dir), \
                patch('conductr_cli.sandbox_run_jvm.find_bind_addrs', mock_find_bind_addrs), \
                patch('conductr_cli.sandbox_run_jvm.obtain_sandbox_image', mock_obtain_sandbox_image), \
                patch('conductr_cli.sandbox_stop.stop', mock_sandbox_stop), \
                patch('conductr_cli.sandbox_run_jvm.start_core_instances', mock_start_core_instances), \
                patch('conductr_cli.sandbox_common.wait_for_start', mock_wait_for_start), \
                patch('conductr_cli.license_validation.validate_license', mock_validate_license), \
                patch('conductr_cli.sandbox_run_jvm.start_agent_instances', mock_start_agent_instances):
            result = sandbox_run_jvm.run(input_args, features)
            expected_result = sandbox_run_jvm.SandboxRunResult(mock_core_pids, [bind_addr1],
                                                               mock_agent_pids, [bind_addr1, bind_addr2, bind_addr3],
                                                               wait_for_conductr=False,
                                                               license_validation_error=None,
                                                               sandbox_upgrade_requirements=mock_upgrade_requirement)
            self.assertEqual(expected_result, result)

        mock_sandbox_stop.assert_called_once_with(input_args)
        mock_validate_jvm_support.assert_called_once_with()
        mock_validate_hostname_lookup.assert_called_once_with()
        mock_validate_64bit_support.assert_called_once_with()
        mock_validate_bintray_credentials.assert_called_once_with('2.0.0', False)
        mock_cleanup_tmp_dir.assert_called_once_with(self.tmp_dir)
        mock_find_bind_addrs.assert_called_with(3, self.addr_range)
        mock_start_core_instances.assert_called_with(mock_core_extracted_dir,
                                                     self.tmp_dir,
                                                     [],
                                                     [],
                                                     [],
                                                     [],
                                                     [bind_addr1],
                                                     [],
                                                     features,
                                                     'info')
        expected_args = sandbox_run_jvm.WaitForConductrArgs(bind_addr1)
        mock_wait_for_start.assert_called_once_with(expected_args)
        mock_validate_license.assert_called_once_with('2.0.0', bind_addr1, 3, DEFAULT_LICENSE_FILE)
        mock_start_agent_instances.assert_called_with(mock_agent_extracted_dir,
                                                      self.tmp_dir,
                                                      [],
                                                      [],
                                                      [],
                                                      [],
                                                      [bind_addr1, bind_addr2, bind_addr3],
                                                      [bind_addr1],
                                                      [],
                                                      features,
                                                      'info')

    def test_custom_env_args(self):
        mock_validate_jvm_support = MagicMock()
        mock_validate_hostname_lookup = MagicMock()
        mock_validate_64bit_support = MagicMock()
        mock_validate_bintray_credentials = MagicMock()
        mock_cleanup_tmp_dir = MagicMock()

        bind_addr1 = MagicMock()
        bind_addr2 = MagicMock()
        bind_addr3 = MagicMock()
        bind_addrs = [bind_addr1, bind_addr2, bind_addr3]
        mock_find_bind_addrs = MagicMock(return_value=bind_addrs)

        mock_core_extracted_dir = MagicMock()
        mock_agent_extracted_dir = MagicMock()
        mock_upgrade_requirement = MagicMock()
        mock_obtain_sandbox_image = MagicMock(return_value=(mock_core_extracted_dir,
                                                            mock_agent_extracted_dir,
                                                            mock_upgrade_requirement))

        mock_sandbox_stop = MagicMock()

        mock_core_pids = MagicMock()
        mock_start_core_instances = MagicMock(return_value=mock_core_pids)

        mock_wait_for_start = MagicMock()

        mock_validate_license = MagicMock()

        mock_agent_pids = MagicMock()
        mock_start_agent_instances = MagicMock(return_value=mock_agent_pids)

        envs = ['COMMON=1']
        envs_core = ['CORE=A', 'CORE_B=B']
        envs_agent = ['AGENT=X', 'AGENT_B=Y']

        args_input = ['-Dall=one']
        args_input_core = ['-Dcore=A']
        args_input_agent = ['-Dagent=B']

        args = self.default_args.copy()
        args.update({
            'envs': envs,
            'envs_core': envs_core,
            'envs_agent': envs_agent,
            'args': args_input,
            'args_core': args_input_core,
            'args_agent': args_input_agent,
        })
        input_args = MagicMock(**args)
        features = []

        with patch('conductr_cli.sandbox_run_jvm.validate_jvm_support', mock_validate_jvm_support), \
                patch('conductr_cli.sandbox_run_jvm.validate_hostname_lookup', mock_validate_hostname_lookup), \
                patch('conductr_cli.sandbox_run_jvm.validate_64bit_support', mock_validate_64bit_support), \
                patch('conductr_cli.sandbox_run_jvm.validate_bintray_credentials', mock_validate_bintray_credentials), \
                patch('conductr_cli.sandbox_run_jvm.cleanup_tmp_dir', mock_cleanup_tmp_dir), \
                patch('conductr_cli.sandbox_run_jvm.find_bind_addrs', mock_find_bind_addrs), \
                patch('conductr_cli.sandbox_run_jvm.obtain_sandbox_image', mock_obtain_sandbox_image), \
                patch('conductr_cli.sandbox_stop.stop', mock_sandbox_stop), \
                patch('conductr_cli.sandbox_run_jvm.start_core_instances', mock_start_core_instances), \
                patch('conductr_cli.sandbox_common.wait_for_start', mock_wait_for_start), \
                patch('conductr_cli.license_validation.validate_license', mock_validate_license), \
                patch('conductr_cli.sandbox_run_jvm.start_agent_instances', mock_start_agent_instances):
            result = sandbox_run_jvm.run(input_args, features)
            expected_result = sandbox_run_jvm.SandboxRunResult(mock_core_pids, [bind_addr1],
                                                               mock_agent_pids, [bind_addr1],
                                                               wait_for_conductr=False,
                                                               license_validation_error=None,
                                                               sandbox_upgrade_requirements=mock_upgrade_requirement)
            self.assertEqual(expected_result, result)

        mock_sandbox_stop.assert_called_once_with(input_args)
        mock_validate_jvm_support.assert_called_once_with()
        mock_validate_hostname_lookup.assert_called_once_with()
        mock_validate_64bit_support.assert_called_once_with()
        mock_validate_bintray_credentials.assert_called_once_with('2.0.0', False)
        mock_find_bind_addrs.assert_called_with(1, self.addr_range)
        mock_start_core_instances.assert_called_with(mock_core_extracted_dir,
                                                     self.tmp_dir,
                                                     envs,
                                                     envs_core,
                                                     args_input,
                                                     args_input_core,
                                                     [bind_addr1],
                                                     [],
                                                     features,
                                                     'info')
        expected_args = sandbox_run_jvm.WaitForConductrArgs(bind_addr1)
        mock_wait_for_start.assert_called_once_with(expected_args)
        mock_validate_license.assert_called_once_with('2.0.0', bind_addr1, 1, DEFAULT_LICENSE_FILE)
        mock_start_agent_instances.assert_called_with(mock_agent_extracted_dir,
                                                      self.tmp_dir,
                                                      envs,
                                                      envs_agent,
                                                      args_input,
                                                      args_input_agent,
                                                      [bind_addr1],
                                                      [bind_addr1],
                                                      [],
                                                      features,
                                                      'info')

    def test_roles(self):
        mock_validate_jvm_support = MagicMock()
        mock_validate_hostname_lookup = MagicMock()
        mock_validate_64bit_support = MagicMock()
        mock_validate_bintray_credentials = MagicMock()
        mock_cleanup_tmp_dir = MagicMock()

        bind_addr = MagicMock()
        bind_addrs = [bind_addr]
        mock_find_bind_addrs = MagicMock(return_value=bind_addrs)

        mock_core_extracted_dir = MagicMock()
        mock_agent_extracted_dir = MagicMock()
        mock_upgrade_requirement = MagicMock()
        mock_obtain_sandbox_image = MagicMock(return_value=(mock_core_extracted_dir,
                                                            mock_agent_extracted_dir,
                                                            mock_upgrade_requirement))

        mock_sandbox_stop = MagicMock()

        mock_core_pids = MagicMock()
        mock_start_core_instances = MagicMock(return_value=mock_core_pids)
        mock_wait_for_start = MagicMock()

        mock_validate_license = MagicMock()

        mock_agent_pids = MagicMock()
        mock_start_agent_instances = MagicMock(return_value=mock_agent_pids)

        args = self.default_args.copy()
        args.update({
            'conductr_roles': [['role1', 'role2'], ['role3']]
        })
        input_args = MagicMock(**args)

        mock_feature = MagicMock()
        features = [mock_feature]

        with patch('conductr_cli.sandbox_run_jvm.validate_jvm_support', mock_validate_jvm_support), \
                patch('conductr_cli.sandbox_run_jvm.validate_hostname_lookup', mock_validate_hostname_lookup), \
                patch('conductr_cli.sandbox_run_jvm.validate_64bit_support', mock_validate_64bit_support), \
                patch('conductr_cli.sandbox_run_jvm.validate_bintray_credentials', mock_validate_bintray_credentials), \
                patch('conductr_cli.sandbox_run_jvm.cleanup_tmp_dir', mock_cleanup_tmp_dir), \
                patch('conductr_cli.sandbox_run_jvm.find_bind_addrs', mock_find_bind_addrs), \
                patch('conductr_cli.sandbox_run_jvm.obtain_sandbox_image', mock_obtain_sandbox_image), \
                patch('conductr_cli.sandbox_stop.stop', mock_sandbox_stop), \
                patch('conductr_cli.sandbox_run_jvm.start_core_instances', mock_start_core_instances), \
                patch('conductr_cli.sandbox_common.wait_for_start', mock_wait_for_start), \
                patch('conductr_cli.license_validation.validate_license', mock_validate_license), \
                patch('conductr_cli.sandbox_run_jvm.start_agent_instances', mock_start_agent_instances):
            result = sandbox_run_jvm.run(input_args, features)
            expected_result = sandbox_run_jvm.SandboxRunResult(mock_core_pids, bind_addrs,
                                                               mock_agent_pids, bind_addrs,
                                                               wait_for_conductr=False,
                                                               license_validation_error=None,
                                                               sandbox_upgrade_requirements=mock_upgrade_requirement)
            self.assertEqual(expected_result, result)

        mock_sandbox_stop.assert_called_once_with(input_args)
        mock_validate_jvm_support.assert_called_once_with()
        mock_validate_hostname_lookup.assert_called_once_with()
        mock_validate_64bit_support.assert_called_once_with()
        mock_validate_bintray_credentials.assert_called_once_with('2.0.0', False)
        mock_cleanup_tmp_dir.assert_called_once_with(self.tmp_dir)
        mock_find_bind_addrs.assert_called_with(1, self.addr_range)
        mock_start_core_instances.assert_called_with(mock_core_extracted_dir,
                                                     self.tmp_dir,
                                                     [],
                                                     [],
                                                     [],
                                                     [],
                                                     bind_addrs,
                                                     [['role1', 'role2'], ['role3']],
                                                     features,
                                                     'info')
        expected_args = sandbox_run_jvm.WaitForConductrArgs(bind_addrs[0])
        mock_wait_for_start.assert_called_once_with(expected_args)
        mock_validate_license.assert_called_once_with('2.0.0', bind_addr, 1, DEFAULT_LICENSE_FILE)
        mock_start_agent_instances.assert_called_with(mock_agent_extracted_dir,
                                                      self.tmp_dir,
                                                      [],
                                                      [],
                                                      [],
                                                      [],
                                                      bind_addrs,
                                                      bind_addrs,
                                                      [['role1', 'role2'], ['role3']],
                                                      features,
                                                      'info')

    def test_license_validation_error(self):
        mock_validate_jvm_support = MagicMock()
        mock_validate_hostname_lookup = MagicMock()
        mock_validate_64bit_support = MagicMock()
        mock_validate_bintray_credentials = MagicMock()
        mock_cleanup_tmp_dir = MagicMock()

        bind_addr = MagicMock()
        bind_addrs = [bind_addr]
        mock_find_bind_addrs = MagicMock(return_value=bind_addrs)

        mock_core_extracted_dir = MagicMock()
        mock_agent_extracted_dir = MagicMock()
        mock_upgrade_requirement = MagicMock()
        mock_obtain_sandbox_image = MagicMock(return_value=(mock_core_extracted_dir,
                                                            mock_agent_extracted_dir,
                                                            mock_upgrade_requirement))
        mock_wait_for_start = MagicMock()

        mock_sandbox_stop = MagicMock()

        mock_core_pids = MagicMock()
        mock_start_core_instances = MagicMock(return_value=mock_core_pids)

        license_validation_error = LicenseValidationError('test only')
        mock_validate_license = MagicMock(side_effect=license_validation_error)

        mock_agent_pids = MagicMock()
        mock_start_agent_instances = MagicMock(return_value=mock_agent_pids)

        input_args = MagicMock(**self.default_args)
        features = []

        with patch('conductr_cli.sandbox_run_jvm.validate_jvm_support', mock_validate_jvm_support), \
                patch('conductr_cli.sandbox_run_jvm.validate_hostname_lookup', mock_validate_hostname_lookup), \
                patch('conductr_cli.sandbox_run_jvm.validate_64bit_support', mock_validate_64bit_support), \
                patch('conductr_cli.sandbox_run_jvm.validate_bintray_credentials', mock_validate_bintray_credentials), \
                patch('conductr_cli.sandbox_run_jvm.cleanup_tmp_dir', mock_cleanup_tmp_dir), \
                patch('conductr_cli.sandbox_run_jvm.find_bind_addrs', mock_find_bind_addrs), \
                patch('conductr_cli.sandbox_run_jvm.obtain_sandbox_image', mock_obtain_sandbox_image), \
                patch('conductr_cli.sandbox_common.wait_for_start', mock_wait_for_start), \
                patch('conductr_cli.sandbox_stop.stop', mock_sandbox_stop), \
                patch('conductr_cli.sandbox_run_jvm.start_core_instances', mock_start_core_instances), \
                patch('conductr_cli.license_validation.validate_license', mock_validate_license), \
                patch('conductr_cli.sandbox_run_jvm.start_agent_instances', mock_start_agent_instances):
            result = sandbox_run_jvm.run(input_args, features)
            expected_result = sandbox_run_jvm.SandboxRunResult(mock_core_pids, bind_addrs,
                                                               mock_agent_pids, bind_addrs,
                                                               wait_for_conductr=False,
                                                               license_validation_error=license_validation_error,
                                                               sandbox_upgrade_requirements=mock_upgrade_requirement)
            self.assertEqual(expected_result, result)

        mock_validate_jvm_support.assert_called_once_with()
        mock_validate_hostname_lookup.assert_called_once_with()
        mock_validate_64bit_support.assert_called_once_with()
        mock_validate_bintray_credentials.assert_called_once_with('2.0.0', False)
        mock_cleanup_tmp_dir.assert_called_once_with(self.tmp_dir)
        mock_find_bind_addrs.assert_called_with(1, self.addr_range)
        mock_start_core_instances.assert_called_with(mock_core_extracted_dir,
                                                     self.tmp_dir,
                                                     [],
                                                     [],
                                                     [],
                                                     [],
                                                     bind_addrs,
                                                     [],
                                                     features,
                                                     'info')
        expected_args = sandbox_run_jvm.WaitForConductrArgs(bind_addr)
        mock_wait_for_start.assert_called_once_with(expected_args)
        mock_validate_license.assert_called_once_with('2.0.0', bind_addr, 1, DEFAULT_LICENSE_FILE)
        mock_start_agent_instances.assert_called_with(mock_agent_extracted_dir,
                                                      self.tmp_dir,
                                                      [],
                                                      [],
                                                      [],
                                                      [],
                                                      bind_addrs,
                                                      bind_addrs,
                                                      [],
                                                      features,
                                                      'info')


class TestInstanceCount(CliTestCase):
    def test_x_y_format(self):
        nr_of_core_instances, nr_of_agent_instances = sandbox_run_jvm.instance_count(2, '2:3')
        self.assertEqual(nr_of_core_instances, 2)
        self.assertEqual(nr_of_agent_instances, 3)

    def test_number_format(self):
        nr_of_core_instances, nr_of_agent_instances = sandbox_run_jvm.instance_count(2, '5')
        self.assertEqual(nr_of_core_instances, 1)
        self.assertEqual(nr_of_agent_instances, 5)

    def test_invalid_format(self):
        self.assertRaises(InstanceCountError, sandbox_run_jvm.instance_count, 2, 'FOO')


class TestFindBindAddresses(CliTestCase):
    nr_of_instances = 3
    addr_range = ipaddress.ip_network('192.168.1.0/24', strict=True)

    def test_bind_addrs_exist(self):
        mock_can_bind = MagicMock(return_value=True)
        mock_addr_alias_commands = MagicMock(return_value='test')
        mock_subprocess_check_call = MagicMock()

        with patch('conductr_cli.host.can_bind', mock_can_bind), \
                patch('conductr_cli.host.addr_alias_commands', mock_addr_alias_commands), \
                patch('subprocess.check_call', mock_subprocess_check_call):
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

        mock_addr_alias_commands.assert_not_called()
        mock_subprocess_check_call.assert_not_called()

    def test_no_bind_addrs_exist(self):
        can_bind_first_iteration_responses = [False] * len(list(self.addr_range.hosts()))
        can_bind_second_iteration_responses = [True] * len(list(self.addr_range.hosts()))
        mock_can_bind = MagicMock(side_effect=can_bind_first_iteration_responses + can_bind_second_iteration_responses)
        mock_addr_alias_commands = MagicMock(return_value=[
            ['sudo', 'ifconfig', 'lo0', 'alias', '192.168.10.1', '255.255.255.255'],
            ['sudo', 'ifconfig', 'lo0', 'alias', '192.168.10.2', '255.255.255.255'],
            ['sudo', 'ifconfig', 'lo0', 'alias', '192.168.10.3', '255.255.255.255']
        ])
        mock_subprocess_check_call = MagicMock()

        with patch('conductr_cli.host.can_bind', mock_can_bind), \
                patch('conductr_cli.host.addr_alias_commands', mock_addr_alias_commands), \
                patch('subprocess.check_call', mock_subprocess_check_call):
            result = sandbox_run_jvm.find_bind_addrs(self.nr_of_instances, self.addr_range)
            self.assertEqual([
                ipaddress.ip_address('192.168.1.1'),
                ipaddress.ip_address('192.168.1.2'),
                ipaddress.ip_address('192.168.1.3')
            ], result)

        mock_addr_alias_commands.assert_called_once_with(
            [ipaddress.ip_address('192.168.1.1'),
             ipaddress.ip_address('192.168.1.2'),
             ipaddress.ip_address('192.168.1.3')],
            4)
        mock_subprocess_check_call.assert_has_calls([
            call(['sudo', 'ifconfig', 'lo0', 'alias', '192.168.10.1', '255.255.255.255']),
            call(['sudo', 'ifconfig', 'lo0', 'alias', '192.168.10.2', '255.255.255.255']),
            call(['sudo', 'ifconfig', 'lo0', 'alias', '192.168.10.3', '255.255.255.255'])
        ])

    def test_partial_bind_addrs_exists(self):
        can_bind_first_iteration_responses = [True] + [False] * (len(list(self.addr_range.hosts())) - 1)
        can_bind_second_iteration_responses = [True] * len(list(self.addr_range.hosts()))
        mock_can_bind = MagicMock(side_effect=can_bind_first_iteration_responses + can_bind_second_iteration_responses)
        mock_addr_alias_commands = MagicMock(return_value=[
            ['sudo', 'ifconfig', 'lo0', 'alias', '192.168.10.2', '255.255.255.255'],
            ['sudo', 'ifconfig', 'lo0', 'alias', '192.168.10.3', '255.255.255.255']
        ])
        mock_subprocess_check_call = MagicMock()

        with patch('conductr_cli.host.can_bind', mock_can_bind), \
                patch('conductr_cli.host.addr_alias_commands', mock_addr_alias_commands), \
                patch('subprocess.check_call', mock_subprocess_check_call):
            result = sandbox_run_jvm.find_bind_addrs(self.nr_of_instances, self.addr_range)
            self.assertEqual([
                ipaddress.ip_address('192.168.1.1'),
                ipaddress.ip_address('192.168.1.2'),
                ipaddress.ip_address('192.168.1.3')
            ], result)

        mock_addr_alias_commands.assert_called_once_with(
            [ipaddress.ip_address('192.168.1.2'),
             ipaddress.ip_address('192.168.1.3')],
            4)
        mock_subprocess_check_call.assert_has_calls([
            call(['sudo', 'ifconfig', 'lo0', 'alias', '192.168.10.2', '255.255.255.255']),
            call(['sudo', 'ifconfig', 'lo0', 'alias', '192.168.10.3', '255.255.255.255'])
        ])

    def test_password_prompt_exception(self):
        mock_can_bind = MagicMock(return_value=False)
        mock_addr_alias_commands = MagicMock(return_value=[
            ['sudo', 'ifconfig', 'lo0', 'alias', '192.168.10.1', '255.255.255.255'],
            ['sudo', 'ifconfig', 'lo0', 'alias', '192.168.10.2', '255.255.255.255'],
            ['sudo', 'ifconfig', 'lo0', 'alias', '192.168.10.3', '255.255.255.255']
        ])
        mock_subprocess_check_call = MagicMock(side_effect=subprocess.CalledProcessError(1, 'test'))

        with patch('conductr_cli.host.can_bind', mock_can_bind), \
                patch('conductr_cli.host.addr_alias_commands', mock_addr_alias_commands), \
                patch('subprocess.check_call', mock_subprocess_check_call):
            self.assertRaises(BindAddressNotFound,
                              sandbox_run_jvm.find_bind_addrs, self.nr_of_instances, self.addr_range)

        mock_addr_alias_commands.assert_called_once_with(
            [ipaddress.ip_address('192.168.1.1'),
             ipaddress.ip_address('192.168.1.2'),
             ipaddress.ip_address('192.168.1.3')],
            4)
        mock_subprocess_check_call.assert_called_once_with(
            ['sudo', 'ifconfig', 'lo0', 'alias', '192.168.10.1', '255.255.255.255'])

    def test_unknown_operation_system(self):
        mock_can_bind = MagicMock(return_value=False)
        mock_addr_alias_commands = MagicMock(return_value=[])
        mock_subprocess_check_call = MagicMock()

        with patch('conductr_cli.host.can_bind', mock_can_bind), \
                patch('conductr_cli.host.addr_alias_commands', mock_addr_alias_commands), \
                patch('subprocess.check_call', mock_subprocess_check_call):
            self.assertRaises(BindAddressNotFound,
                              sandbox_run_jvm.find_bind_addrs, self.nr_of_instances, self.addr_range)

        mock_addr_alias_commands.assert_called_once_with(
            [ipaddress.ip_address('192.168.1.1'),
             ipaddress.ip_address('192.168.1.2'),
             ipaddress.ip_address('192.168.1.3')],
            4)
        mock_subprocess_check_call.assert_not_called()


class TestObtainSandboxImage(CliTestCase):
    def test_obtain_macos_artefact_from_bintray(self):
        mock_is_macos = MagicMock(return_value=True)
        mock_is_64bit = MagicMock(return_value=True)
        mock_bintray_credentials = MagicMock()
        mock_load_bintray_credentials = MagicMock(return_value=mock_bintray_credentials)
        mock_download_sandbox_image = \
            MagicMock(side_effect=[
                '/cache_dir/conductr-2.0.0-Mac_OS_X-x86_64.tgz',
                '/cache_dir/conductr-agent-2.0.0-Mac_OS_X-x86_64.tgz'
            ])
        mock_check_upgrade_requirements_result = MagicMock()
        mock_check_upgrade_requirements = MagicMock(return_value=mock_check_upgrade_requirements_result)
        mock_glob = MagicMock(side_effect=[[], []])
        mock_os_path_exists = MagicMock(side_effect=[False, False])
        mock_os_makedirs = MagicMock()
        mock_os_path_basename = MagicMock()
        mock_shutil_unpack_archive = MagicMock()
        mock_os_listdir = MagicMock(side_effect=[
            ['conductr-2.0.0'],  # Top level directory inside the core archive
            ['core-some-file-a', 'core-some-file-b'],  # Extracted files from core archive
            ['conductr-agent-2.0.0'],  # Top level directory inside the agent archive
            ['agent-some-file-a', 'agent-some-file-b'],  # Extracted files from agent archive
        ])
        mock_shutil_move = MagicMock()
        mock_os_rmdir = MagicMock()

        with patch('conductr_cli.host.is_macos', mock_is_macos), \
                patch('conductr_cli.host.is_64bit', mock_is_64bit), \
                patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials',
                      mock_load_bintray_credentials), \
                patch('conductr_cli.sandbox_run_jvm.download_sandbox_image', mock_download_sandbox_image), \
                patch('conductr_cli.sandbox_run_jvm.check_upgrade_requirements', mock_check_upgrade_requirements), \
                patch('glob.glob', mock_glob), \
                patch('os.path.exists', mock_os_path_exists), \
                patch('os.makedirs', mock_os_makedirs), \
                patch('os.path.basename', mock_os_path_basename), \
                patch('shutil.unpack_archive', mock_shutil_unpack_archive), \
                patch('os.listdir', mock_os_listdir), \
                patch('shutil.move', mock_shutil_move), \
                patch('os.rmdir', mock_os_rmdir):
            result = sandbox_run_jvm.obtain_sandbox_image('/cache_dir', '2.0.0', offline_mode=False)
            self.assertEqual(('/cache_dir/core', '/cache_dir/agent', mock_check_upgrade_requirements_result), result)

        mock_glob.assert_has_calls([
            call('/cache_dir/conductr-2.0.0-Mac_OS_X-*64.tgz'),
            call('/cache_dir/conductr-agent-2.0.0-Mac_OS_X-*64.tgz')
        ])

        mock_load_bintray_credentials.assert_called_once_with(raise_error=False)

        mock_download_sandbox_image.assert_has_calls([
            call(mock_bintray_credentials,
                 '/cache_dir',
                 package_name='ConductR-Universal',
                 artefact_type='core',
                 image_version='2.0.0'),
            call(mock_bintray_credentials,
                 '/cache_dir',
                 package_name='ConductR-Agent-Universal',
                 artefact_type='agent',
                 image_version='2.0.0')
        ])

        mock_check_upgrade_requirements.assert_called_once_with(mock_bintray_credentials, '/cache_dir', '2.0.0')

        mock_shutil_move.assert_has_calls([
            call('/cache_dir/core/conductr-2.0.0/core-some-file-a', '/cache_dir/core/core-some-file-a'),
            call('/cache_dir/core/conductr-2.0.0/core-some-file-b', '/cache_dir/core/core-some-file-b'),
            call('/cache_dir/agent/conductr-agent-2.0.0/agent-some-file-a', '/cache_dir/agent/agent-some-file-a'),
            call('/cache_dir/agent/conductr-agent-2.0.0/agent-some-file-b', '/cache_dir/agent/agent-some-file-b')
        ])

        mock_os_rmdir.assert_has_calls([
            call('/cache_dir/core/conductr-2.0.0'),
            call('/cache_dir/agent/conductr-agent-2.0.0')
        ])

    def test_obtain_linux_artefact_from_bintray(self):
        mock_is_macos = MagicMock(return_value=False)
        mock_is_linux = MagicMock(return_value=True)
        mock_is_64bit = MagicMock(return_value=True)
        mock_bintray_credentials = MagicMock()
        mock_load_bintray_credentials = MagicMock(return_value=mock_bintray_credentials)
        mock_download_sandbox_image = \
            MagicMock(side_effect=[
                '/cache_dir/conductr-2.0.0-Linux-x86_64.tgz',
                '/cache_dir/conductr-agent-2.0.0-Linux-x86_64.tgz'
            ])
        mock_check_upgrade_requirements_result = MagicMock()
        mock_check_upgrade_requirements = MagicMock(return_value=mock_check_upgrade_requirements_result)
        mock_glob = MagicMock(side_effect=[[], []])
        mock_os_path_exists = MagicMock(side_effect=[False, False])
        mock_os_makedirs = MagicMock()
        mock_os_path_basename = MagicMock()
        mock_shutil_unpack_archive = MagicMock()
        mock_os_listdir = MagicMock(side_effect=[
            ['conductr-2.0.0'],  # Top level directory inside the core archive
            ['core-some-file-a', 'core-some-file-b'],  # Extracted files from core archive
            ['conductr-agent-2.0.0'],  # Top level directory inside the agent archive
            ['agent-some-file-a', 'agent-some-file-b'],  # Extracted files from agent archive
        ])
        mock_shutil_move = MagicMock()
        mock_os_rmdir = MagicMock()

        with patch('conductr_cli.host.is_macos', mock_is_macos), \
                patch('conductr_cli.host.is_linux', mock_is_linux), \
                patch('conductr_cli.host.is_64bit', mock_is_64bit), \
                patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials',
                      mock_load_bintray_credentials), \
                patch('conductr_cli.sandbox_run_jvm.download_sandbox_image', mock_download_sandbox_image), \
                patch('conductr_cli.sandbox_run_jvm.check_upgrade_requirements', mock_check_upgrade_requirements), \
                patch('glob.glob', mock_glob), \
                patch('os.path.exists', mock_os_path_exists), \
                patch('os.makedirs', mock_os_makedirs), \
                patch('os.path.basename', mock_os_path_basename), \
                patch('shutil.unpack_archive', mock_shutil_unpack_archive), \
                patch('os.listdir', mock_os_listdir), \
                patch('shutil.move', mock_shutil_move), \
                patch('os.rmdir', mock_os_rmdir):
            result = sandbox_run_jvm.obtain_sandbox_image('/cache_dir', '2.0.0', offline_mode=False)
            self.assertEqual(('/cache_dir/core', '/cache_dir/agent', mock_check_upgrade_requirements_result), result)

        mock_glob.assert_has_calls([
            call('/cache_dir/conductr-2.0.0-Linux-*64.tgz'),
            call('/cache_dir/conductr-agent-2.0.0-Linux-*64.tgz')
        ])

        mock_load_bintray_credentials.assert_called_once_with(raise_error=False)

        mock_download_sandbox_image.assert_has_calls([
            call(mock_bintray_credentials,
                 '/cache_dir',
                 package_name='ConductR-Universal',
                 image_version='2.0.0',
                 artefact_type='core'),
            call(mock_bintray_credentials,
                 '/cache_dir',
                 package_name='ConductR-Agent-Universal',
                 image_version='2.0.0',
                 artefact_type='agent')
        ])

        mock_check_upgrade_requirements.assert_called_once_with(mock_bintray_credentials, '/cache_dir', '2.0.0')

        mock_shutil_move.assert_has_calls([
            call('/cache_dir/core/conductr-2.0.0/core-some-file-a', '/cache_dir/core/core-some-file-a'),
            call('/cache_dir/core/conductr-2.0.0/core-some-file-b', '/cache_dir/core/core-some-file-b'),
            call('/cache_dir/agent/conductr-agent-2.0.0/agent-some-file-a', '/cache_dir/agent/agent-some-file-a'),
            call('/cache_dir/agent/conductr-agent-2.0.0/agent-some-file-b', '/cache_dir/agent/agent-some-file-b')
        ])

        mock_os_rmdir.assert_has_calls([
            call('/cache_dir/core/conductr-2.0.0'),
            call('/cache_dir/agent/conductr-agent-2.0.0')
        ])

    def test_sandbox_image_not_available_offline(self):
        mock_os_path_exists = MagicMock(side_effect=[False, False])

        with patch('os.path.exists', mock_os_path_exists):
            self.assertRaises(SandboxImageNotAvailableOfflineError,
                              sandbox_run_jvm.obtain_sandbox_image, '/cache_dir', '1.0.0', True)

    def test_obtain_from_cache(self):
        mock_bintray_credentials = MagicMock()
        mock_load_bintray_credentials = MagicMock(return_value=mock_bintray_credentials)
        mock_download_sandbox_image = MagicMock()
        mock_check_upgrade_requirements_result = MagicMock()
        mock_check_upgrade_requirements = MagicMock(return_value=mock_check_upgrade_requirements_result)
        mock_glob = MagicMock(side_effect=[
            ['~/.conductr/images/conductr-2.0.0-Mac_OS_X-*64.tgz'],
            ['~/.conductr/images/conductr-agent-2.0.0-Mac_OS_X-*64.tgz']
        ])
        mock_os_path_exists = MagicMock(side_effect=[True, True])
        mock_shutil_rmtree = MagicMock()
        mock_os_makedirs = MagicMock()
        mock_os_path_basename = MagicMock()
        mock_shutil_unpack_archive = MagicMock()
        mock_os_listdir = MagicMock(side_effect=[
            ['conductr-2.0.0'],  # Top level directory inside the core archive
            ['core-some-file-a', 'core-some-file-b'],  # Extracted files from core archive
            ['conductr-agent-2.0.0'],  # Top level directory inside the agent archive
            ['agent-some-file-a', 'agent-some-file-b'],  # Extracted files from agent archive
        ])
        mock_shutil_move = MagicMock()
        mock_os_rmdir = MagicMock()

        with patch('conductr_cli.sandbox_run_jvm.download_sandbox_image', mock_download_sandbox_image), \
                patch('conductr_cli.sandbox_run_jvm.check_upgrade_requirements', mock_check_upgrade_requirements), \
                patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials',
                      mock_load_bintray_credentials), \
                patch('glob.glob', mock_glob), \
                patch('os.path.exists', mock_os_path_exists), \
                patch('shutil.rmtree', mock_shutil_rmtree), \
                patch('os.makedirs', mock_os_makedirs), \
                patch('os.path.basename', mock_os_path_basename), \
                patch('shutil.unpack_archive', mock_shutil_unpack_archive), \
                patch('os.listdir', mock_os_listdir), \
                patch('shutil.move', mock_shutil_move), \
                patch('os.rmdir', mock_os_rmdir):
            result = sandbox_run_jvm.obtain_sandbox_image('/cache_dir', '2.0.0', offline_mode=False)
            self.assertEqual(('/cache_dir/core', '/cache_dir/agent', mock_check_upgrade_requirements_result), result)

        mock_load_bintray_credentials.assert_called_once_with(raise_error=False)
        mock_download_sandbox_image.assert_not_called()

        mock_check_upgrade_requirements.assert_called_once_with(mock_bintray_credentials, '/cache_dir', '2.0.0')

        mock_shutil_rmtree.assert_has_calls([
            call('/cache_dir/core'),
            call('/cache_dir/agent')
        ])

        mock_os_rmdir.assert_has_calls([
            call('/cache_dir/core/conductr-2.0.0'),
            call('/cache_dir/agent/conductr-agent-2.0.0')
        ])

    def test_no_upgrade_requirement_check(self):
        mock_bintray_credentials = MagicMock()
        mock_load_bintray_credentials = MagicMock(return_value=mock_bintray_credentials)
        mock_download_sandbox_image = MagicMock()
        mock_check_upgrade_requirements = MagicMock()
        mock_glob = MagicMock(side_effect=[
            ['~/.conductr/images/conductr-2.0.0-Mac_OS_X-*64.tgz'],
            ['~/.conductr/images/conductr-agent-2.0.0-Mac_OS_X-*64.tgz']
        ])
        mock_os_path_exists = MagicMock(side_effect=[True, True])
        mock_shutil_rmtree = MagicMock()
        mock_os_makedirs = MagicMock()
        mock_os_path_basename = MagicMock()
        mock_shutil_unpack_archive = MagicMock()
        mock_os_listdir = MagicMock(side_effect=[
            ['conductr-2.0.0'],  # Top level directory inside the core archive
            ['core-some-file-a', 'core-some-file-b'],  # Extracted files from core archive
            ['conductr-agent-2.0.0'],  # Top level directory inside the agent archive
            ['agent-some-file-a', 'agent-some-file-b'],  # Extracted files from agent archive
        ])
        mock_shutil_move = MagicMock()
        mock_os_rmdir = MagicMock()

        with patch('conductr_cli.sandbox_run_jvm.download_sandbox_image', mock_download_sandbox_image), \
                patch('conductr_cli.sandbox_run_jvm.check_upgrade_requirements', mock_check_upgrade_requirements), \
                patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials',
                      mock_load_bintray_credentials), \
                patch('glob.glob', mock_glob), \
                patch('os.path.exists', mock_os_path_exists), \
                patch('shutil.rmtree', mock_shutil_rmtree), \
                patch('os.makedirs', mock_os_makedirs), \
                patch('os.path.basename', mock_os_path_basename), \
                patch('shutil.unpack_archive', mock_shutil_unpack_archive), \
                patch('os.listdir', mock_os_listdir), \
                patch('shutil.move', mock_shutil_move), \
                patch('os.rmdir', mock_os_rmdir):
            result = sandbox_run_jvm.obtain_sandbox_image('/cache_dir', '2.0.0', offline_mode=True)
            self.assertEqual(('/cache_dir/core', '/cache_dir/agent', None), result)

        mock_load_bintray_credentials.assert_called_once_with(raise_error=False)
        mock_download_sandbox_image.assert_not_called()
        mock_check_upgrade_requirements.assert_not_called()

        mock_shutil_rmtree.assert_has_calls([
            call('/cache_dir/core'),
            call('/cache_dir/agent')
        ])

        mock_os_rmdir.assert_has_calls([
            call('/cache_dir/core/conductr-2.0.0'),
            call('/cache_dir/agent/conductr-agent-2.0.0')
        ])

    def test_unsupported_os(self):
        mock_is_macos = MagicMock(return_value=False)
        mock_is_linux = MagicMock(return_value=False)
        mock_os_path_exists = MagicMock(side_effect=[False, False, False, False])

        with patch('conductr_cli.host.is_macos', mock_is_macos), \
                patch('conductr_cli.host.is_linux', mock_is_linux), \
                patch('os.path.exists', mock_os_path_exists):
            self.assertRaises(SandboxUnsupportedOsError,
                              sandbox_run_jvm.obtain_sandbox_image,
                              '/cache_dir',
                              '2.0.0',
                              offline_mode=False)


class TestStartCore(CliTestCase):
    extract_dir = '/User/tester/.conductr/images/core'

    tmp_dir = '/User/tester/.conductr/images/tmp'

    addrs = [
        ipaddress.ip_address('192.168.1.1'),
        ipaddress.ip_address('192.168.1.2'),
        ipaddress.ip_address('192.168.1.3')
    ]

    envs = ['FOO=BAR']
    core_envs = ['CORE=XYZ']
    args = ['-Dcommon=1']
    core_args = ['-Dcore=A']

    log_level = 'info'

    def test_start_instances(self):
        conductr_roles = []
        features = []

        merged_env = {'test': 'only'}
        mock_merge_with_os_envs = MagicMock(return_value=merged_env)

        mock_popen = MagicMock(side_effect=[
            self.mock_pid(1001),
            self.mock_pid(1002),
            self.mock_pid(1003)
        ])

        with patch('conductr_cli.sandbox_run_jvm.merge_with_os_envs', mock_merge_with_os_envs), \
                patch('subprocess.Popen', mock_popen):
            result = sandbox_run_jvm.start_core_instances(self.extract_dir,
                                                          self.tmp_dir,
                                                          self.envs,
                                                          self.core_envs,
                                                          self.args,
                                                          self.core_args,
                                                          self.addrs,
                                                          conductr_roles,
                                                          features,
                                                          self.log_level)
            self.assertEqual([1001, 1002, 1003], result)

        mock_merge_with_os_envs.assert_called_once_with([], self.envs, self.core_envs)

        self.assertEqual([
            call([
                '{}/bin/conductr'.format(self.extract_dir),
                '-Djava.io.tmpdir={}'.format(self.tmp_dir),
                '-Dakka.loglevel={}'.format(self.log_level),
                '-Dconductr.ip={}'.format(self.addrs[0]),
                '-Dconductr.resource-provider.match-offer-roles=off',
                '-Dcommon=1',
                '-Dcore=A'
            ], cwd=self.extract_dir, start_new_session=True, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, env=merged_env),
            call([
                '{}/bin/conductr'.format(self.extract_dir),
                '-Djava.io.tmpdir={}'.format(self.tmp_dir),
                '-Dakka.loglevel={}'.format(self.log_level),
                '-Dconductr.ip={}'.format(self.addrs[1]),
                '-Dconductr.resource-provider.match-offer-roles=off',
                '-Dcommon=1',
                '-Dcore=A',
                '--seed', '{}:9004'.format(self.addrs[0])
            ], cwd=self.extract_dir, start_new_session=True, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, env=merged_env),
            call([
                '{}/bin/conductr'.format(self.extract_dir),
                '-Djava.io.tmpdir={}'.format(self.tmp_dir),
                '-Dakka.loglevel={}'.format(self.log_level),
                '-Dconductr.ip={}'.format(self.addrs[2]),
                '-Dconductr.resource-provider.match-offer-roles=off',
                '-Dcommon=1',
                '-Dcore=A',
                '--seed', '{}:9004'.format(self.addrs[0])
            ], cwd=self.extract_dir, start_new_session=True, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, env=merged_env),
        ], mock_popen.call_args_list)

    def test_roles_and_features(self):
        conductr_roles = [['role1', 'role2'], ['role3']]

        mock_feature = MagicMock(**{
            'conductr_core_envs': lambda: ['CORE_TEST=1']
        })

        features = [
            LoggingFeature("v1", "2.0.0", offline_mode=False),
            mock_feature
        ]

        merged_env = {'test': 'only'}
        mock_merge_with_os_envs = MagicMock(return_value=merged_env)

        mock_popen = MagicMock(side_effect=[
            self.mock_pid(1001),
            self.mock_pid(1002),
            self.mock_pid(1003)
        ])

        with patch('conductr_cli.sandbox_run_jvm.merge_with_os_envs', mock_merge_with_os_envs), \
                patch('subprocess.Popen', mock_popen):
            result = sandbox_run_jvm.start_core_instances(self.extract_dir,
                                                          self.tmp_dir,
                                                          self.envs,
                                                          self.core_envs,
                                                          self.args,
                                                          self.core_args,
                                                          self.addrs,
                                                          conductr_roles,
                                                          features,
                                                          self.log_level)
            self.assertEqual([1001, 1002, 1003], result)

        self.assertEqual(mock_feature.method_calls, [
            call.conductr_pre_core_start(
                self.envs, self.core_envs, self.args, self.core_args, self.extract_dir, self.addrs, conductr_roles
            ),
            call.conductr_roles(),
            call.conductr_args()
        ])

        mock_merge_with_os_envs.assert_called_once_with(['CORE_TEST=1'], self.envs, self.core_envs)

        self.assertEqual([
            call([
                '{}/bin/conductr'.format(self.extract_dir),
                '-Djava.io.tmpdir={}'.format(self.tmp_dir),
                '-Dakka.loglevel={}'.format(self.log_level),
                '-Dconductr.ip={}'.format(self.addrs[0]),
                '-Dconductr.resource-provider.match-offer-roles=on',
                '-Dcommon=1',
                '-Dcore=A',
                '-Dcontrail.syslog.server.port=9200',
                '-Dcontrail.syslog.server.elasticsearch.enabled=on'
            ], cwd=self.extract_dir, start_new_session=True, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, env=merged_env),
            call([
                '{}/bin/conductr'.format(self.extract_dir),
                '-Djava.io.tmpdir={}'.format(self.tmp_dir),
                '-Dakka.loglevel={}'.format(self.log_level),
                '-Dconductr.ip={}'.format(self.addrs[1]),
                '-Dconductr.resource-provider.match-offer-roles=on',
                '-Dcommon=1',
                '-Dcore=A',
                '-Dcontrail.syslog.server.port=9200',
                '-Dcontrail.syslog.server.elasticsearch.enabled=on',
                '--seed', '{}:9004'.format(self.addrs[0])
            ], cwd=self.extract_dir, start_new_session=True, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, env=merged_env),
            call([
                '{}/bin/conductr'.format(self.extract_dir),
                '-Djava.io.tmpdir={}'.format(self.tmp_dir),
                '-Dakka.loglevel={}'.format(self.log_level),
                '-Dconductr.ip={}'.format(self.addrs[2]),
                '-Dconductr.resource-provider.match-offer-roles=on',
                '-Dcommon=1',
                '-Dcore=A',
                '-Dcontrail.syslog.server.port=9200',
                '-Dcontrail.syslog.server.elasticsearch.enabled=on',
                '--seed', '{}:9004'.format(self.addrs[0])
            ], cwd=self.extract_dir, start_new_session=True, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, env=merged_env),
        ], mock_popen.call_args_list)

    def mock_pid(self, pid_value):
        mock_process = MagicMock()
        mock_process.pid = pid_value
        return mock_process


class TestStartAgent(CliTestCase):
    extract_dir = '/User/tester/.conductr/images/agent'

    tmp_dir = '/User/tester/.conductr/images/tmp'

    addrs = [
        ipaddress.ip_address('192.168.1.1'),
        ipaddress.ip_address('192.168.1.2'),
        ipaddress.ip_address('192.168.1.3')
    ]

    envs = ['FOO=BAR']
    agent_envs = ['AGENT=XYZ']

    args = ['-Dcommon=1']
    agent_args = ['-Dagent=A']

    log_level = 'info'

    def test_start_instances(self):
        merged_env = {'test': 'only'}
        mock_merge_with_os_envs = MagicMock(return_value=merged_env)

        mock_popen = MagicMock(side_effect=[
            self.mock_pid(1001),
            self.mock_pid(1002),
            self.mock_pid(1003)
        ])

        with patch('conductr_cli.sandbox_run_jvm.merge_with_os_envs', mock_merge_with_os_envs), \
                patch('subprocess.Popen', mock_popen):
            result = sandbox_run_jvm.start_agent_instances(self.extract_dir,
                                                           self.tmp_dir,
                                                           self.envs,
                                                           self.agent_envs,
                                                           self.args,
                                                           self.agent_args,
                                                           self.addrs,
                                                           self.addrs,
                                                           conductr_roles=[],
                                                           features=[],
                                                           log_level=self.log_level)
            self.assertEqual([1001, 1002, 1003], result)

        mock_merge_with_os_envs.assert_called_once_with([], self.envs, self.agent_envs)

        self.assertEqual([
            call([
                '{}/bin/conductr-agent'.format(self.extract_dir),
                '-Djava.io.tmpdir={}'.format(self.tmp_dir),
                '-Dakka.loglevel={}'.format(self.log_level),
                '-Dconductr.agent.ip={}'.format(self.addrs[0]),
                '--core-node', '{}:9004'.format(self.addrs[0]),
                '-Dcommon=1',
                '-Dagent=A'
            ], cwd=self.extract_dir, start_new_session=True, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, env=merged_env),
            call([
                '{}/bin/conductr-agent'.format(self.extract_dir),
                '-Djava.io.tmpdir={}'.format(self.tmp_dir),
                '-Dakka.loglevel={}'.format(self.log_level),
                '-Dconductr.agent.ip={}'.format(self.addrs[1]),
                '--core-node', '{}:9004'.format(self.addrs[1]),
                '-Dcommon=1',
                '-Dagent=A'
            ], cwd=self.extract_dir, start_new_session=True, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, env=merged_env),
            call([
                '{}/bin/conductr-agent'.format(self.extract_dir),
                '-Djava.io.tmpdir={}'.format(self.tmp_dir),
                '-Dakka.loglevel={}'.format(self.log_level),
                '-Dconductr.agent.ip={}'.format(self.addrs[2]),
                '--core-node', '{}:9004'.format(self.addrs[2]),
                '-Dcommon=1',
                '-Dagent=A'
            ], cwd=self.extract_dir, start_new_session=True, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, env=merged_env),
        ], mock_popen.call_args_list)

    def test_start_linux(self):
        mock_popen = MagicMock(side_effect=[
            self.mock_pid(1001),
            self.mock_pid(1002),
            self.mock_pid(1003)
        ])

        with patch('subprocess.Popen', mock_popen), patch('conductr_cli.host.is_linux', lambda: True):
            sandbox_run_jvm.start_agent_instances(self.extract_dir,
                                                  self.tmp_dir,
                                                  self.envs,
                                                  self.agent_envs,
                                                  self.args,
                                                  self.agent_args,
                                                  self.addrs,
                                                  self.addrs,
                                                  conductr_roles=[],
                                                  features=[],
                                                  log_level=self.log_level)

        for c in mock_popen.call_args_list:
            args, kwargs = c

            self.assertFalse(any(any('-Dconductr.agent.run.force-oci-docker=on' in a for a in c) for c in args))

    def test_start_non_linux_has_docker(self):
        mock_popen = MagicMock(side_effect=[
            self.mock_pid(1001),
            self.mock_pid(1002),
            self.mock_pid(1003)
        ])

        mock_oci_docker_start = MagicMock()

        with \
                patch('subprocess.Popen', mock_popen), \
                patch('conductr_cli.docker.is_docker_present', lambda: True), \
                patch('conductr_cli.host.is_linux', lambda: False), \
                patch('conductr_cli.sandbox_features.OciInDockerFeature.start', mock_oci_docker_start), \
                patch('conductr_cli.sandbox_features.OciInDockerFeature.extract_image_name', lambda _1, _2: 'image'):
            sandbox_run_jvm.start_agent_instances(self.extract_dir,
                                                  self.tmp_dir,
                                                  self.envs,
                                                  self.agent_envs,
                                                  self.args,
                                                  self.agent_args,
                                                  self.addrs,
                                                  self.addrs,
                                                  conductr_roles=[],
                                                  features=sandbox_features.collect_features(
                                                      [],
                                                      no_default_features=False,
                                                      image_version='2.0.0',
                                                      offline_mode=False
                                                  ),
                                                  log_level=self.log_level)

        for c in mock_popen.call_args_list:
            args, kwargs = c

            self.assertTrue(all(any('-Dconductr.agent.run.force-oci-docker=on' in a for a in c) for c in args))

    def test_start_non_linux_no_docker(self):
        mock_popen = MagicMock(side_effect=[
            self.mock_pid(1001),
            self.mock_pid(1002),
            self.mock_pid(1003)
        ])

        mock_oci_docker_start = MagicMock()

        with \
                patch('subprocess.Popen', mock_popen), \
                patch('conductr_cli.docker.is_docker_present', lambda: False), \
                patch('conductr_cli.host.is_linux', lambda: False), \
                patch('conductr_cli.sandbox_features.OciInDockerFeature.extract_image_name', lambda _1, _2: 'image'), \
                patch('conductr_cli.sandbox_features.OciInDockerFeature.start', mock_oci_docker_start):
            sandbox_run_jvm.start_agent_instances(self.extract_dir,
                                                  self.tmp_dir,
                                                  self.envs,
                                                  self.agent_envs,
                                                  self.args,
                                                  self.agent_args,
                                                  self.addrs,
                                                  self.addrs,
                                                  conductr_roles=[],
                                                  features=sandbox_features.collect_features(
                                                      [],
                                                      no_default_features=False,
                                                      image_version='2.0.0',
                                                      offline_mode=False
                                                  ),
                                                  log_level=self.log_level)

        for c in mock_popen.call_args_list:
            args, kwargs = c

            self.assertFalse(any(any('-Dconductr.agent.run.force-oci-docker=on' in a for a in c) for c in args))

    def test_roles_and_features(self):
        merged_env = {'test': 'only'}
        mock_merge_with_os_envs = MagicMock(return_value=merged_env)

        mock_popen = MagicMock(side_effect=[
            self.mock_pid(1001),
            self.mock_pid(1002),
            self.mock_pid(1003)
        ])

        mock_feature = MagicMock(**{
            'conductr_agent_envs': lambda: ['AGENT_TEST=1']
        })

        conductr_roles = [['role1', 'role2'], ['role3']]
        features = [
            LoggingFeature('v2', '2.0.0', offline_mode=False),
            mock_feature
        ]

        with patch('conductr_cli.sandbox_run_jvm.merge_with_os_envs', mock_merge_with_os_envs), \
                patch('subprocess.Popen', mock_popen):
            result = sandbox_run_jvm.start_agent_instances(self.extract_dir,
                                                           self.tmp_dir,
                                                           self.envs,
                                                           self.agent_envs,
                                                           self.args,
                                                           self.agent_args,
                                                           self.addrs,
                                                           self.addrs,
                                                           conductr_roles=conductr_roles,
                                                           features=features,
                                                           log_level=self.log_level)
            self.assertEqual([1001, 1002, 1003], result)

        mock_merge_with_os_envs.assert_called_once_with(
            ['AGENT_TEST=1'],
            self.envs,
            self.agent_envs
        )

        self.assertEqual(mock_feature.method_calls, [
            call.conductr_pre_agent_start(
                self.envs,
                self.agent_envs,
                self.args,
                self.agent_args,
                self.extract_dir,
                self.addrs,
                self.addrs,
                conductr_roles
            ),
            call.conductr_roles(),
            call.conductr_args()
        ])

        self.assertEqual([
            call([
                '{}/bin/conductr-agent'.format(self.extract_dir),
                '-Djava.io.tmpdir={}'.format(self.tmp_dir),
                '-Dakka.loglevel={}'.format(self.log_level),
                '-Dconductr.agent.ip={}'.format(self.addrs[0]),
                '--core-node', '{}:9004'.format(self.addrs[0]),
                '-Dconductr.agent.roles.0=role1',
                '-Dconductr.agent.roles.1=role2',
                '-Dconductr.agent.roles.2=elasticsearch',
                '-Dconductr.agent.roles.3=kibana',
                '-Dcommon=1',
                '-Dagent=A',
                '-Dcontrail.syslog.server.port=9200',
                '-Dcontrail.syslog.server.elasticsearch.enabled=on'
            ], cwd=self.extract_dir, start_new_session=True, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, env=merged_env),
            call([
                '{}/bin/conductr-agent'.format(self.extract_dir),
                '-Djava.io.tmpdir={}'.format(self.tmp_dir),
                '-Dakka.loglevel={}'.format(self.log_level),
                '-Dconductr.agent.ip={}'.format(self.addrs[1]),
                '--core-node', '{}:9004'.format(self.addrs[1]),
                '-Dconductr.agent.roles.0=role3',
                '-Dcommon=1',
                '-Dagent=A',
                '-Dcontrail.syslog.server.port=9200',
                '-Dcontrail.syslog.server.elasticsearch.enabled=on'
            ], cwd=self.extract_dir, start_new_session=True, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, env=merged_env),
            call([
                '{}/bin/conductr-agent'.format(self.extract_dir),
                '-Djava.io.tmpdir={}'.format(self.tmp_dir),
                '-Dakka.loglevel={}'.format(self.log_level),
                '-Dconductr.agent.ip={}'.format(self.addrs[2]),
                '--core-node', '{}:9004'.format(self.addrs[2]),
                '-Dconductr.agent.roles.0=role1',
                '-Dconductr.agent.roles.1=role2',
                '-Dcommon=1',
                '-Dagent=A',
                '-Dcontrail.syslog.server.port=9200',
                '-Dcontrail.syslog.server.elasticsearch.enabled=on',
            ], cwd=self.extract_dir, start_new_session=True, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, env=merged_env),
        ], mock_popen.call_args_list)

    def test_start_instances_with_less_number_of_core_nodes(self):
        merged_env = {'test': 'only'}
        mock_merge_with_os_envs = MagicMock(return_value=merged_env)

        mock_popen = MagicMock(side_effect=[
            self.mock_pid(1001),
            self.mock_pid(1002),
            self.mock_pid(1003)
        ])

        conductr_roles = []
        features = []

        with patch('conductr_cli.sandbox_run_jvm.merge_with_os_envs', mock_merge_with_os_envs), \
                patch('subprocess.Popen', mock_popen):
            result = sandbox_run_jvm.start_agent_instances(self.extract_dir,
                                                           self.tmp_dir,
                                                           self.envs,
                                                           self.agent_envs,
                                                           self.args,
                                                           self.agent_args,
                                                           self.addrs,
                                                           self.addrs[0:2],
                                                           conductr_roles=conductr_roles,
                                                           features=features,
                                                           log_level=self.log_level)
            self.assertEqual([1001, 1002, 1003], result)

        mock_merge_with_os_envs.assert_called_once_with([], self.envs, self.agent_envs)

        self.assertEqual([
            call([
                '{}/bin/conductr-agent'.format(self.extract_dir),
                '-Djava.io.tmpdir={}'.format(self.tmp_dir),
                '-Dakka.loglevel={}'.format(self.log_level),
                '-Dconductr.agent.ip={}'.format(self.addrs[0]),
                '--core-node', '{}:9004'.format(self.addrs[0]),
                '-Dcommon=1',
                '-Dagent=A'
            ], cwd=self.extract_dir, start_new_session=True, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, env=merged_env),
            call([
                '{}/bin/conductr-agent'.format(self.extract_dir),
                '-Djava.io.tmpdir={}'.format(self.tmp_dir),
                '-Dakka.loglevel={}'.format(self.log_level),
                '-Dconductr.agent.ip={}'.format(self.addrs[1]),
                '--core-node', '{}:9004'.format(self.addrs[1]),
                '-Dcommon=1',
                '-Dagent=A'
            ], cwd=self.extract_dir, start_new_session=True, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, env=merged_env),
            call([
                '{}/bin/conductr-agent'.format(self.extract_dir),
                '-Djava.io.tmpdir={}'.format(self.tmp_dir),
                '-Dakka.loglevel={}'.format(self.log_level),
                '-Dconductr.agent.ip={}'.format(self.addrs[2]),
                '--core-node', '{}:9004'.format(self.addrs[0]),
                '-Dcommon=1',
                '-Dagent=A'
            ], cwd=self.extract_dir, start_new_session=True, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, env=merged_env),
        ], mock_popen.call_args_list)

    def mock_pid(self, pid_value):
        mock_process = MagicMock()
        mock_process.pid = pid_value
        return mock_process


class TestLogRunAttempt(CliTestCase):
    wait_timeout = 60
    run_result = sandbox_run_jvm.SandboxRunResult(
        [1001, 1002, 1003],
        [ipaddress.ip_address('192.168.1.1'), ipaddress.ip_address('192.168.1.2'), ipaddress.ip_address('192.168.1.3')],
        [2001, 2002, 2003],
        [ipaddress.ip_address('192.168.1.1'), ipaddress.ip_address('192.168.1.2'), ipaddress.ip_address('192.168.1.3')],
        wait_for_conductr=True,
        license_validation_error=None,
        sandbox_upgrade_requirements=None
    )
    feature_results = [sandbox_features.BundleStartResult('bundle-a', 1001),
                       sandbox_features.BundleStartResult('bundle-b', 1002)]

    def test_log_output(self):
        run_mock = MagicMock()
        stdout = MagicMock()
        input_args = MagicMock(**{
            'bundle_http_port': 9000
        })

        with patch('conductr_cli.conduct_main.run', run_mock):
            logging_setup.configure_logging(input_args, stdout)
            sandbox_run_jvm.log_run_attempt(
                input_args,
                run_result=self.run_result,
                feature_results=self.feature_results,
                feature_provided=[FEATURE_PROVIDE_PROXYING]
            )

        run_mock.assert_called_with(['info', '--host', '192.168.1.1'], configure_logging=False)

        expected_stdout = strip_margin("""||------------------------------------------------|
                                          || Summary                                        |
                                          ||------------------------------------------------|
                                          ||- - - - - - - - - - - - - - - - - - - - - - - - |
                                          || ConductR                                       |
                                          ||- - - - - - - - - - - - - - - - - - - - - - - - |
                                          |ConductR has been started:
                                          |  core instances on 192.168.1.1, 192.168.1.2, 192.168.1.3
                                          |  agent instances on 192.168.1.1, 192.168.1.2, 192.168.1.3
                                          |ConductR service locator has been started on:
                                          |  192.168.1.1:9008
                                          ||- - - - - - - - - - - - - - - - - - - - - - - - |
                                          || Proxy                                          |
                                          ||- - - - - - - - - - - - - - - - - - - - - - - - |
                                          |HAProxy has been started
                                          |By default, your bundles are accessible on:
                                          |  192.168.1.1:9000
                                          ||- - - - - - - - - - - - - - - - - - - - - - - - |
                                          || Features                                       |
                                          ||- - - - - - - - - - - - - - - - - - - - - - - - |
                                          |The following feature related bundles have been started:
                                          |  bundle-a on 192.168.1.1:1001
                                          |  bundle-b on 192.168.1.1:1002
                                          ||- - - - - - - - - - - - - - - - - - - - - - - - |
                                          || Bundles                                        |
                                          ||- - - - - - - - - - - - - - - - - - - - - - - - |
                                          |Check latest bundle status with:
                                          |  conduct info
                                          |Current bundle status:
                                          |""")
        self.assertEqual(expected_stdout, self.output(stdout))

    def test_log_output_single_core_and_agent(self):
        run_result = sandbox_run_jvm.SandboxRunResult(
            [1001],
            [ipaddress.ip_address('192.168.1.1')],
            [2001],
            [ipaddress.ip_address('192.168.1.1')],
            wait_for_conductr=False,
            license_validation_error=None,
            sandbox_upgrade_requirements=None
        )

        run_mock = MagicMock()
        stdout = MagicMock()
        input_args = MagicMock(**{
            'no_wait': False,
            'bundle_http_port': 9000
        })

        with patch('conductr_cli.conduct_main.run', run_mock):
            logging_setup.configure_logging(input_args, stdout)
            sandbox_run_jvm.log_run_attempt(
                input_args,
                run_result=run_result,
                feature_results=self.feature_results,
                feature_provided=[FEATURE_PROVIDE_PROXYING]
            )

        expected_stdout = strip_margin("""||------------------------------------------------|
                                          || Summary                                        |
                                          ||------------------------------------------------|
                                          ||- - - - - - - - - - - - - - - - - - - - - - - - |
                                          || ConductR                                       |
                                          ||- - - - - - - - - - - - - - - - - - - - - - - - |
                                          |ConductR has been started:
                                          |  core instance on 192.168.1.1
                                          |  agent instance on 192.168.1.1
                                          |ConductR service locator has been started on:
                                          |  192.168.1.1:9008
                                          ||- - - - - - - - - - - - - - - - - - - - - - - - |
                                          || Proxy                                          |
                                          ||- - - - - - - - - - - - - - - - - - - - - - - - |
                                          |HAProxy has been started
                                          |By default, your bundles are accessible on:
                                          |  192.168.1.1:9000
                                          ||- - - - - - - - - - - - - - - - - - - - - - - - |
                                          || Features                                       |
                                          ||- - - - - - - - - - - - - - - - - - - - - - - - |
                                          |The following feature related bundles have been started:
                                          |  bundle-a on 192.168.1.1:1001
                                          |  bundle-b on 192.168.1.1:1002
                                          ||- - - - - - - - - - - - - - - - - - - - - - - - |
                                          || Bundles                                        |
                                          ||- - - - - - - - - - - - - - - - - - - - - - - - |
                                          |Check latest bundle status with:
                                          |  conduct info
                                          |Current bundle status:
                                          |""")
        self.assertEqual(expected_stdout, self.output(stdout))

    def test_log_output_no_proxy(self):
        run_mock = MagicMock()
        stdout = MagicMock()
        input_args = MagicMock(**{
            'no_wait': False
        })

        with patch('conductr_cli.conduct_main.run', run_mock):
            logging_setup.configure_logging(input_args, stdout)
            sandbox_run_jvm.log_run_attempt(
                input_args,
                run_result=self.run_result,
                feature_results=self.feature_results,
                feature_provided=[]
            )

        expected_stdout = strip_margin("""||------------------------------------------------|
                                          || Summary                                        |
                                          ||------------------------------------------------|
                                          ||- - - - - - - - - - - - - - - - - - - - - - - - |
                                          || ConductR                                       |
                                          ||- - - - - - - - - - - - - - - - - - - - - - - - |
                                          |ConductR has been started:
                                          |  core instances on 192.168.1.1, 192.168.1.2, 192.168.1.3
                                          |  agent instances on 192.168.1.1, 192.168.1.2, 192.168.1.3
                                          |ConductR service locator has been started on:
                                          |  192.168.1.1:9008
                                          ||- - - - - - - - - - - - - - - - - - - - - - - - |
                                          || Proxy                                          |
                                          ||- - - - - - - - - - - - - - - - - - - - - - - - |
                                          |HAProxy has not been started
                                          |To enable proxying ensure Docker is running and restart the sandbox
                                          ||- - - - - - - - - - - - - - - - - - - - - - - - |
                                          || Features                                       |
                                          ||- - - - - - - - - - - - - - - - - - - - - - - - |
                                          |The following feature related bundles have been started:
                                          |  bundle-a on 192.168.1.1:9008/services/bundle-a
                                          |  bundle-b on 192.168.1.1:9008/services/bundle-b
                                          ||- - - - - - - - - - - - - - - - - - - - - - - - |
                                          || Bundles                                        |
                                          ||- - - - - - - - - - - - - - - - - - - - - - - - |
                                          |Check latest bundle status with:
                                          |  conduct info
                                          |Current bundle status:
                                          |""")
        self.assertEqual(expected_stdout, self.output(stdout))

    def test_log_output_with_upgrade_warning(self):
        run_result = sandbox_run_jvm.SandboxRunResult(
            [1001],
            [ipaddress.ip_address('192.168.1.1')],
            [2001],
            [ipaddress.ip_address('192.168.1.1')],
            wait_for_conductr=False,
            license_validation_error=None,
            sandbox_upgrade_requirements=sandbox_run_jvm.SandboxUpgradeRequirement(
                is_upgrade_required=True,
                current_version=semver.parse_version_info('2.0.5'),
                latest_version=semver.parse_version_info('2.0.8'),
            )
        )

        run_mock = MagicMock()
        stdout = MagicMock()
        input_args = MagicMock(**{
            'no_wait': False,
            'bundle_http_port': 9000
        })

        with patch('conductr_cli.conduct_main.run', run_mock):
            logging_setup.configure_logging(input_args, stdout)
            sandbox_run_jvm.log_run_attempt(
                input_args,
                run_result=run_result,
                feature_results=[],
                feature_provided=[]
            )

        self.maxDiff = None
        expected_stdout = strip_margin("""||------------------------------------------------|
                                          || Summary                                        |
                                          ||------------------------------------------------|
                                          ||- - - - - - - - - - - - - - - - - - - - - - - - |
                                          || ConductR                                       |
                                          ||- - - - - - - - - - - - - - - - - - - - - - - - |
                                          |ConductR has been started:
                                          |  core instance on 192.168.1.1
                                          |  agent instance on 192.168.1.1
                                          |ConductR service locator has been started on:
                                          |  192.168.1.1:9008
                                          ||- - - - - - - - - - - - - - - - - - - - - - - - |
                                          || Proxy                                          |
                                          ||- - - - - - - - - - - - - - - - - - - - - - - - |
                                          |HAProxy has not been started
                                          |To enable proxying ensure Docker is running and restart the sandbox
                                          ||- - - - - - - - - - - - - - - - - - - - - - - - |
                                          || Bundles                                        |
                                          ||- - - - - - - - - - - - - - - - - - - - - - - - |
                                          |Check latest bundle status with:
                                          |  conduct info
                                          |Current bundle status:
                                          |
                                          |Warning: A newer ConductR version is available. Please upgrade the sandbox to 2.0.8 by running
                                          |Warning:   sandbox run 2.0.8
                                          |""")
        self.assertEqual(as_warn(expected_stdout), self.output(stdout))


class TestValidateJvm(CliTestCase):
    def test_supported_oracle(self):
        cmd_output = strip_margin("""|java version "1.8.0_72"
                                     |Java(TM) SE Runtime Environment (build 1.8.0_72-b15)
                                     |Java HotSpot(TM) 64-Bit Server VM (build 25.72-b15, mixed mode)
                                     |""")
        mock_getoutput = MagicMock(return_value=cmd_output)

        with patch('subprocess.getoutput', mock_getoutput):
            sandbox_run_jvm.validate_jvm_support()

        mock_getoutput.assert_called_once_with('java -version')

    def test_supported_open_jdk(self):
        cmd_output = strip_margin("""|openjdk version "1.8.0_111"
                                     |OpenJDK Runtime Environment (build 1.8.0_111-8u111-b14-3-b14)
                                     |OpenJDK 64-Bit Server VM (build 25.111-b14, mixed mode)
                                     |""")
        mock_getoutput = MagicMock(return_value=cmd_output)

        with patch('subprocess.getoutput', mock_getoutput):
            sandbox_run_jvm.validate_jvm_support()

        mock_getoutput.assert_called_once_with('java -version')

    def test_supported_with_options_warnings(self):
        cmd_output = strip_margin("""|Picked up _JAVA_OPTIONS: -Xss8m -Xms512m -Xmx2048m -XX:MaxPermSize=512m -XX:ReservedCodeCacheSize=128m -XX:+CMSClassUnloadingEnabled -XX:+UseConcMarkSweepGC
                                     |OpenJDK 64-Bit Server VM warning: ignoring option MaxPermSize=512m; support was removed in 8.0
                                     |openjdk version "1.8.0_121"
                                     |OpenJDK Runtime Environment (build 1.8.0_121-8u121-b13-3-b13)
                                     |OpenJDK 64-Bit Server VM (build 25.121-b13, mixed mode)""")

        mock_getoutput = MagicMock(return_value=cmd_output)

        with patch('subprocess.getoutput', mock_getoutput):
            sandbox_run_jvm.validate_jvm_support()

        mock_getoutput.assert_called_once_with('java -version')

    def test_unsupported_vendor(self):
        cmd_output = strip_margin("""|unsupported version "1.2.3.4"
                                     |UnsupportedJDK Runtime Environment (build 1.2.3.4)
                                     |UnsupportedJDK 64-Bit Server VM (build 1.2.3.4, mixed mode)
                                     |""")
        mock_getoutput = MagicMock(return_value=cmd_output)

        with patch('subprocess.getoutput', mock_getoutput):
            self.assertRaises(JavaUnsupportedVendorError, sandbox_run_jvm.validate_jvm_support)

        mock_getoutput.assert_called_once_with('java -version')

    def test_unsupported_version(self):
        cmd_output = strip_margin("""|java version "1.7.0_72"
                                     |Java(TM) SE Runtime Environment (build 1.8.0_72-b15)
                                     |Java HotSpot(TM) 64-Bit Server VM (build 25.72-b15, mixed mode)
                                     |""")
        mock_getoutput = MagicMock(return_value=cmd_output)

        with patch('subprocess.getoutput', mock_getoutput):
            self.assertRaises(JavaUnsupportedVersionError, sandbox_run_jvm.validate_jvm_support)

        mock_getoutput.assert_called_once_with('java -version')

    def test_parse_error_from_invalid_output(self):
        mock_getoutput = MagicMock(return_value="gobbledygook")

        with patch('subprocess.getoutput', mock_getoutput):
            self.assertRaises(JavaVersionParseError, sandbox_run_jvm.validate_jvm_support)

        mock_getoutput.assert_called_once_with('java -version')

    def test_parse_error_from_unexpected_first_line(self):
        cmd_output = strip_margin("""|I like to eat
                                     |Java(TM) SE Runtime Environment (build 1.8.0_72-b15)
                                     |Java HotSpot(TM) 64-Bit Server VM (build 25.72-b15, mixed mode)
                                     |""")
        mock_getoutput = MagicMock(return_value=cmd_output)

        with patch('subprocess.getoutput', mock_getoutput):
            self.assertRaises(JavaVersionParseError, sandbox_run_jvm.validate_jvm_support)

        mock_getoutput.assert_called_once_with('java -version')

    def test_call_error(self):
        mock_getoutput = MagicMock(side_effect=subprocess.CalledProcessError(1, 'test'))

        with patch('subprocess.getoutput', mock_getoutput):
            self.assertRaises(JavaCallError, sandbox_run_jvm.validate_jvm_support)

        mock_getoutput.assert_called_once_with('java -version')


class TestValidateHostnameLookup(CliTestCase):
    def test_macos_hostname_on_each_localhost_line(self):
        mock_is_mac_os = MagicMock(return_value=True)
        mock_hostname = MagicMock(return_value='mbpro.local')
        mock_open = MagicMock(return_value=io.StringIO(
            '# localhost comment\n'
            '127.0.0.1	localhost mbpro.local\n'
            '255.255.255.255	broadcasthost\n'
            '::1             localhost mbpro.local\n'
        ))

        with patch('conductr_cli.host.is_macos', mock_is_mac_os), \
                patch('conductr_cli.host.hostname', mock_hostname), \
                patch('builtins.open', mock_open):
            sandbox_run_jvm.validate_hostname_lookup()

        mock_hostname.assert_called_once_with()
        mock_open.assert_called_once_with('/etc/hosts', 'r')

    def test_macos_hostname_on_one_localhost_line(self):
        mock_is_mac_os = MagicMock(return_value=True)
        mock_hostname = MagicMock(return_value='mbpro.local')
        mock_open = MagicMock(return_value=io.StringIO(
            '# localhost comment\n'
            '127.0.0.1	localhost mbpro.local\n'
            '255.255.255.255	broadcasthost\n'
            '::1             localhost\n'
        ))

        with patch('conductr_cli.host.is_macos', mock_is_mac_os), \
                patch('conductr_cli.host.hostname', mock_hostname), \
                patch('builtins.open', mock_open):
            sandbox_run_jvm.validate_hostname_lookup()

        mock_hostname.assert_called_once_with()
        mock_open.assert_called_once_with('/etc/hosts', 'r')

    def test_macos_fail_no_hostname(self):
        mock_is_mac_os = MagicMock(return_value=True)
        mock_hostname = MagicMock(return_value='mbpro.local')
        mock_open = MagicMock(return_value=io.StringIO(
            '# localhost comment\n'
            '127.0.0.1	localhost\n'
            '255.255.255.255	broadcasthost\n'
            '::1             localhost\n'
        ))

        with patch('conductr_cli.host.is_macos', mock_is_mac_os), \
                patch('conductr_cli.host.hostname', mock_hostname), \
                patch('builtins.open', mock_open):
            self.assertRaises(HostnameLookupError, sandbox_run_jvm.validate_hostname_lookup)

        mock_hostname.assert_called_once_with()
        mock_open.assert_called_once_with('/etc/hosts', 'r')

    def test_macos_fail_hostname_commented_out(self):
        mock_is_mac_os = MagicMock(return_value=True)
        mock_hostname = MagicMock(return_value='mbpro.local')
        mock_open = MagicMock(return_value=io.StringIO(
            '# localhost comment\n'
            '127.0.0.1	localhost # mbpro.local\n'
            '255.255.255.255	broadcasthost\n'
            '::1             localhost\n'
        ))

        with patch('conductr_cli.host.is_macos', mock_is_mac_os), \
                patch('conductr_cli.host.hostname', mock_hostname), \
                patch('builtins.open', mock_open):
            self.assertRaises(HostnameLookupError, sandbox_run_jvm.validate_hostname_lookup)

        mock_hostname.assert_called_once_with()
        mock_open.assert_called_once_with('/etc/hosts', 'r')

    def test_macos_fail_invalid_hostname(self):
        mock_is_mac_os = MagicMock(return_value=True)
        mock_hostname = MagicMock(return_value='mbpro.local')
        mock_open = MagicMock(return_value=io.StringIO(
            '# localhost comment\n'
            '127.0.0.1	localhost mbpro.local1\n'
            '255.255.255.255	broadcasthost\n'
            '::1             localhost\n'
        ))

        with patch('conductr_cli.host.is_macos', mock_is_mac_os), \
                patch('conductr_cli.host.hostname', mock_hostname), \
                patch('builtins.open', mock_open):
            self.assertRaises(HostnameLookupError, sandbox_run_jvm.validate_hostname_lookup)

        mock_hostname.assert_called_once_with()
        mock_open.assert_called_once_with('/etc/hosts', 'r')

    def test_non_macos(self):
        mock_is_mac_os = MagicMock(return_value=False)
        mock_hostname = MagicMock()

        with patch('conductr_cli.host.is_macos', mock_is_mac_os), \
                patch('conductr_cli.host.hostname', mock_hostname):
            sandbox_run_jvm.validate_hostname_lookup()

        mock_hostname.assert_not_called()


class TestValidate64BitSupport(CliTestCase):
    def test_64bit(self):
        mock_is_64bit = MagicMock(return_value=True)

        with patch('conductr_cli.host.is_64bit', mock_is_64bit):
            sandbox_run_jvm.validate_64bit_support()

    def test_non_64bit(self):
        mock_is_64bit = MagicMock(return_value=False)

        with patch('conductr_cli.host.is_64bit', mock_is_64bit):
            self.assertRaises(SandboxUnsupportedOsArchError,
                              sandbox_run_jvm.validate_64bit_support)


class TestValidateBintrayCredentials(CliTestCase):
    def test_check_passed(self):
        mock_load_bintray_credentials = MagicMock()

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', mock_load_bintray_credentials):
            sandbox_run_jvm.validate_bintray_credentials('2.0.0', offline_mode=False)

        mock_load_bintray_credentials.assert_called_once_with(disable_instructions=True, raise_error=True)

    def test_check_failed(self):
        mock_load_bintray_credentials = MagicMock(side_effect=BintrayCredentialsNotFoundError('test only'))

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', mock_load_bintray_credentials):
            self.assertRaises(BintrayCredentialsNotFoundError,
                              sandbox_run_jvm.validate_bintray_credentials, '2.0.0', offline_mode=False)

        mock_load_bintray_credentials.assert_called_once_with(disable_instructions=True, raise_error=True)

    def test_no_check_offline_mode(self):
        mock_load_bintray_credentials = MagicMock()

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', mock_load_bintray_credentials):
            sandbox_run_jvm.validate_bintray_credentials('2.0.0', offline_mode=True)

        mock_load_bintray_credentials.assert_not_called()

    def test_no_check_conductr_version(self):
        mock_load_bintray_credentials = MagicMock()

        with patch('conductr_cli.resolvers.bintray_resolver.load_bintray_credentials', mock_load_bintray_credentials):
            sandbox_run_jvm.validate_bintray_credentials('2.1.0', offline_mode=False)

        mock_load_bintray_credentials.assert_not_called()


class TestDownloadSandboxImage(CliTestCase):
    bintray_auth = ('Bintray', 'username', 'password')

    image_dir = '~/.conductr/images'

    image_version = '2.1.0-alpha.1'

    core_package_name = 'ConductR-Universal'

    core_artefact_type = 'core'

    core_artefact_file_name = 'conductr-2.1.0-alpha.1-Mac_OS_X-x86_64.tgz'

    core_artefact_mac_os = {
        'package_name': 'ConductR-Universal',
        'resolver': 'conductr_cli.resolvers.bintray_resolver',
        'org': 'lightbend',
        'repo': 'commercial-releases',
        'version': '2.1.0-alpha.1',
        'path': 'conductr-2.1.0-alpha.1-Mac_OS_X-x86_64.tgz',
        'download_url': 'https://dl.bintray.com/lightbend/commercial-releases/conductr-2.1.0-alpha.1-Mac_OS_X-x86_64.tgz'
    }

    core_artefact_linux = {
        'package_name': 'ConductR-Universal',
        'resolver': 'conductr_cli.resolvers.bintray_resolver',
        'org': 'lightbend',
        'repo': 'commercial-releases',
        'version': '2.1.0-alpha.1',
        'path': 'conductr-2.1.0-alpha.1-Linux-x86_64.tgz',
        'download_url': 'https://dl.bintray.com/lightbend/commercial-releases/conductr-2.1.0-alpha.1-Linux-x86_64.tgz'
    }

    agent_package_name = 'ConductR-Agent-Universal'

    agent_artefact_type = 'agent'

    agent_artefact_file_name = 'conductr-agent-2.1.0-alpha.1-Mac_OS_X-x86_64.tgz'

    agent_artefact_mac_os = {
        'package_name': 'ConductR-Agent-Universal',
        'resolver': 'conductr_cli.resolvers.bintray_resolver',
        'org': 'lightbend',
        'repo': 'commercial-releases',
        'version': '2.1.0-alpha.1',
        'path': 'conductr-agent-2.1.0-alpha.1-Mac_OS_X-x86_64.tgz',
        'download_url': 'https://dl.bintray.com/lightbend/commercial-releases/conductr-agent-2.1.0-alpha.1-Mac_OS_X-x86_64.tgz'
    }

    agent_artefact_linux = {
        'package_name': 'ConductR-Agent-Universal',
        'resolver': 'conductr_cli.resolvers.bintray_resolver',
        'org': 'lightbend',
        'repo': 'commercial-releases',
        'version': '2.1.0-alpha.1',
        'path': 'conductr-agent-2.1.0-alpha.1-Linux-x86_64.tgz',
        'download_url': 'https://dl.bintray.com/lightbend/commercial-releases/conductr-agent-2.1.0-alpha.1-Linux-x86_64.tgz'
    }

    def test_download_core_from_commercial_releases(self):
        mock_artefact_os_name = MagicMock(return_value='Mac_OS_X')
        artefacts = [self.core_artefact_mac_os, self.core_artefact_linux]
        mock_bintray_artefacts_by_version = MagicMock(return_value=artefacts)

        mock_bintray_download_artefact = MagicMock(return_value=(True,
                                                                 'conductr-2.1.0-alpha.1-Mac_OS_X-x86_64.tgz',
                                                                 '~/.conductr/images/conductr-2.1.0-alpha.1-Mac_OS_X-x86_64.tgz',
                                                                 None))

        with patch('conductr_cli.sandbox_run_jvm.artefact_os_name', mock_artefact_os_name), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_artefacts_by_version',
                      mock_bintray_artefacts_by_version), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_download_artefact',
                      mock_bintray_download_artefact):
            self.assertEqual('~/.conductr/images/conductr-2.1.0-alpha.1-Mac_OS_X-x86_64.tgz',
                             sandbox_run_jvm.download_sandbox_image(self.bintray_auth,
                                                                    self.image_dir,
                                                                    self.core_package_name,
                                                                    self.core_artefact_type,
                                                                    self.image_version))

        mock_bintray_artefacts_by_version.assert_called_once_with(self.bintray_auth,
                                                                  'lightbend',
                                                                  'commercial-releases',
                                                                  self.core_package_name,
                                                                  self.image_version)
        mock_bintray_download_artefact.assert_called_once_with(self.image_dir,
                                                               self.core_artefact_mac_os,
                                                               self.bintray_auth,
                                                               raise_error=True)

    def test_download_core_from_generic(self):
        mock_artefact_os_name = MagicMock(return_value='Mac_OS_X')
        bintray_auth = (None, None, None)

        artefacts = [self.core_artefact_mac_os, self.core_artefact_linux]
        mock_bintray_artefacts_by_version = MagicMock(return_value=artefacts)

        mock_bintray_download_artefact = MagicMock(return_value=(True,
                                                                 'conductr-2.1.0-alpha.1-Mac_OS_X-x86_64.tgz',
                                                                 '~/.conductr/images/conductr-2.1.0-alpha.1-Mac_OS_X-x86_64.tgz',
                                                                 None))

        with patch('conductr_cli.sandbox_run_jvm.artefact_os_name', mock_artefact_os_name), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_artefacts_by_version',
                      mock_bintray_artefacts_by_version), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_download_artefact',
                      mock_bintray_download_artefact):
            self.assertEqual('~/.conductr/images/conductr-2.1.0-alpha.1-Mac_OS_X-x86_64.tgz',
                             sandbox_run_jvm.download_sandbox_image(bintray_auth,
                                                                    self.image_dir,
                                                                    self.core_package_name,
                                                                    self.core_artefact_type,
                                                                    self.image_version))

        mock_bintray_artefacts_by_version.assert_called_once_with(bintray_auth,
                                                                  'lightbend',
                                                                  'generic',
                                                                  self.core_package_name,
                                                                  self.image_version)
        mock_bintray_download_artefact.assert_called_once_with(self.image_dir,
                                                               self.core_artefact_mac_os,
                                                               bintray_auth,
                                                               raise_error=True)

    def test_download_core_older_version(self):
        image_version = '2.0.5'

        mock_artefact_os_name = MagicMock(return_value='Mac_OS_X')

        core_artefact_mac_os = self.core_artefact_mac_os.copy()
        core_artefact_mac_os.update({
            'version': '2.0.5',
            'path': 'conductr-2.0.5-Mac_OS_X-x86_64.tgz',
            'download_url': 'https://dl.bintray.com/lightbend/commercial-releases/conductr-2.0.5-Mac_OS_X-x86_64.tgz'
        })
        core_artefact_linux = self.core_artefact_linux.copy()
        core_artefact_linux.update({
            'version': '2.0.5',
            'path': 'conductr-2.0.5-Linux-x86_64.tgz',
            'download_url': 'https://dl.bintray.com/lightbend/commercial-releases/conductr-2.0.5-Linux-x86_64.tgz'
        })
        artefacts = [core_artefact_mac_os, core_artefact_linux]
        mock_bintray_artefacts_by_version = MagicMock(return_value=artefacts)

        mock_bintray_download_artefact = MagicMock(return_value=(True,
                                                                 'conductr-2.0.5-Mac_OS_X-x86_64.tgz',
                                                                 '~/.conductr/images/conductr-2.0.5-Mac_OS_X-x86_64.tgz',
                                                                 None))

        with patch('conductr_cli.sandbox_run_jvm.artefact_os_name', mock_artefact_os_name), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_artefacts_by_version',
                      mock_bintray_artefacts_by_version), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_download_artefact',
                      mock_bintray_download_artefact):
            self.assertEqual('~/.conductr/images/conductr-2.0.5-Mac_OS_X-x86_64.tgz',
                             sandbox_run_jvm.download_sandbox_image(self.bintray_auth,
                                                                    self.image_dir,
                                                                    self.core_package_name,
                                                                    self.core_artefact_type,
                                                                    image_version))

        mock_bintray_artefacts_by_version.assert_called_once_with(self.bintray_auth,
                                                                  'lightbend',
                                                                  'commercial-releases',
                                                                  self.core_package_name,
                                                                  image_version)
        mock_bintray_download_artefact.assert_called_once_with(self.image_dir,
                                                               core_artefact_mac_os,
                                                               self.bintray_auth,
                                                               raise_error=True)

    def test_download_agent_from_commercial_releases(self):
        mock_artefact_os_name = MagicMock(return_value='Mac_OS_X')
        artefacts = [self.agent_artefact_mac_os, self.agent_artefact_linux]
        mock_bintray_artefacts_by_version = MagicMock(return_value=artefacts)

        mock_bintray_download_artefact = MagicMock(return_value=(True,
                                                                 'conductr-agent-2.1.0-alpha.1-Mac_OS_X-x86_64.tgz',
                                                                 '~/.conductr/images/conductr-agent-2.1.0-alpha.1-Mac_OS_X-x86_64.tgz',
                                                                 None))

        with patch('conductr_cli.sandbox_run_jvm.artefact_os_name', mock_artefact_os_name), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_artefacts_by_version',
                      mock_bintray_artefacts_by_version), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_download_artefact',
                      mock_bintray_download_artefact):
            self.assertEqual('~/.conductr/images/conductr-agent-2.1.0-alpha.1-Mac_OS_X-x86_64.tgz',
                             sandbox_run_jvm.download_sandbox_image(self.bintray_auth,
                                                                    self.image_dir,
                                                                    self.agent_package_name,
                                                                    self.agent_artefact_type,
                                                                    self.image_version))

        mock_bintray_artefacts_by_version.assert_called_once_with(self.bintray_auth,
                                                                  'lightbend',
                                                                  'commercial-releases',
                                                                  self.agent_package_name,
                                                                  self.image_version)
        mock_bintray_download_artefact.assert_called_once_with(self.image_dir,
                                                               self.agent_artefact_mac_os,
                                                               self.bintray_auth,
                                                               raise_error=True)

    def test_download_agent_from_generic(self):
        mock_artefact_os_name = MagicMock(return_value='Mac_OS_X')
        bintray_auth = (None, None, None)

        artefacts = [self.agent_artefact_mac_os, self.agent_artefact_linux]
        mock_bintray_artefacts_by_version = MagicMock(return_value=artefacts)

        mock_bintray_download_artefact = MagicMock(return_value=(True,
                                                                 'conductr-agent-2.1.0-alpha.1-Mac_OS_X-x86_64.tgz',
                                                                 '~/.conductr/images/conductr-agent-2.1.0-alpha.1-Mac_OS_X-x86_64.tgz',
                                                                 None))

        with patch('conductr_cli.sandbox_run_jvm.artefact_os_name', mock_artefact_os_name), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_artefacts_by_version',
                      mock_bintray_artefacts_by_version), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_download_artefact',
                      mock_bintray_download_artefact):
            self.assertEqual('~/.conductr/images/conductr-agent-2.1.0-alpha.1-Mac_OS_X-x86_64.tgz',
                             sandbox_run_jvm.download_sandbox_image(bintray_auth,
                                                                    self.image_dir,
                                                                    self.agent_package_name,
                                                                    self.agent_artefact_type,
                                                                    self.image_version))

        mock_bintray_artefacts_by_version.assert_called_once_with(bintray_auth,
                                                                  'lightbend',
                                                                  'generic',
                                                                  self.agent_package_name,
                                                                  self.image_version)
        mock_bintray_download_artefact.assert_called_once_with(self.image_dir,
                                                               self.agent_artefact_mac_os,
                                                               bintray_auth,
                                                               raise_error=True)

    def test_download_agent_older_version(self):
        image_version = '2.0.5'

        mock_artefact_os_name = MagicMock(return_value='Mac_OS_X')
        bintray_auth = (None, None, None)

        agent_artefact_mac_os = self.agent_artefact_mac_os.copy()
        agent_artefact_mac_os.update({
            'version': '2.0.5',
            'path': 'conductr-agent-2.0.5-Mac_OS_X-x86_64.tgz',
            'download_url': 'https://dl.bintray.com/lightbend/commercial-releases/conductr-agent-2.0.5-Mac_OS_X-x86_64.tgz'
        })
        agent_artefact_linux = self.agent_artefact_linux.copy()
        agent_artefact_linux.update({
            'version': '2.0.5',
            'path': 'conductr-agent-2.0.5-Linux-x86_64.tgz',
            'download_url': 'https://dl.bintray.com/lightbend/commercial-releases/conductr-agent-2.0.5-Linux-x86_64.tgz'
        })
        artefacts = [agent_artefact_mac_os, agent_artefact_linux]
        mock_bintray_artefacts_by_version = MagicMock(return_value=artefacts)

        mock_bintray_download_artefact = MagicMock(return_value=(True,
                                                                 'conductr-agent-2.0.5-Mac_OS_X-x86_64.tgz',
                                                                 '~/.conductr/images/conductr-agent-2.0.5-Mac_OS_X-x86_64.tgz',
                                                                 None))

        with patch('conductr_cli.sandbox_run_jvm.artefact_os_name', mock_artefact_os_name), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_artefacts_by_version',
                      mock_bintray_artefacts_by_version), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_download_artefact',
                      mock_bintray_download_artefact):
            self.assertEqual('~/.conductr/images/conductr-agent-2.0.5-Mac_OS_X-x86_64.tgz',
                             sandbox_run_jvm.download_sandbox_image(bintray_auth,
                                                                    self.image_dir,
                                                                    self.agent_package_name,
                                                                    self.agent_artefact_type,
                                                                    image_version))

        mock_bintray_artefacts_by_version.assert_called_once_with(bintray_auth,
                                                                  'lightbend',
                                                                  'commercial-releases',
                                                                  self.agent_package_name,
                                                                  image_version)
        mock_bintray_download_artefact.assert_called_once_with(self.image_dir,
                                                               agent_artefact_mac_os,
                                                               bintray_auth,
                                                               raise_error=True)

    def test_bintray_unreachable(self):
        mock_bintray_artefacts_by_version = MagicMock(side_effect=ConnectionError('test'))

        with patch('conductr_cli.resolvers.bintray_resolver.bintray_artefacts_by_version',
                   mock_bintray_artefacts_by_version):
            self.assertRaises(BintrayUnreachableError,
                              sandbox_run_jvm.download_sandbox_image,
                              self.bintray_auth,
                              self.image_dir,
                              self.core_package_name,
                              self.core_artefact_type,
                              self.image_version)

        mock_bintray_artefacts_by_version.assert_called_once_with(self.bintray_auth,
                                                                  'lightbend',
                                                                  'commercial-releases',
                                                                  self.core_package_name,
                                                                  self.image_version)

    def test_not_found(self):

        response = MagicMock(**{'status_code': 404})
        error = HTTPError('test', response=response)
        mock_bintray_artefacts_by_version = MagicMock(side_effect=error)

        with patch('conductr_cli.resolvers.bintray_resolver.bintray_artefacts_by_version',
                   mock_bintray_artefacts_by_version), \
                self.assertRaises(SandboxImageNotFoundError):
                    sandbox_run_jvm.download_sandbox_image(self.bintray_auth, self.image_dir, self.core_package_name,
                                                           self.core_artefact_type, self.image_version)

        mock_bintray_artefacts_by_version.assert_called_once_with(self.bintray_auth,
                                                                  'lightbend',
                                                                  'commercial-releases',
                                                                  self.core_package_name,
                                                                  self.image_version)

    def test_http_error(self):
        response = MagicMock(**{'status_code': 500})
        error = HTTPError('test', response=response)
        mock_bintray_artefacts_by_version = MagicMock(side_effect=error)

        with patch('conductr_cli.resolvers.bintray_resolver.bintray_artefacts_by_version',
                   mock_bintray_artefacts_by_version), \
                self.assertRaises(SandboxImageFetchError) as err:
                    sandbox_run_jvm.download_sandbox_image(self.bintray_auth, self.image_dir, self.core_package_name,
                                                           self.core_artefact_type, self.image_version)

        self.assertEqual(err.exception.cause, error)
        mock_bintray_artefacts_by_version.assert_called_once_with(self.bintray_auth,
                                                                  'lightbend',
                                                                  'commercial-releases',
                                                                  self.core_package_name,
                                                                  self.image_version)

    def test_url_error(self):
        error = URLError('test')
        mock_bintray_artefacts_by_version = MagicMock(side_effect=error)

        with patch('conductr_cli.resolvers.bintray_resolver.bintray_artefacts_by_version',
                   mock_bintray_artefacts_by_version), \
                self.assertRaises(SandboxImageFetchError) as err:
                    sandbox_run_jvm.download_sandbox_image(self.bintray_auth, self.image_dir, self.core_package_name,
                                                           self.core_artefact_type, self.image_version)

        self.assertEqual(err.exception.cause, error)
        mock_bintray_artefacts_by_version.assert_called_once_with(self.bintray_auth,
                                                                  'lightbend',
                                                                  'commercial-releases',
                                                                  self.core_package_name,
                                                                  self.image_version)

    def test_artefact_not_found(self):
        mock_artefact_os_name = MagicMock(return_value='Mac_OS_X')
        mock_bintray_artefacts_by_version = MagicMock(return_value=[])

        with patch('conductr_cli.sandbox_run_jvm.artefact_os_name', mock_artefact_os_name), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_artefacts_by_version',
                      mock_bintray_artefacts_by_version):
            self.assertRaises(SandboxImageNotFoundError,
                              sandbox_run_jvm.download_sandbox_image,
                              self.bintray_auth,
                              self.image_dir,
                              self.core_package_name,
                              self.core_artefact_type,
                              self.image_version)

        mock_bintray_artefacts_by_version.assert_called_once_with(self.bintray_auth,
                                                                  'lightbend',
                                                                  'commercial-releases',
                                                                  self.core_package_name,
                                                                  self.image_version)

    def test_artefact_multiple_found(self):
        mock_artefact_os_name = MagicMock(return_value='Mac_OS_X')
        mock_bintray_artefacts_by_version = MagicMock(return_value=[
            self.core_artefact_mac_os,
            self.core_artefact_linux,
            self.core_artefact_mac_os
        ])

        with patch('conductr_cli.sandbox_run_jvm.artefact_os_name', mock_artefact_os_name), \
                patch('conductr_cli.resolvers.bintray_resolver.bintray_artefacts_by_version',
                      mock_bintray_artefacts_by_version):
            self.assertRaises(SandboxImageNotFoundError,
                              sandbox_run_jvm.download_sandbox_image,
                              self.bintray_auth,
                              self.image_dir,
                              self.core_package_name,
                              self.core_artefact_type,
                              self.image_version)

        mock_bintray_artefacts_by_version.assert_called_once_with(self.bintray_auth,
                                                                  'lightbend',
                                                                  'commercial-releases',
                                                                  self.core_package_name,
                                                                  self.image_version)


class TestArtefactOsName(CliTestCase):
    def test_mac_os(self):
        mock_is_macos = MagicMock(return_value=True)
        mock_is_linux = MagicMock(return_value=False)
        with patch('conductr_cli.host.is_macos', mock_is_macos), \
                patch('conductr_cli.host.is_linux', mock_is_linux):
            self.assertEqual('Mac_OS_X', sandbox_run_jvm.artefact_os_name())

        mock_is_macos.assert_called_once_with()
        mock_is_linux.assert_not_called()

    def test_linux(self):
        mock_is_macos = MagicMock(return_value=False)
        mock_is_linux = MagicMock(return_value=True)
        with patch('conductr_cli.host.is_macos', mock_is_macos), \
                patch('conductr_cli.host.is_linux', mock_is_linux):
            self.assertEqual('Linux', sandbox_run_jvm.artefact_os_name())

        mock_is_macos.assert_called_once_with()
        mock_is_linux.assert_called_once_with()

    def test_unsupported_os(self):
        mock_is_macos = MagicMock(return_value=False)
        mock_is_linux = MagicMock(return_value=False)
        with patch('conductr_cli.host.is_macos', mock_is_macos), \
                patch('conductr_cli.host.is_linux', mock_is_linux):
            self.assertRaises(SandboxUnsupportedOsError,
                              sandbox_run_jvm.artefact_os_name)

        mock_is_macos.assert_called_once_with()
        mock_is_linux.assert_called_once_with()


class TestCleanupTmpDir(CliTestCase):
    tmp_dir = '~/.conductr/images/tmp'

    def test_existing_tmp_dir(self):
        mock_exists = MagicMock(return_value=True)
        mock_rmtree = MagicMock()
        mock_makedirs = MagicMock()

        with patch('os.path.exists', mock_exists), \
                patch('shutil.rmtree', mock_rmtree), \
                patch('os.makedirs', mock_makedirs):
            sandbox_run_jvm.cleanup_tmp_dir(self.tmp_dir)

        mock_exists.assert_called_once_with(self.tmp_dir)
        mock_rmtree.assert_called_once_with(self.tmp_dir)
        mock_makedirs.assert_called_once_with(self.tmp_dir, exist_ok=True)

    def test_without_existing_tmp_dir(self):
        mock_exists = MagicMock(return_value=False)
        mock_rmtree = MagicMock()
        mock_makedirs = MagicMock()

        with patch('os.path.exists', mock_exists), \
                patch('shutil.rmtree', mock_rmtree), \
                patch('os.makedirs', mock_makedirs):
            sandbox_run_jvm.cleanup_tmp_dir(self.tmp_dir)

        mock_exists.assert_called_once_with(self.tmp_dir)
        mock_rmtree.assert_not_called()
        mock_makedirs.assert_called_once_with(self.tmp_dir, exist_ok=True)


class TestMergeWithOsEnv(CliTestCase):
    def test_return_merged_env(self):
        os_env = {'os': 'env'}
        mock_copy = MagicMock(return_value=os_env)

        mock_sys_meipass = MagicMock(return_value=None)

        with patch('os.environ.copy', mock_copy), \
                patch('conductr_cli.pyinstaller_info.sys_meipass', mock_sys_meipass):
            result = sandbox_run_jvm.merge_with_os_envs(['a=1', 'b=2'], ['c=3'])
            self.assertEqual({
                'a': '1',
                'b': '2',
                'c': '3',
                'os': 'env',
            }, result)

    def test_return_os_env_if_empty_inputs(self):
        os_env = {'os': 'env'}
        mock_copy = MagicMock(return_value=os_env)

        mock_sys_meipass = MagicMock(return_value=None)

        with patch('os.environ.copy', mock_copy), \
                patch('conductr_cli.pyinstaller_info.sys_meipass', mock_sys_meipass):
            result = sandbox_run_jvm.merge_with_os_envs([], [])
            self.assertEqual(os_env, result)

    def test_cleanup_pyinstaller_paths(self):
        pyinstaller_path = '/tmp/_MEIkhfrhw'

        os_env = {
            'os': 'env',
            'PATH': pyinstaller_path,
            'LD_LIBRARY_PATH': pyinstaller_path,
        }
        mock_copy = MagicMock(return_value=os_env)

        mock_sys_meipass = MagicMock(return_value=pyinstaller_path)

        with patch('os.environ.copy', mock_copy), \
                patch('conductr_cli.pyinstaller_info.sys_meipass', mock_sys_meipass):
            result = sandbox_run_jvm.merge_with_os_envs(['a=1', 'b=2'], ['c=3'])
            self.assertEqual({
                'a': '1',
                'b': '2',
                'c': '3',
                'os': 'env',
            }, result)

    def test_cleanup_pyinstaller_paths_should_not_clear_overrides(self):
        pyinstaller_path = '/tmp/_MEIkhfrhw'

        os_env = {
            'os': 'env',
            'PATH': pyinstaller_path,
            'LD_LIBRARY_PATH': pyinstaller_path,
        }
        mock_copy = MagicMock(return_value=os_env)

        mock_sys_meipass = MagicMock(return_value=pyinstaller_path)

        with patch('os.environ.copy', mock_copy), \
                patch('conductr_cli.pyinstaller_info.sys_meipass', mock_sys_meipass):
            result = sandbox_run_jvm.merge_with_os_envs(['LD_LIBRARY_PATH=/my/path'], ['PATH=/other/path'])
            self.assertEqual({
                'LD_LIBRARY_PATH': '/my/path',
                'PATH': '/other/path',
                'os': 'env',
            }, result)

    def test_cleanup_pyinstaller_paths_if_empty_inputs(self):
        pyinstaller_path = '/tmp/_MEIkhfrhw'

        os_env = {
            'os': 'env',
            'PATH': pyinstaller_path,
            'LD_LIBRARY_PATH': pyinstaller_path,
        }
        mock_copy = MagicMock(return_value=os_env)

        mock_sys_meipass = MagicMock(return_value=pyinstaller_path)

        with patch('os.environ.copy', mock_copy), \
                patch('conductr_cli.pyinstaller_info.sys_meipass', mock_sys_meipass):
            result = sandbox_run_jvm.merge_with_os_envs([], [])
            self.assertEqual({
                'os': 'env',
            }, result)


class TestRemovePathFromEnv(CliTestCase):
    def test_leaving_input_as_is(self):
        env = {
            'USER': 'john'
        }
        result = sandbox_run_jvm.remove_path_from_env(env, 'PATH', '/tmp/_MEIkhfrhw')
        self.assertEqual(env, result)

    def test_remove_value(self):
        env = {
            'USER': 'john',
            'PATH': '/tmp/_MEIkhfrhw:/home/bar/:/usr/local'
        }
        result = sandbox_run_jvm.remove_path_from_env(env, 'PATH', '/tmp/_MEIkhfrhw')
        expected_result = {
            'USER': 'john',
            'PATH': '/home/bar/:/usr/local'
        }
        self.assertEqual(expected_result, result)

        env = {
            'USER': 'john',
            'PATH': '/home/bar/:/tmp/_MEIkhfrhw:/usr/local'
        }
        result = sandbox_run_jvm.remove_path_from_env(env, 'PATH', '/tmp/_MEIkhfrhw')
        expected_result = {
            'USER': 'john',
            'PATH': '/home/bar/:/usr/local'
        }
        self.assertEqual(expected_result, result)

        env = {
            'USER': 'john',
            'PATH': '/home/bar/:/usr/local:/tmp/_MEIkhfrhw'
        }
        result = sandbox_run_jvm.remove_path_from_env(env, 'PATH', '/tmp/_MEIkhfrhw')
        expected_result = {
            'USER': 'john',
            'PATH': '/home/bar/:/usr/local'
        }
        self.assertEqual(expected_result, result)

    def test_delete_key(self):
        env = {
            'USER': 'john',
            'PATH': '/tmp/_MEIkhfrhw'
        }
        result = sandbox_run_jvm.remove_path_from_env(env, 'PATH', '/tmp/_MEIkhfrhw')
        expected_result = {
            'USER': 'john',
        }
        self.assertEqual(expected_result, result)

        env = {
            'PATH': '/tmp/_MEIkhfrhw'
        }
        result = sandbox_run_jvm.remove_path_from_env(env, 'PATH', '/tmp/_MEIkhfrhw')
        expected_result = {}
        self.assertEqual(expected_result, result)


class TestCheckUpgradeRequirement(CliTestCase):
    bintray_realm = 'bintray'
    bintray_username = 'me'
    bintray_password = 'abcdef'
    bintray_auth = (bintray_realm, bintray_username, bintray_password)

    no_bintray_auth = (None, None, None)

    image_dir = '/tmp/cache-dir'

    def test_upgrade_required_commercial_repo(self):
        mock_get = self.mock_get_versions(['2.1.7', '2.1.0', '2.1.8'])

        mock_resolve_binary_from_cache = MagicMock(return_value=None)

        with patch('requests.get', mock_get), \
                patch('conductr_cli.sandbox_run_jvm.resolve_binary_from_cache', mock_resolve_binary_from_cache):
            result = sandbox_run_jvm.check_upgrade_requirements(self.bintray_auth, self.image_dir, '2.1.0')
            expected_result = sandbox_run_jvm.SandboxUpgradeRequirement(
                is_upgrade_required=True,
                current_version=semver.parse_version_info('2.1.0'),
                latest_version=semver.parse_version_info('2.1.8')
            )
            self.assertEqual(expected_result, result)

        mock_get.assert_called_once_with(
            'https://api.bintray.com/packages/lightbend/commercial-releases/ConductR-Universal',
            auth=(self.bintray_username, self.bintray_password)
        )

        mock_resolve_binary_from_cache.assert_called_once_with(self.image_dir, 'conductr', '2.1.8')

    def test_upgrade_required_generic_repo(self):
        mock_get = self.mock_get_versions(['2.1.0', '2.1.8'])

        mock_resolve_binary_from_cache = MagicMock(return_value=None)

        with patch('requests.get', mock_get), \
                patch('conductr_cli.sandbox_run_jvm.resolve_binary_from_cache', mock_resolve_binary_from_cache):
            result = sandbox_run_jvm.check_upgrade_requirements(self.no_bintray_auth, self.image_dir, '2.1.0')
            expected_result = sandbox_run_jvm.SandboxUpgradeRequirement(
                is_upgrade_required=True,
                current_version=semver.parse_version_info('2.1.0'),
                latest_version=semver.parse_version_info('2.1.8')
            )
            self.assertEqual(expected_result, result)

        mock_get.assert_called_once_with('https://api.bintray.com/packages/lightbend/generic/ConductR-Universal')

        mock_resolve_binary_from_cache.assert_called_once_with(self.image_dir, 'conductr', '2.1.8')

    def test_upgrade_required_private_repo(self):
        mock_get = self.mock_get_versions(['2.0.0', '2.0.8'])

        mock_resolve_binary_from_cache = MagicMock(return_value=None)

        with patch('requests.get', mock_get), \
                patch('conductr_cli.sandbox_run_jvm.resolve_binary_from_cache', mock_resolve_binary_from_cache):
            result = sandbox_run_jvm.check_upgrade_requirements(self.bintray_auth, self.image_dir, '2.0.5')
            expected_result = sandbox_run_jvm.SandboxUpgradeRequirement(
                is_upgrade_required=True,
                current_version=semver.parse_version_info('2.0.5'),
                latest_version=semver.parse_version_info('2.0.8')
            )
            self.assertEqual(expected_result, result)

        mock_get.assert_called_once_with(
            'https://api.bintray.com/packages/lightbend/commercial-releases/ConductR-Universal',
            auth=(self.bintray_username, self.bintray_password)
        )

        mock_resolve_binary_from_cache.assert_called_once_with(self.image_dir, 'conductr', '2.0.8')

    def test_upgrade_not_required(self):
        mock_get = self.mock_get_versions(['2.1.0', '2.1.8'])

        mock_downloaded_artefact = MagicMock()
        mock_resolve_binary_from_cache = MagicMock(return_value=mock_downloaded_artefact)

        with patch('requests.get', mock_get), \
                patch('conductr_cli.sandbox_run_jvm.resolve_binary_from_cache', mock_resolve_binary_from_cache):
            result = sandbox_run_jvm.check_upgrade_requirements(self.bintray_auth, self.image_dir, '2.1.0')
            expected_result = sandbox_run_jvm.SandboxUpgradeRequirement(
                is_upgrade_required=False,
                current_version=semver.parse_version_info('2.1.0'),
                latest_version=semver.parse_version_info('2.1.8')
            )
            self.assertEqual(expected_result, result)

        mock_get.assert_called_once_with(
            'https://api.bintray.com/packages/lightbend/commercial-releases/ConductR-Universal',
            auth=(self.bintray_username, self.bintray_password)
        )

        mock_resolve_binary_from_cache.assert_called_once_with(self.image_dir, 'conductr', '2.1.8')

    def test_version_not_found(self):
        mock_get = self.mock_get_versions(['0.1.0', '0.1.8'])

        mock_resolve_binary_from_cache = MagicMock()

        with patch('requests.get', mock_get), \
                patch('conductr_cli.sandbox_run_jvm.resolve_binary_from_cache', mock_resolve_binary_from_cache):
            result = sandbox_run_jvm.check_upgrade_requirements(self.bintray_auth, self.image_dir, '2.1.0')
            self.assertIsNone(result)

        mock_get.assert_called_once_with(
            'https://api.bintray.com/packages/lightbend/commercial-releases/ConductR-Universal',
            auth=(self.bintray_username, self.bintray_password)
        )

        mock_resolve_binary_from_cache.assert_not_called()

    def test_http_error(self):
        mock_get = self.respond_with(500, 'test error')

        mock_resolve_binary_from_cache = MagicMock()

        with patch('requests.get', mock_get), \
                patch('conductr_cli.sandbox_run_jvm.resolve_binary_from_cache', mock_resolve_binary_from_cache):
            result = sandbox_run_jvm.check_upgrade_requirements(self.bintray_auth, self.image_dir, '2.1.0')
            self.assertIsNone(result)

        mock_get.assert_called_once_with(
            'https://api.bintray.com/packages/lightbend/commercial-releases/ConductR-Universal',
            auth=(self.bintray_username, self.bintray_password)
        )

        mock_resolve_binary_from_cache.assert_not_called()

    def test_url_error(self):
        mock_get = MagicMock(side_effect=URLError('test'))

        mock_resolve_binary_from_cache = MagicMock()

        with patch('requests.get', mock_get), \
                patch('conductr_cli.sandbox_run_jvm.resolve_binary_from_cache', mock_resolve_binary_from_cache):
            result = sandbox_run_jvm.check_upgrade_requirements(self.bintray_auth, self.image_dir, '2.1.0')
            self.assertIsNone(result)

        mock_get.assert_called_once_with(
            'https://api.bintray.com/packages/lightbend/commercial-releases/ConductR-Universal',
            auth=(self.bintray_username, self.bintray_password)
        )

        mock_resolve_binary_from_cache.assert_not_called()

    def test_connection_error(self):
        mock_get = MagicMock(side_effect=ConnectionError('test'))

        mock_resolve_binary_from_cache = MagicMock()

        with patch('requests.get', mock_get), \
                patch('conductr_cli.sandbox_run_jvm.resolve_binary_from_cache', mock_resolve_binary_from_cache):
            result = sandbox_run_jvm.check_upgrade_requirements(self.bintray_auth, self.image_dir, '2.1.0')
            self.assertIsNone(result)

        mock_get.assert_called_once_with(
            'https://api.bintray.com/packages/lightbend/commercial-releases/ConductR-Universal',
            auth=(self.bintray_username, self.bintray_password)
        )

        mock_resolve_binary_from_cache.assert_not_called()

    def mock_get_versions(self, version_numbers):
        json_text = json.dumps({'versions': version_numbers})
        return self.respond_with(200, json_text, 'application/json')
