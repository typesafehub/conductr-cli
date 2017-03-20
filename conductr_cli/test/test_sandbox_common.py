from conductr_cli.test.cli_test_case import CliTestCase
from conductr_cli import logging_setup, sandbox_common
from conductr_cli.sandbox_common import DEFAULT_WAIT_RETRIES, DEFAULT_WAIT_RETRY_INTERVAL
from conductr_cli.exceptions import ConductrStartupError
from unittest.mock import call, patch, MagicMock
from requests.exceptions import ConnectionError


class TestSandboxCommon(CliTestCase):
    def test_bundle_http_port(self):
        port_number = 1111
        getenv_mock = MagicMock(return_value=port_number)
        with patch('os.getenv', getenv_mock):
            result = sandbox_common.bundle_http_port()

        self.assertEqual(result, port_number)
        getenv_mock.assert_called_with('BUNDLE_HTTP_PORT', 9000)


class TestFindPids(CliTestCase):
    image_dir = '/Users/mj/.conductr/images'
    core_run_dir = '{}/core'.format(image_dir)
    agent_run_dir = '{}/agent'.format(image_dir)

    def test_pids_found(self):
        ps = [
            {'pid': 58001, 'name': 'launchd', 'cmdline': ['/sbin/launchd']},
            {'pid': 58002, 'name': 'java', 'cmdline': ['/Library/Java/JavaVirtualMachines/jdk1.8.0_112.jdk/Contents/Home/bin/java', '-Dconductr.ip=192.168.10.1', '-cp', '/Users/mj/.conductr/images/core/lib/com.typesafe.conductr.conductr-2.0.0-rc.2.jar:/dependent-libs', 'com.typesafe.conductr.ConductR']},
            {'pid': 58003, 'name': 'java', 'cmdline': ['/Library/Java/JavaVirtualMachines/jdk1.8.0_112.jdk/Contents/Home/bin/java', '-Dconductr.agent.ip=192.168.10.1', '-cp', '/Users/mj/.conductr/images/agent/lib/com.typesafe.conductr.conductr-agent-2.0.0-rc.2.jar:/dependent-libs', 'com.typesafe.conductr.agent.ConductRAgent', '--core-node', '192.168.10.1:9004']},
            {'pid': 58004, 'name': 'java', 'cmdline': ['/Library/Java/JavaVirtualMachines/jdk1.8.0_112.jdk/Contents/Home/bin/java', '-Dconductr.ip=192.168.10.2', '-cp', '/Users/mj/.conductr/images/core/lib/com.typesafe.conductr.conductr-2.0.0-rc.2.jar:/dependent-libs', 'com.typesafe.conductr.ConductR']},
            {'pid': 58005, 'name': 'java', 'cmdline': ['/Library/Java/JavaVirtualMachines/jdk1.8.0_112.jdk/Contents/Home/bin/java', '-Dconductr.agent.ip=192.168.10.2', '-cp', '/Users/mj/.conductr/images/agent/lib/com.typesafe.conductr.conductr-agent-2.0.0-rc.2.jar:/dependent-libs', 'com.typesafe.conductr.agent.ConductRAgent', '--core-node', '192.168.10.2:9004']},
            {'pid': 58006, 'name': 'java', 'cmdline': ['/Library/Java/JavaVirtualMachines/jdk1.8.0_112.jdk/Contents/Home/bin/java', '-Dconductr.ip=192.168.10.3', '-cp', '/Users/mj/.conductr/images/core/lib/com.typesafe.conductr.conductr-2.0.0-rc.2.jar:/dependent-libs', 'com.typesafe.conductr.ConductR']},
            {'pid': 58007, 'name': 'java', 'cmdline': ['/Library/Java/JavaVirtualMachines/jdk1.8.0_112.jdk/Contents/Home/bin/java', '-Dconductr.agent.ip=192.168.10.3', '-cp', '/Users/mj/.conductr/images/agent/lib/com.typesafe.conductr.conductr-agent-2.0.0-rc.2.jar:/dependent-libs', 'com.typesafe.conductr.agent.ConductRAgent', '--core-node', '192.168.10.3:9004']},
            {'pid': 58008, 'name': 'logd', 'cmdline': ['/usr/libexec/logd']}
        ]

        result = sandbox_common.calculate_pids(self.core_run_dir, self.agent_run_dir, ps)

        self.assertEqual([
            {'id': 58002, 'type': 'core', 'ip': '192.168.10.1'},
            {'id': 58003, 'type': 'agent', 'ip': '192.168.10.1'},
            {'id': 58004, 'type': 'core', 'ip': '192.168.10.2'},
            {'id': 58005, 'type': 'agent', 'ip': '192.168.10.2'},
            {'id': 58006, 'type': 'core', 'ip': '192.168.10.3'},
            {'id': 58007, 'type': 'agent', 'ip': '192.168.10.3'}
        ], result)

    def test_no_pids(self):
        ps = [
            {'pid': 58001, 'name': 'launchd', 'cmdline': ['/sbin/launchd']},
            {'pid': 58008, 'name': 'logd', 'cmdline': ['/usr/libexec/logd']}
        ]

        result = sandbox_common.calculate_pids(self.core_run_dir, self.agent_run_dir, ps)
        self.assertEqual([], result)


