from conductr_cli.test.cli_test_case import CliTestCase
from conductr_cli import sandbox_common
from unittest.mock import patch, MagicMock


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
        ps_output = '58001   ??  Ss     0:36.97 /sbin/launchd\n' \
                    '58002   ??  Ss     0:30.48 /Library/Java/JavaVirtualMachines/jdk1.8.0_112.jdk/Contents/Home/bin/java -Dconductr.ip=192.168.10.1 -cp /Users/mj/.conductr/images/core/lib/com.typesafe.conductr.conductr-2.0.0-rc.2.jar:/dependent-libs com.typesafe.conductr.ConductR\n' \
                    '58003   ??  Ss     1:17.36 /Library/Java/JavaVirtualMachines/jdk1.8.0_112.jdk/Contents/Home/bin/java -Dconductr.agent.ip=192.168.10.1 -cp /Users/mj/.conductr/images/agent/lib/com.typesafe.conductr.conductr-agent-2.0.0-rc.2.jar:/dependent-libs com.typesafe.conductr.agent.ConductRAgent --core-node 192.168.10.1:9004\n' \
                    '58004   ??  Ss     0:30.48 /Library/Java/JavaVirtualMachines/jdk1.8.0_112.jdk/Contents/Home/bin/java -Dconductr.ip=192.168.10.2 -cp /Users/mj/.conductr/images/core/lib/com.typesafe.conductr.conductr-2.0.0-rc.2.jar:/dependent-libs com.typesafe.conductr.ConductR\n' \
                    '58005   ??  Ss     1:17.36 /Library/Java/JavaVirtualMachines/jdk1.8.0_112.jdk/Contents/Home/bin/java -Dconductr.agent.ip=192.168.10.2 -cp /Users/mj/.conductr/images/agent/lib/com.typesafe.conductr.conductr-agent-2.0.0-rc.2.jar:/dependent-libs com.typesafe.conductr.agent.ConductRAgent --core-node 192.168.10.2:9004\n' \
                    '58006   ??  Ss     0:30.48 /Library/Java/JavaVirtualMachines/jdk1.8.0_112.jdk/Contents/Home/bin/java -Dconductr.ip=192.168.10.3 -cp /Users/mj/.conductr/images/core/lib/com.typesafe.conductr.conductr-2.0.0-rc.2.jar:/dependent-libs com.typesafe.conductr.ConductR\n' \
                    '58007   ??  Ss     1:17.36 /Library/Java/JavaVirtualMachines/jdk1.8.0_112.jdk/Contents/Home/bin/java -Dconductr.agent.ip=192.168.10.3 -cp /Users/mj/.conductr/images/agent/lib/com.typesafe.conductr.conductr-agent-2.0.0-rc.2.jar:/dependent-libs com.typesafe.conductr.agent.ConductRAgent --core-node 192.168.10.3:9004\n' \
                    '58008   ??  Ss     0:36.97 /usr/libexec/logd'

        mock_getoutput = MagicMock(return_value=ps_output)

        with patch('subprocess.getoutput', mock_getoutput):
            result = sandbox_common.find_pids(self.core_run_dir, self.agent_run_dir)
            self.assertEqual([
                {'id': 58002, 'type': 'core', 'ip': '192.168.10.1'},
                {'id': 58003, 'type': 'agent', 'ip': '192.168.10.1'},
                {'id': 58004, 'type': 'core', 'ip': '192.168.10.2'},
                {'id': 58005, 'type': 'agent', 'ip': '192.168.10.2'},
                {'id': 58006, 'type': 'core', 'ip': '192.168.10.3'},
                {'id': 58007, 'type': 'agent', 'ip': '192.168.10.3'}
            ], result)

    def test_no_pids(self):
        ps_output = '58001   ??  Ss     0:36.97 /sbin/launchd\n' \
                    '58008   ??  Ss     0:36.97 /usr/libexec/logd'

        mock_getoutput = MagicMock(return_value=ps_output)

        with patch('subprocess.getoutput', mock_getoutput):
            result = sandbox_common.find_pids(self.core_run_dir, self.agent_run_dir)
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
