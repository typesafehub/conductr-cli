from conductr_cli.test.cli_test_case import CliTestCase
from conductr_cli import sandbox_logs
from unittest.mock import MagicMock


class TestSandboxLogs(CliTestCase):
    def test_tail_args_built(self):
        self.assertEqual(
            ['/usr/bin/env', 'tail', '-q', '-n', '15', '/image/dir/core/logs/conductr.log', '/image/dir/agent/logs/conductr-agent.log'],

            sandbox_logs.logs_args(MagicMock(**{
                'image_dir': '/image/dir',
                'follow': False,
                'lines': 15
            }))
        )

        self.assertEqual(
            ['/usr/bin/env', 'tail', '-q', '-f', '--follow=name', '--retry', '-n', '35', '/some/image/dir/core/logs/conductr.log', '/some/image/dir/agent/logs/conductr-agent.log'],

            sandbox_logs.logs_args(MagicMock(**{
                'image_dir': '/some/image/dir',
                'follow': True,
                'lines': 35
            }))
        )
