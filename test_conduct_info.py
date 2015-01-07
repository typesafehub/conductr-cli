from unittest import TestCase
from unittest.mock import patch, MagicMock
from test_utils import respond_with, output, strip_margin


class TestConductInfoCommand(TestCase):

    defaultArgs = {
        "host": "127.0.0.1",
        "port": 9005,
        "verbose": False
    }

    defaultUrl = "http://127.0.0.1:9005/bundles"

    def test_no_bundles(self):
        requests = respond_with(text="[]")
        stdout = MagicMock()

        with patch.dict('sys.modules', requests=requests), patch('sys.stdout', stdout):
            import conduct_info
            conduct_info.info(MagicMock(**self.defaultArgs))

        requests.get.assert_called_with(self.defaultUrl)
        self.assertEqual(
            strip_margin("""|ID  #RUN
                            |"""),
            output(stdout))

    def test_stopped_bundle(self):
        requests = respond_with(text="""[
            {
                "bundleId": "45e0c477d3e5ea92aa8d85c0d8f3e25c",
                "bundleExecutions": []
            }
        ]""")
        stdout = MagicMock()

        with patch.dict('sys.modules', requests=requests), patch('sys.stdout', stdout):
            import conduct_info
            conduct_info.info(MagicMock(**self.defaultArgs))

        requests.get.assert_called_with(self.defaultUrl)
        self.assertEqual(
            strip_margin("""|ID                                #RUN
                            |45e0c477d3e5ea92aa8d85c0d8f3e25c  0
                            |"""),
            output(stdout))

    def test_one_running_one_stopped(self):
        requests = respond_with(text="""[
            {
                "bundleId": "45e0c477d3e5ea92aa8d85c0d8f3e25c",
                "bundleExecutions": [1,2,3]
            },
            {
                "bundleId": "c52e3f8d0c58d8aa29ae5e3d774c0e54",
                "bundleExecutions": []
            }
        ]""")
        stdout = MagicMock()

        with patch.dict('sys.modules', requests=requests), patch('sys.stdout', stdout):
            import conduct_info
            conduct_info.info(MagicMock(**self.defaultArgs))

        requests.get.assert_called_with(self.defaultUrl)
        self.assertEqual(
            strip_margin("""|ID                                #RUN
                            |45e0c477d3e5ea92aa8d85c0d8f3e25c  3
                            |c52e3f8d0c58d8aa29ae5e3d774c0e54  0
                            |"""),
            output(stdout))

    def test_one_running_one_stopped_verbose(self):
        requests = respond_with(text="""[
            {
                "bundleId": "45e0c477d3e5ea92aa8d85c0d8f3e25c",
                "bundleExecutions": [1,2,3]
            },
            {
                "bundleId": "c52e3f8d0c58d8aa29ae5e3d774c0e54",
                "bundleExecutions": []
            }
        ]""")
        stdout = MagicMock()

        with patch.dict('sys.modules', requests=requests), patch('sys.stdout', stdout):
            import conduct_info
            args = self.defaultArgs.copy()
            args.update({"verbose": True})
            conduct_info.info(MagicMock(**args))

        requests.get.assert_called_with(self.defaultUrl)
        self.assertEqual(
            strip_margin("""|[
                            |  {
                            |    "bundleExecutions": [
                            |      1,
                            |      2,
                            |      3
                            |    ],
                            |    "bundleId": "45e0c477d3e5ea92aa8d85c0d8f3e25c"
                            |  },
                            |  {
                            |    "bundleExecutions": [],
                            |    "bundleId": "c52e3f8d0c58d8aa29ae5e3d774c0e54"
                            |  }
                            |]
                            |ID                                #RUN
                            |45e0c477d3e5ea92aa8d85c0d8f3e25c  3
                            |c52e3f8d0c58d8aa29ae5e3d774c0e54  0
                            |"""),
            output(stdout))

if __name__ == '__main__':
    unittest.main()
