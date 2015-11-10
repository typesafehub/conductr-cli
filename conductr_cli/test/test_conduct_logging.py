from unittest import TestCase
from conductr_cli import validation
import arrow

try:
    from unittest.mock import MagicMock  # 3.3 and beyond
except ImportError:
    from mock import MagicMock


class TestConductLogsCommand(TestCase):
    def test_format_date_timestamp_utc(self):
        timestamp = '2015-08-24T01:16:22.327Z'
        args = MagicMock()
        args.date = True
        args.utc = True
        result = validation.format_timestamp(timestamp, args)
        self.assertEqual('2015-08-24T01:16:22Z', result)

    def test_format_timestamp_utc(self):
        timestamp = '2015-08-24T01:16:22.327Z'
        args = MagicMock()
        args.date = False
        args.utc = True
        result = validation.format_timestamp(timestamp, args)
        self.assertEqual('01:16:22Z', result)

    def test_format_date_timestamp(self):
        timestamp = '2015-08-24T01:16:22.327Z'
        args = MagicMock()
        args.date = True
        args.utc = False
        result = validation.format_timestamp(timestamp, args)
        expected_result = arrow.get(timestamp).to('local').datetime.strftime('%c')
        self.assertEqual(expected_result, result)

    def test_format_timestamp(self):
        timestamp = '2015-08-24T01:16:22.327Z'
        args = MagicMock()
        args.date = False
        args.utc = False
        result = validation.format_timestamp(timestamp, args)
        expected_result = arrow.get(timestamp).to('local').datetime.strftime('%X')
        self.assertEqual(expected_result, result)