class TestResolveConductRRolesByInstance(CliTestCase):
    user_roles = [['role1', 'role2'], ['role3']]
    feature_roles = ['elasticsearch', 'kibana']

    def test_user_and_feature_roles(self):
        self.assertEqual(
            ['role1', 'role2', 'elasticsearch', 'kibana'],
            sandbox_common.resolve_conductr_roles_by_instance(self.user_roles, self.feature_roles, instance=0))

        self.assertEqual(
            ['role3'],
            sandbox_common.resolve_conductr_roles_by_instance(self.user_roles, self.feature_roles, instance=1))

        self.assertEqual(
            ['role1', 'role2'],
            sandbox_common.resolve_conductr_roles_by_instance(self.user_roles, self.feature_roles, instance=2))

    def test_empty_user_roles(self):
        self.assertEqual(
            [],
            sandbox_common.resolve_conductr_roles_by_instance([], self.feature_roles, instance=0))

        self.assertEqual(
            [],
            sandbox_common.resolve_conductr_roles_by_instance([], self.feature_roles, instance=1))

        self.assertEqual(
            [],
            sandbox_common.resolve_conductr_roles_by_instance([], self.feature_roles, instance=2))

    def test_empty_feature_roles(self):
        self.assertEqual(
            ['role1', 'role2'],
            sandbox_common.resolve_conductr_roles_by_instance(self.user_roles, [], instance=0))

        self.assertEqual(
            ['role3'],
            sandbox_common.resolve_conductr_roles_by_instance(self.user_roles, [], instance=1))

        self.assertEqual(
            ['role1', 'role2'],
            sandbox_common.resolve_conductr_roles_by_instance(self.user_roles, [], instance=2))


class TestWaitForStart(CliTestCase):
    def test_wait_for_start(self):
        stdout = MagicMock()
        is_tty_mock = MagicMock(return_value=True)
        mock_get_env = MagicMock(return_value=1)

        members_url = '/members'
        mock_url = MagicMock(return_value=members_url)

        mock_http_get = MagicMock(return_value='test only')

        with \
                patch('os.getenv', mock_get_env), \
                patch('conductr_cli.conduct_url.url', mock_url), \
                patch('conductr_cli.conduct_request.get', mock_http_get), \
                patch('sys.stdout.isatty', is_tty_mock):
            args = MagicMock(**{})
            logging_setup.configure_logging(args, stdout)
            run_result = MagicMock(**{
                'host': '10.0.0.1'
            })
            result = sandbox_common.wait_for_start(run_result)
            self.assertEqual(True, result)

        self.assertEqual([
            call('CONDUCTR_SANDBOX_WAIT_RETRIES', DEFAULT_WAIT_RETRIES),
            call('CONDUCTR_SANDBOX_WAIT_RETRY_INTERVAL', DEFAULT_WAIT_RETRY_INTERVAL)
        ], mock_get_env.call_args_list)

        mock_http_get.assert_called_once_with(dcos_mode=False, host='10.0.0.1', timeout=5, url='/members')

        self.assertEqual([
            call.write('Waiting for ConductR to start\r'),
            call.write(''),
            call.flush(),
            call.write('Waiting for ConductR to start.\r'),
            call.write(''),
            call.flush(),
            call.write('Waiting for ConductR to start.\n'),
            call.write(''),
            call.flush()
        ], stdout.method_calls)

    def test_wait_for_start_timeout(self):
        stdout = MagicMock()
        is_tty_mock = MagicMock(return_value=True)
        mock_get_env = MagicMock(return_value=1)

        members_url = '/members'
        mock_url = MagicMock(return_value=members_url)

        mock_http_get = MagicMock(side_effect=[ConnectionError()])

        with \
                patch('os.getenv', mock_get_env), \
                patch('conductr_cli.conduct_url.url', mock_url), \
                patch('conductr_cli.conduct_request.get', mock_http_get), \
                patch('sys.stdout.isatty', is_tty_mock):
            args = MagicMock(**{})
            logging_setup.configure_logging(args, stdout)
            run_result = MagicMock(**{
                'host': '10.0.0.1'
            })
            self.assertRaises(ConductrStartupError, sandbox_common.wait_for_start, run_result)

        self.assertEqual([
            call('CONDUCTR_SANDBOX_WAIT_RETRIES', DEFAULT_WAIT_RETRIES),
            call('CONDUCTR_SANDBOX_WAIT_RETRY_INTERVAL', DEFAULT_WAIT_RETRY_INTERVAL)
        ], mock_get_env.call_args_list)

        mock_http_get.assert_called_once_with(dcos_mode=False, host='10.0.0.1', timeout=5, url='/members')

        self.assertEqual([
            call.write('Waiting for ConductR to start\r'),
            call.write(''),
            call.flush(),
            call.write('Waiting for ConductR to start.\r'),
            call.write(''),
            call.flush(),
            call.write('Waiting for ConductR to start.\n'),
            call.write(''),
            call.flush()
        ], stdout.method_calls)
