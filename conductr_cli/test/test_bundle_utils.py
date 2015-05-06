from unittest import TestCase
from conductr_cli import bundle_utils
from conductr_cli.test.cli_test_case import create_temp_bundle
import shutil


class ShortId(TestCase):

    def test(self):
        self.assertEqual(
            bundle_utils.short_id('45e0c477d3e5ea92aa8d85c0d8f3e25c'),
            '45e0c47')

        self.assertEqual(
            bundle_utils.short_id('c1ab77e63b722ef8c6ea8a1c274be053-3cc322b62e7608b5cdf37185240f7853'),
            'c1ab77e-3cc322b')


class Conf(TestCase):

    def setUp(self):  # noqa
        self.tmpdir, self.bundle_path = create_temp_bundle('bundle conf contents')

    def test(self):
        conf_contents = bundle_utils.conf(self.bundle_path)
        self.assertEqual(conf_contents, 'bundle conf contents')

    def tearDown(self):  # noqa
        shutil.rmtree(self.tmpdir)
