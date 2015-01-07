from unittest import TestCase
from unittest.mock import patch, MagicMock
from test_utils import respond_with, output, strip_margin


class TestConductUnloadCommand(TestCase):

    defaultResponse = strip_margin("""|{
                                      |  "bundleId": "45e0c477d3e5ea92aa8d85c0d8f3e25c"
                                      |}
                                      |""")

    defaultArgs = {
        "host": "127.0.0.1",
        "port": 9005,
        "verbose": False,
        "bundle": "45e0c477d3e5ea92aa8d85c0d8f3e25c"
    }

    defaultUrl = "http://127.0.0.1:9005/bundles/45e0c477d3e5ea92aa8d85c0d8f3e25c"

    defaultOutput = strip_margin("""|Bundle unload request sent.
                                    |Print ConductR info with: cli/conduct info
                                    |""")

    def test_success(self):
        requests = respond_with(200, self.defaultResponse)
        stdout = MagicMock()

        with patch.dict('sys.modules', requests=requests), patch('sys.stdout', stdout):
            import conduct_unload
            conduct_unload.unload(MagicMock(**self.defaultArgs))

        requests.delete.assert_called_with(self.defaultUrl)

        self.assertEqual(self.defaultOutput, output(stdout))

    def test_success_verbose(self):
        requests = respond_with(200, self.defaultResponse)
        stdout = MagicMock()

        with patch.dict('sys.modules', requests=requests), patch('sys.stdout', stdout):
            import conduct_unload
            args = self.defaultArgs.copy()
            args.update({"verbose": True})
            conduct_unload.unload(MagicMock(**args))

        requests.delete.assert_called_with(self.defaultUrl)

        self.assertEqual(self.defaultResponse + self.defaultOutput, output(stdout))

    def test_failure(self):
        requests = respond_with(404)
        stderr = MagicMock()

        with patch.dict('sys.modules', requests=requests), patch('sys.stderr', stderr):
            import conduct_unload
            conduct_unload.unload(MagicMock(**self.defaultArgs))

        requests.delete.assert_called_with(self.defaultUrl)

        self.assertEqual(
            strip_margin("""|ERROR:404 Not Found
                            |"""),
            output(stderr))

if __name__ == '__main__':
    unittest.main()
