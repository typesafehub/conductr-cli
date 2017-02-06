from unittest import TestCase
from conductr_cli import validation
from unittest.mock import MagicMock
import arrow


class TestConductLogsCommand(TestCase):
    def test_format_date_timestamp_utc(self):
        timestamp = '2015-08-24T01:16:22.327Z'
        args = MagicMock(**{'utc': True})
        result = validation.format_timestamp(timestamp, args)
        self.assertEqual('Mon 2015-08-24T01:16:22Z', result)

    def test_format_date_timestamp(self):
        timestamp = '2015-08-24T01:16:22.327Z'
        args = MagicMock(**{'utc': False})
        result = validation.format_timestamp(timestamp, args)
        expected_result = arrow.get(timestamp).to('local').strftime('%a %Y-%m-%dT%H:%M:%S%z')
        self.assertEqual(expected_result, result)
