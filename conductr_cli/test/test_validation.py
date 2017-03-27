from argparse import ArgumentTypeError
from conductr_cli.validation import argparse_json, argparse_version
from conductr_cli.test.cli_test_case import CliTestCase


class TestTerminal(CliTestCase):
    def test_argparse_version_number(self):
        self.assertEqual(argparse_version('1'), '1')
        self.assertEqual(argparse_version('1.1'), '1.1')
        self.assertEqual(argparse_version('1.1.0'), '1.1.0')
        self.assertEqual(argparse_version('1.1.0-SNAPSHOT'), '1.1.0-SNAPSHOT')
        self.assertEqual(argparse_version('1.2.3.4.5'), '1.2.3.4.5')
        self.assertEqual(argparse_version('2'), '2')
        self.assertEqual(argparse_version('2.0.0'), '2.0.0')
        self.assertEqual(argparse_version('2.0.0-SNAPSHOT'), '2.0.0-SNAPSHOT')

        with self.assertRaises(ArgumentTypeError):
            argparse_version('potato')

        with self.assertRaises(ArgumentTypeError):
            argparse_version('1.')

        with self.assertRaises(ArgumentTypeError):
            argparse_version(' asdf 1 hello')

    def test_argparse_json(self):
        self.assertEqual(argparse_json('[]'), [])
        self.assertEqual(argparse_json('{}'), {})
        self.assertEqual(argparse_json('["hello", "there"]'), ['hello', 'there'])
        self.assertEqual(argparse_json('[null]'), [None])
        self.assertEqual(argparse_json('{"year":2000}'), {'year': 2000})
        self.assertEqual(argparse_json('1'), 1)
        self.assertTrue(argparse_json('true'))
        self.assertFalse(argparse_json('false'))
        self.assertEqual(argparse_json('0'), 0)
        self.assertEqual(argparse_json('1.5'), 1.5)
        self.assertEqual(argparse_json('""'), '')
        self.assertEqual(argparse_json('null'), None)

        with self.assertRaises(ArgumentTypeError):
            argparse_json('potato')

        with self.assertRaises(ArgumentTypeError):
            argparse_json('1.')

        with self.assertRaises(ArgumentTypeError):
            argparse_json("{ 'wrong': 'quotes'}")
