from conductr_cli.test.cli_test_case import CliTestCase
from conductr_cli import sandbox_logs
from unittest.mock import MagicMock

import io
import tempfile


class TestSandboxLogs(CliTestCase):
    def test_log_files_is_correct(self):
        self.assertEqual(
            ['/image/dir/core/logs/conductr.log', '/image/dir/agent/logs/conductr-agent.log'],

            sandbox_logs.log_files(MagicMock(**{'image_dir': '/image/dir'}))
        )

    def test_tail_reads_files(self):
        one_fd, one_path = tempfile.mkstemp()
        two_fd, two_path = tempfile.mkstemp()

        one_file = open(one_path, 'w')
        two_file = open(two_path, 'w')

        output = io.StringIO()

        one_file.write("line 1\nline 2\nline 3\n")
        one_file.close()
        two_file.write("line a\nline b\nline c\n")
        two_file.close()

        sandbox_logs.tail([one_path, two_path], False, output, 8, 0.25)

        self.assertEqual(
            "line 1\nline 2\nline 3\nline a\nline b\nline c\n",
            output.getvalue()
        )
