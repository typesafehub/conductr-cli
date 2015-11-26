from unittest import TestCase
from conductr_cli.test.cli_test_case import strip_margin
from conductr_cli import sse_client

try:
    from unittest.mock import patch, MagicMock  # 3.3 and beyond
except ImportError:
    from mock import patch, MagicMock


class TestSSEClient(TestCase):
    def test_sse(self):
        raw_sse = strip_margin("""|data:
                                  |
                                  |event:My Test Event
                                  |data:My Test Data
                                  |
                                  |data:
                                  |
                                  |""")
        raw_sse_iterators = [iter(list(line)) for line in list(raw_sse)]
        iter_content_mock = MagicMock(side_effect=raw_sse_iterators)

        raise_for_status_mock = MagicMock()

        response_mock = MagicMock()
        response_mock.raise_for_status = raise_for_status_mock
        response_mock.iter_content = iter_content_mock

        request_get_mock = MagicMock(return_value=response_mock)

        result = []
        with patch('requests.get', request_get_mock):
            events = sse_client.get_events('http://host.com')
            for event in events:
                result.append(event)

        self.assertEqual([
            sse_client.Event(event=None, data=''),
            sse_client.Event(event='My Test Event', data='My Test Data'),
            sse_client.Event(event=None, data='')
        ], result)

        request_get_mock.assert_called_with('http://host.com', stream=True, **sse_client.SSE_REQUEST_INPUT)
        raise_for_status_mock.assert_called_with()
        iter_content_mock.assert_called_with(decode_unicode=True)
