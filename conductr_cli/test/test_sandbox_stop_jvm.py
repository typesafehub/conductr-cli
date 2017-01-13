from conductr_cli.test.cli_test_case import CliTestCase, as_error, strip_margin
from conductr_cli import sandbox_stop_jvm, logging_setup
from conductr_cli.screen_utils import headline
from unittest.mock import patch, MagicMock, call
import signal


class TestStop(CliTestCase):

    default_args = {
        'local_connection': True,
        'verbose': False,
        'quiet': False,
        'image_dir': '/Users/mj/.conductr/images'
    }

    def test_stop_processes_with_first_attempt(self):
        ps_output_first = '58001   ??  Ss     0:36.97 /sbin/launchd\n' \
                          '58002   ??  Ss     0:30.48 /Library/Java/JavaVirtualMachines/jdk1.8.0_112.jdk/Contents/Home/bin/java -Dconductr.ip=192.168.10.1 -cp /Users/mj/.conductr/images/core/lib/com.typesafe.conductr.conductr-2.0.0-rc.2.jar:/dependent-libs com.typesafe.conductr.ConductR\n' \
                          '58003   ??  Ss     1:17.36 /Library/Java/JavaVirtualMachines/jdk1.8.0_112.jdk/Contents/Home/bin/java -Dconductr.agent.ip=192.168.10.1 -cp /Users/mj/.conductr/images/agent/lib/com.typesafe.conductr.conductr-agent-2.0.0-rc.2.jar:/dependent-libs com.typesafe.conductr.agent.ConductRAgent --core-node 192.168.10.1:9004\n' \
                          '58004   ??  Ss     0:30.48 /Library/Java/JavaVirtualMachines/jdk1.8.0_112.jdk/Contents/Home/bin/java -Dconductr.ip=192.168.10.2 -cp /Users/mj/.conductr/images/core/lib/com.typesafe.conductr.conductr-2.0.0-rc.2.jar:/dependent-libs com.typesafe.conductr.ConductR\n' \
                          '58005   ??  Ss     1:17.36 /Library/Java/JavaVirtualMachines/jdk1.8.0_112.jdk/Contents/Home/bin/java -Dconductr.agent.ip=192.168.10.2 -cp /Users/mj/.conductr/images/agent/lib/com.typesafe.conductr.conductr-agent-2.0.0-rc.2.jar:/dependent-libs com.typesafe.conductr.agent.ConductRAgent --core-node 192.168.10.2:9004\n' \
                          '58006   ??  Ss     0:30.48 /Library/Java/JavaVirtualMachines/jdk1.8.0_112.jdk/Contents/Home/bin/java -Dconductr.ip=192.168.10.3 -cp /Users/mj/.conductr/images/core/lib/com.typesafe.conductr.conductr-2.0.0-rc.2.jar:/dependent-libs com.typesafe.conductr.ConductR\n' \
                          '58007   ??  Ss     1:17.36 /Library/Java/JavaVirtualMachines/jdk1.8.0_112.jdk/Contents/Home/bin/java -Dconductr.agent.ip=192.168.10.3 -cp /Users/mj/.conductr/images/agent/lib/com.typesafe.conductr.conductr-agent-2.0.0-rc.2.jar:/dependent-libs com.typesafe.conductr.agent.ConductRAgent --core-node 192.168.10.3:9004\n' \
                          '58008   ??  Ss     0:36.97 /usr/libexec/logd'
        ps_output_second = '58001   ??  Ss     0:36.97 /sbin/launchd\n' \
                           '58008   ??  Ss     0:36.97 /usr/libexec/logd'

        stdout = MagicMock()
        mock_os_kill = MagicMock()
        mock_time_sleep = MagicMock()
        mock_subprocess_getoutput = MagicMock(side_effect=[ps_output_first, ps_output_second])

        with patch('os.kill', mock_os_kill), \
                patch('time.sleep', mock_time_sleep), \
                patch('subprocess.getoutput', mock_subprocess_getoutput), \
                patch('conductr_cli.sandbox_stop_jvm', mock_subprocess_getoutput):
            logging_setup.configure_logging(MagicMock(**self.default_args), stdout)
            sandbox_stop_jvm.stop(MagicMock(**self.default_args))

        self.assertEqual(strip_margin("""||------------------------------------------------|
                                         || Stopping ConductR                              |
                                         ||------------------------------------------------|
                                         |ConductR core pid 58002 stopped
                                         |ConductR agent pid 58003 stopped
                                         |ConductR core pid 58004 stopped
                                         |ConductR agent pid 58005 stopped
                                         |ConductR core pid 58006 stopped
                                         |ConductR agent pid 58007 stopped
                                         |ConductR has been successfully stopped
                                         |"""), self.output(stdout))
        mock_os_kill.assert_has_calls([call(58002, signal.SIGTERM),
                                       call(58003, signal.SIGTERM),
                                       call(58004, signal.SIGTERM),
                                       call(58005, signal.SIGTERM),
                                       call(58006, signal.SIGTERM),
                                       call(58007, signal.SIGTERM)])

    def test_stop_processes_with_second_attempt(self):
        ps_output_first = '58001   ??  Ss     0:36.97 /sbin/launchd\n' \
                          '58002   ??  Ss     0:30.48 /Library/Java/JavaVirtualMachines/jdk1.8.0_112.jdk/Contents/Home/bin/java -Dconductr.ip=192.168.10.1 -cp /Users/mj/.conductr/images/core/lib/com.typesafe.conductr.conductr-2.0.0-rc.2.jar:/dependent-libs com.typesafe.conductr.ConductR\n' \
                          '58003   ??  Ss     1:17.36 /Library/Java/JavaVirtualMachines/jdk1.8.0_112.jdk/Contents/Home/bin/java -Dconductr.agent.ip=192.168.10.1 -cp /Users/mj/.conductr/images/agent/lib/com.typesafe.conductr.conductr-agent-2.0.0-rc.2.jar:/dependent-libs com.typesafe.conductr.agent.ConductRAgent --core-node 192.168.10.1:9004\n' \
                          '58004   ??  Ss     0:30.48 /Library/Java/JavaVirtualMachines/jdk1.8.0_112.jdk/Contents/Home/bin/java -Dconductr.ip=192.168.10.2 -cp /Users/mj/.conductr/images/core/lib/com.typesafe.conductr.conductr-2.0.0-rc.2.jar:/dependent-libs com.typesafe.conductr.ConductR\n' \
                          '58005   ??  Ss     1:17.36 /Library/Java/JavaVirtualMachines/jdk1.8.0_112.jdk/Contents/Home/bin/java -Dconductr.agent.ip=192.168.10.2 -cp /Users/mj/.conductr/images/agent/lib/com.typesafe.conductr.conductr-agent-2.0.0-rc.2.jar:/dependent-libs com.typesafe.conductr.agent.ConductRAgent --core-node 192.168.10.2:9004\n' \
                          '58006   ??  Ss     0:30.48 /Library/Java/JavaVirtualMachines/jdk1.8.0_112.jdk/Contents/Home/bin/java -Dconductr.ip=192.168.10.3 -cp /Users/mj/.conductr/images/core/lib/com.typesafe.conductr.conductr-2.0.0-rc.2.jar:/dependent-libs com.typesafe.conductr.ConductR\n' \
                          '58007   ??  Ss     1:17.36 /Library/Java/JavaVirtualMachines/jdk1.8.0_112.jdk/Contents/Home/bin/java -Dconductr.agent.ip=192.168.10.3 -cp /Users/mj/.conductr/images/agent/lib/com.typesafe.conductr.conductr-agent-2.0.0-rc.2.jar:/dependent-libs com.typesafe.conductr.agent.ConductRAgent --core-node 192.168.10.3:9004\n' \
                          '58008   ??  Ss     0:36.97 /usr/libexec/logd'
        ps_output_second = '58001   ??  Ss     0:36.97 /sbin/launchd\n' \
                           '58002   ??  Ss     0:30.48 /Library/Java/JavaVirtualMachines/jdk1.8.0_112.jdk/Contents/Home/bin/java -Dconductr.ip=192.168.10.1 -cp /Users/mj/.conductr/images/core/lib/com.typesafe.conductr.conductr-2.0.0-rc.2.jar:/dependent-libs com.typesafe.conductr.ConductR\n' \
                           '58003   ??  Ss     1:17.36 /Library/Java/JavaVirtualMachines/jdk1.8.0_112.jdk/Contents/Home/bin/java -Dconductr.agent.ip=192.168.10.1 -cp /Users/mj/.conductr/images/agent/lib/com.typesafe.conductr.conductr-agent-2.0.0-rc.2.jar:/dependent-libs com.typesafe.conductr.agent.ConductRAgent --core-node 192.168.10.1:9004\n' \
                           '58008   ??  Ss     0:36.97 /usr/libexec/logd'
        ps_output_third = '58001   ??  Ss     0:36.97 /sbin/launchd\n' \
                          '58008   ??  Ss     0:36.97 /usr/libexec/logd'

        stdout = MagicMock()
        mock_os_kill = MagicMock()
        mock_time_sleep = MagicMock()
        mock_subprocess_getoutput = MagicMock(side_effect=[ps_output_first, ps_output_second, ps_output_third])

        with patch('os.kill', mock_os_kill), \
                patch('time.sleep', mock_time_sleep), \
                patch('subprocess.getoutput', mock_subprocess_getoutput), \
                patch('conductr_cli.sandbox_stop_jvm', mock_subprocess_getoutput):
            logging_setup.configure_logging(MagicMock(**self.default_args), stdout)
            sandbox_stop_jvm.stop(MagicMock(**self.default_args))

        self.assertEqual(strip_margin("""||------------------------------------------------|
                                         || Stopping ConductR                              |
                                         ||------------------------------------------------|
                                         |ConductR core pid 58004 stopped
                                         |ConductR agent pid 58005 stopped
                                         |ConductR core pid 58006 stopped
                                         |ConductR agent pid 58007 stopped
                                         |ConductR core pid 58002 stopped
                                         |ConductR agent pid 58003 stopped
                                         |ConductR has been successfully stopped
                                         |"""), self.output(stdout))
        mock_os_kill.assert_has_calls([call(58002, signal.SIGTERM),
                                       call(58003, signal.SIGTERM),
                                       call(58004, signal.SIGTERM),
                                       call(58005, signal.SIGTERM),
                                       call(58006, signal.SIGTERM),
                                       call(58007, signal.SIGTERM)])

    def test_hung_processes(self):
        ps_output = '58001   ??  Ss     0:36.97 /sbin/launchd\n' \
                    '58002   ??  Ss     0:30.48 /Library/Java/JavaVirtualMachines/jdk1.8.0_112.jdk/Contents/Home/bin/java -Dconductr.ip=192.168.10.1 -cp /Users/mj/.conductr/images/core/lib/com.typesafe.conductr.conductr-2.0.0-rc.2.jar:/dependent-libs com.typesafe.conductr.ConductR\n' \
                    '58003   ??  Ss     1:17.36 /Library/Java/JavaVirtualMachines/jdk1.8.0_112.jdk/Contents/Home/bin/java -Dconductr.agent.ip=192.168.10.1 -cp /Users/mj/.conductr/images/agent/lib/com.typesafe.conductr.conductr-agent-2.0.0-rc.2.jar:/dependent-libs com.typesafe.conductr.agent.ConductRAgent --core-node 192.168.10.1:9004\n' \
                    '58008   ??  Ss     0:36.97 /usr/libexec/logd'

        stdout = MagicMock()
        stderr = MagicMock()
        mock_os_kill = MagicMock()
        mock_time_sleep = MagicMock()
        mock_subprocess_getoutput = MagicMock(return_value=ps_output)

        with patch('os.kill', mock_os_kill), \
                patch('time.sleep', mock_time_sleep), \
                patch('subprocess.getoutput', mock_subprocess_getoutput), \
                patch('conductr_cli.sandbox_stop_jvm', mock_subprocess_getoutput):
            logging_setup.configure_logging(MagicMock(**self.default_args), stdout, stderr)
            sandbox_stop_jvm.stop(MagicMock(**self.default_args))

        self.assertEqual(headline('Stopping ConductR') + '\n', self.output(stdout))
        self.assertEqual(strip_margin(as_error("""|Error: ConductR core pid 58002 could not be stopped
                                                  |Error: ConductR agent pid 58003 could not be stopped
                                                  |Error: Please stop the processes manually
                                                  |""")), self.output(stderr))
        mock_os_kill.assert_has_calls([call(58002, signal.SIGTERM),
                                       call(58003, signal.SIGTERM)])

    def test_no_process(self):
        ps_output = '58001   ??  Ss     0:36.97 /sbin/launchd\n' \
                    '58008   ??  Ss     0:36.97 /usr/libexec/logd'

        stdout = MagicMock()
        mock_os_kill = MagicMock()
        mock_subprocess_getoutput = MagicMock(return_value=ps_output)

        with patch('os.kill', mock_os_kill), \
                patch('subprocess.getoutput', mock_subprocess_getoutput), \
                patch('conductr_cli.sandbox_stop_jvm', mock_subprocess_getoutput):
            logging_setup.configure_logging(MagicMock(**self.default_args), stdout)
            sandbox_stop_jvm.stop(MagicMock(**self.default_args))

        self.assertEqual('', self.output(stdout))
        mock_os_kill.assert_not_called()
