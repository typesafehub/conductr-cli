from argparse import ArgumentTypeError
from conductr_cli.validation import argparse_version
from conductr_cli.test.cli_test_case import CliTestCase


class TestTerminal(CliTestCase):
    def test_argparse_version_number(self):
        def expect_fail(value):
            passed = False

            try:
                argparse_version(value)
            except ArgumentTypeError:
                passed = True

            self.assertTrue(passed)

        def expect_pass(value):
            self.assertEqual(argparse_version(value), value)

        expect_pass('1')
        expect_pass('1.1')
        expect_pass('1.1.0')
        expect_pass('1.1.0-SNAPSHOT')
        expect_pass('1.2.3.4.5')
        expect_pass('2')
        expect_pass('2.0.0')
        expect_pass('2.0.0-SNAPSHOT')

        expect_fail('potato')
        expect_fail('1.')
        expect_fail(' asdf 1 hello')
