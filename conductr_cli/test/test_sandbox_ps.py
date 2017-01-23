from conductr_cli.test.cli_test_case import CliTestCase, strip_margin
from conductr_cli import logging_setup, sandbox_ps
from unittest.mock import patch, MagicMock


class TestSandboxPs(CliTestCase):
    image_dir = 'image_dir'

    core_extraction_dir = 'core_extraction_dir'

    core_info = {
        'extraction_dir': core_extraction_dir
    }

    agent_extraction_dir = 'agent_extraction_dir'

    agent_info = {
        'extraction_dir': agent_extraction_dir
    }

    pid_infos = [
        {'id': 58002, 'type': 'core', 'ip': '192.168.10.1'},
        {'id': 58003, 'type': 'agent', 'ip': '192.168.10.1'}
    ]

    default_args = {
        'image_dir': image_dir,
        'is_filter_core': False,
        'is_filter_agent': False,
        'is_quiet': False
    }

    def test_default(self):
        stdout = MagicMock()

        mock_resolve_conductr_info = MagicMock(return_value=(self.core_info, self.agent_info))
        mock_find_pids = MagicMock(return_value=self.pid_infos)

        input_args = MagicMock(**self.default_args)

        with patch('conductr_cli.sandbox_common.resolve_conductr_info', mock_resolve_conductr_info), \
                patch('conductr_cli.sandbox_common.find_pids', mock_find_pids):
            logging_setup.configure_logging(input_args, stdout)
            sandbox_ps.ps(input_args)

        mock_resolve_conductr_info.assert_called_once_with(self.image_dir)
        mock_find_pids.assert_called_once_with(self.core_extraction_dir, self.agent_extraction_dir)

        expected_output = strip_margin("""|PID     TYPE            IP
                                          |58002   core  192.168.10.1
                                          |58003  agent  192.168.10.1
                                          |""")
        self.assertEqual(expected_output, self.output(stdout))

    def test_quiet(self):
        stdout = MagicMock()

        mock_resolve_conductr_info = MagicMock(return_value=(self.core_info, self.agent_info))
        mock_find_pids = MagicMock(return_value=self.pid_infos)

        args = self.default_args.copy()
        args.update({
            'is_quiet': True
        })
        input_args = MagicMock(**args)

        with patch('conductr_cli.sandbox_common.resolve_conductr_info', mock_resolve_conductr_info), \
                patch('conductr_cli.sandbox_common.find_pids', mock_find_pids):
            logging_setup.configure_logging(input_args, stdout)
            sandbox_ps.ps(input_args)

        mock_resolve_conductr_info.assert_called_once_with(self.image_dir)
        mock_find_pids.assert_called_once_with(self.core_extraction_dir, self.agent_extraction_dir)

        expected_output = strip_margin("""|58002
                                          |58003
                                          |""")
        self.assertEqual(expected_output, self.output(stdout))

    def test_filter_core(self):
        stdout = MagicMock()

        mock_resolve_conductr_info = MagicMock(return_value=(self.core_info, self.agent_info))
        mock_find_pids = MagicMock(return_value=self.pid_infos)

        args = self.default_args.copy()
        args.update({
            'is_filter_core': True
        })
        input_args = MagicMock(**args)

        with patch('conductr_cli.sandbox_common.resolve_conductr_info', mock_resolve_conductr_info), \
                patch('conductr_cli.sandbox_common.find_pids', mock_find_pids):
            logging_setup.configure_logging(input_args, stdout)
            sandbox_ps.ps(input_args)

        mock_resolve_conductr_info.assert_called_once_with(self.image_dir)
        mock_find_pids.assert_called_once_with(self.core_extraction_dir, self.agent_extraction_dir)

        expected_output = strip_margin("""|PID    TYPE            IP
                                          |58002  core  192.168.10.1
                                          |""")
        self.assertEqual(expected_output, self.output(stdout))

    def test_filter_core_quiet(self):
        stdout = MagicMock()

        mock_resolve_conductr_info = MagicMock(return_value=(self.core_info, self.agent_info))
        mock_find_pids = MagicMock(return_value=self.pid_infos)

        args = self.default_args.copy()
        args.update({
            'is_filter_core': True,
            'is_quiet': True
        })
        input_args = MagicMock(**args)

        with patch('conductr_cli.sandbox_common.resolve_conductr_info', mock_resolve_conductr_info), \
                patch('conductr_cli.sandbox_common.find_pids', mock_find_pids):
            logging_setup.configure_logging(input_args, stdout)
            sandbox_ps.ps(input_args)

        mock_resolve_conductr_info.assert_called_once_with(self.image_dir)
        mock_find_pids.assert_called_once_with(self.core_extraction_dir, self.agent_extraction_dir)

        expected_output = strip_margin("""|58002
                                          |""")
        self.assertEqual(expected_output, self.output(stdout))

    def test_filter_agent(self):
        stdout = MagicMock()

        mock_resolve_conductr_info = MagicMock(return_value=(self.core_info, self.agent_info))
        mock_find_pids = MagicMock(return_value=self.pid_infos)

        args = self.default_args.copy()
        args.update({
            'is_filter_agent': True
        })
        input_args = MagicMock(**args)

        with patch('conductr_cli.sandbox_common.resolve_conductr_info', mock_resolve_conductr_info), \
                patch('conductr_cli.sandbox_common.find_pids', mock_find_pids):
            logging_setup.configure_logging(input_args, stdout)
            sandbox_ps.ps(input_args)

        mock_resolve_conductr_info.assert_called_once_with(self.image_dir)
        mock_find_pids.assert_called_once_with(self.core_extraction_dir, self.agent_extraction_dir)

        expected_output = strip_margin("""|PID     TYPE            IP
                                          |58003  agent  192.168.10.1
                                          |""")
        self.assertEqual(expected_output, self.output(stdout))

    def test_filter_agent_quiet(self):
        stdout = MagicMock()

        mock_resolve_conductr_info = MagicMock(return_value=(self.core_info, self.agent_info))
        mock_find_pids = MagicMock(return_value=self.pid_infos)

        args = self.default_args.copy()
        args.update({
            'is_filter_agent': True,
            'is_quiet': True
        })
        input_args = MagicMock(**args)

        with patch('conductr_cli.sandbox_common.resolve_conductr_info', mock_resolve_conductr_info), \
                patch('conductr_cli.sandbox_common.find_pids', mock_find_pids):
            logging_setup.configure_logging(input_args, stdout)
            sandbox_ps.ps(input_args)

        mock_resolve_conductr_info.assert_called_once_with(self.image_dir)
        mock_find_pids.assert_called_once_with(self.core_extraction_dir, self.agent_extraction_dir)

        expected_output = strip_margin("""|58003
                                          |""")
        self.assertEqual(expected_output, self.output(stdout))
