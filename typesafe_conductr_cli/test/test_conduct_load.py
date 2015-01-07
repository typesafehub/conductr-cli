from unittest import TestCase
from unittest.mock import call, patch, MagicMock
from typesafe_conductr_cli.test.utils import respond_with, output, strip_margin
from typesafe_conductr_cli import conduct_load


class TestConductLoadCommand(TestCase):

    default_response = strip_margin("""|{
                                      |  "bundleId": "45e0c477d3e5ea92aa8d85c0d8f3e25c"
                                      |}
                                      |""")

    default_args = {
        "host": "127.0.0.1",
        "port": 9005,
        "verbose": False,
        "cli_parameters": "",
        "nr_of_cpus": 1,
        "memory": 200,
        "disk_space": False,
        "roles": ["role1, role2"],
        "bundle": "bundle.tgz",
        "configuration": None
    }

    default_url = "http://127.0.0.1:9005/bundles"

    default_files = [
        ('nrOfCpus', '1'),
        ('memory', '200'),
        ('diskSpace', 'False'),
        ('roles', 'role1, role2'),
        ('bundle', 1)
    ]

    output_template = """|Bundle loaded.
                        |Start bundle with: conduct run{} 45e0c477d3e5ea92aa8d85c0d8f3e25c
                        |Unload bundle with: conduct unload{} 45e0c477d3e5ea92aa8d85c0d8f3e25c
                        |Print ConductR info with: conduct info{}
                        |"""

    default_output = strip_margin(output_template.format(*[""]*3))

    def test_success(self):
        http_method = respond_with(200, self.default_response)
        stdout = MagicMock()
        openMock = MagicMock(return_value=1)

        with patch('requests.post', http_method), patch('sys.stdout', stdout), patch('builtins.open', openMock):
            conduct_load.load(MagicMock(**self.default_args))

        openMock.assert_called_with("bundle.tgz", "rb")
        http_method.assert_called_with(self.default_url, files=self.default_files)

        self.assertEqual(self.default_output, output(stdout))

    def test_success_verbose(self):
        http_method = respond_with(200, self.default_response)
        stdout = MagicMock()
        openMock = MagicMock(return_value=1)

        with patch('requests.post', http_method), patch('sys.stdout', stdout), patch('builtins.open', openMock):
            args = self.default_args.copy()
            args.update({"verbose": True})
            conduct_load.load(MagicMock(**args))

        openMock.assert_called_with("bundle.tgz", "rb")
        http_method.assert_called_with(self.default_url, files=self.default_files)

        self.assertEqual(self.default_response + self.default_output, output(stdout))

    def test_success_custom_ip_port(self):
        http_method = respond_with(200, self.default_response)
        stdout = MagicMock()
        openMock = MagicMock(return_value=1)

        cli_parameters = " --host 127.0.1.1 --port 9006"
        with patch('requests.post', http_method), patch('sys.stdout', stdout), patch('builtins.open', openMock):
            args = self.default_args.copy()
            args.update({"cli_parameters": cli_parameters})
            conduct_load.load(MagicMock(**args))

        openMock.assert_called_with("bundle.tgz", "rb")
        http_method.assert_called_with(self.default_url, files=self.default_files)

        self.assertEqual(
            strip_margin(self.output_template.format(*[cli_parameters]*3)),
            output(stdout))

    def test_success_with_configuration(self):
        http_method = respond_with(200, self.default_response)
        stdout = MagicMock()
        openMock = MagicMock(return_value=1)

        with patch('requests.post', http_method), patch('sys.stdout', stdout), patch('builtins.open', openMock):
            args = self.default_args.copy()
            args.update({"configuration": "configuration.tgz"})
            conduct_load.load(MagicMock(**args))

        self.assertEqual(
            openMock.call_args_list,
            [call("bundle.tgz", "rb"), call("configuration.tgz", "rb")]
        )

        http_method.assert_called_with(self.default_url, files=self.default_files + [('configuration', 1)])

        self.assertEqual(self.default_output, output(stdout))

    def test_failure(self):
        http_method = respond_with(404)
        stderr = MagicMock()
        openMock = MagicMock(return_value=1)

        with patch('requests.post', http_method), patch('sys.stderr', stderr), patch('builtins.open', openMock):
            conduct_load.load(MagicMock(**self.default_args))

        openMock.assert_called_with("bundle.tgz", "rb")
        http_method.assert_called_with(self.default_url, files=self.default_files)

        self.assertEqual(
            strip_margin("""|ERROR:404 Not Found
                            |"""),
            output(stderr))

if __name__ == '__main__':
    unittest.main()
