from unittest import TestCase
from unittest.mock import call, patch, MagicMock
from test_utils import respond_with, output, strip_margin


class TestConductLoadCommand(TestCase):

    defaultResponse = strip_margin("""|{
                                      |  "bundleId": "45e0c477d3e5ea92aa8d85c0d8f3e25c"
                                      |}
                                      |""")

    defaultArgs = {
        "host": "127.0.0.1",
        "port": 9005,
        "verbose": False,
        "nr_of_cpus": 1,
        "memory": 200,
        "disk_space": False,
        "roles": ["role1, role2"],
        "bundle": "bundle.tgz",
        "configuration": None
    }

    defaultUrl = "http://127.0.0.1:9005/bundles"

    defaultFiles = [
        ('nrOfCpus', '1'),
        ('memory', '200'),
        ('diskSpace', 'False'),
        ('roles', 'role1, role2'),
        ('bundle', 1)
    ]

    defaultOutput = strip_margin("""|Bundle loaded.
                                    |Start bundle with: cli/conduct run 45e0c477d3e5ea92aa8d85c0d8f3e25c
                                    |Unload bundle with: cli/conduct unload 45e0c477d3e5ea92aa8d85c0d8f3e25c
                                    |Print ConductR info with: cli/conduct info
                                    |""")

    def test_success(self):
        requests = respond_with(200, self.defaultResponse)
        stdout = MagicMock()
        openMock = MagicMock(return_value=1)

        with patch.dict('sys.modules', requests=requests), patch('sys.stdout', stdout), patch('builtins.open', openMock):
            import conduct_load
            conduct_load.load(MagicMock(**self.defaultArgs))

        openMock.assert_called_with("bundle.tgz", "rb")
        requests.post.assert_called_with(self.defaultUrl, files=self.defaultFiles)

        self.assertEqual(self.defaultOutput, output(stdout))

    def test_success_verbose(self):
        requests = respond_with(200, self.defaultResponse)
        stdout = MagicMock()
        openMock = MagicMock(return_value=1)

        with patch.dict('sys.modules', requests=requests), patch('sys.stdout', stdout), patch('builtins.open', openMock):
            import conduct_load
            args = self.defaultArgs.copy()
            args.update({"verbose": True})
            conduct_load.load(MagicMock(**args))

        openMock.assert_called_with("bundle.tgz", "rb")
        requests.post.assert_called_with(self.defaultUrl, files=self.defaultFiles)

        self.assertEqual(self.defaultResponse + self.defaultOutput, output(stdout))

    def test_success_with_configuration(self):
        requests = respond_with(200, self.defaultResponse)
        stdout = MagicMock()
        openMock = MagicMock(return_value=1)

        with patch.dict('sys.modules', requests=requests), patch('sys.stdout', stdout), patch('builtins.open', openMock):
            import conduct_load
            args = self.defaultArgs.copy()
            args.update({"configuration": "configuration.tgz"})
            conduct_load.load(MagicMock(**args))

        self.assertEqual(
            openMock.call_args_list,
            [call("bundle.tgz", "rb"), call("configuration.tgz", "rb")]
        )

        requests.post.assert_called_with(self.defaultUrl, files=self.defaultFiles + [('configuration', 1)])

        self.assertEqual(self.defaultOutput, output(stdout))

    def test_failure(self):
        requests = respond_with(404)
        stderr = MagicMock()
        openMock = MagicMock(return_value=1)

        with patch.dict('sys.modules', requests=requests), patch('sys.stderr', stderr), patch('builtins.open', openMock):
            import conduct_load
            conduct_load.load(MagicMock(**self.defaultArgs))

        openMock.assert_called_with("bundle.tgz", "rb")
        requests.post.assert_called_with(self.defaultUrl, files=self.defaultFiles)

        self.assertEqual(
            strip_margin("""|ERROR:404 Not Found
                            |"""),
            output(stderr))

if __name__ == '__main__':
    unittest.main()
