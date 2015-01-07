from unittest import TestCase
from unittest.mock import patch, MagicMock
from typesafe_conductr_cli.test.utils import respond_with, output, strip_margin
from typesafe_conductr_cli import conduct_unload


class TestConductUnloadCommand(TestCase):

    defaultResponse = strip_margin("""|{
                                      |  "bundleId": "45e0c477d3e5ea92aa8d85c0d8f3e25c"
                                      |}
                                      |""")

    defaultArgs = {
        "host": "127.0.0.1",
        "port": 9005,
        "verbose": False,
        "cli_parameters": "",
        "bundle": "45e0c477d3e5ea92aa8d85c0d8f3e25c"
    }

    defaultUrl = "http://127.0.0.1:9005/bundles/45e0c477d3e5ea92aa8d85c0d8f3e25c"

    outputTemplate = """|Bundle unload request sent.
                        |Print ConductR info with: conduct info{}
                        |"""

    defaultOutput = strip_margin(outputTemplate.format(""))

    def test_success(self):
        http_method = respond_with(200, self.defaultResponse)
        stdout = MagicMock()

        with patch('requests.delete', http_method), patch('sys.stdout', stdout):
            conduct_unload.unload(MagicMock(**self.defaultArgs))

        http_method.assert_called_with(self.defaultUrl)

        self.assertEqual(self.defaultOutput, output(stdout))

    def test_success_verbose(self):
        http_method = respond_with(200, self.defaultResponse)
        stdout = MagicMock()

        with patch('requests.delete', http_method), patch('sys.stdout', stdout):
            args = self.defaultArgs.copy()
            args.update({"verbose": True})
            conduct_unload.unload(MagicMock(**args))

        http_method.assert_called_with(self.defaultUrl)

        self.assertEqual(self.defaultResponse + self.defaultOutput, output(stdout))

    def test_success_with_configuration(self):
        http_method = respond_with(200, self.defaultResponse)
        stdout = MagicMock()

        cli_parameters = " --host 127.0.1.1 --port 9006"
        with patch('requests.delete', http_method), patch('sys.stdout', stdout):
            args = self.defaultArgs.copy()
            args.update({"cli_parameters": cli_parameters})
            conduct_unload.unload(MagicMock(**args))

        http_method.assert_called_with(self.defaultUrl)

        self.assertEqual(
            strip_margin(self.outputTemplate.format(cli_parameters)),
            output(stdout))

    def test_failure(self):
        http_method = respond_with(404)
        stderr = MagicMock()

        with patch('requests.delete', http_method), patch('sys.stderr', stderr):
            conduct_unload.unload(MagicMock(**self.defaultArgs))

        http_method.assert_called_with(self.defaultUrl)

        self.assertEqual(
            strip_margin("""|ERROR:404 Not Found
                            |"""),
            output(stderr))

if __name__ == '__main__':
    unittest.main()
