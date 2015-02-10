from unittest import TestCase
from typesafe_conductr_cli import bundle_id


class TestConductInfoCommand(TestCase):

    def test_shorten(self):
        self.assertEqual(
            bundle_id.shorten('45e0c477d3e5ea92aa8d85c0d8f3e25c'),
            '45e0c47')

        self.assertEqual(
            bundle_id.shorten('c1ab77e63b722ef8c6ea8a1c274be053-3cc322b62e7608b5cdf37185240f7853'),
            'c1ab77e-3cc322b')
