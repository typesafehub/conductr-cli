from argparse import ArgumentTypeError
from conductr_cli import logging_setup, validation
from conductr_cli.exceptions import BundleResolutionError
from conductr_cli.resolvers import bintray_resolver
from conductr_cli.validation import argparse_version, HostnameLookupError
from conductr_cli.test.cli_test_case import CliTestCase, strip_margin, as_error
from unittest.mock import patch, MagicMock


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
        expect_pass('1.1.0-alpha.1')
        expect_pass('1.2.3.4.5')
        expect_pass('2')
        expect_pass('2.0.0')
        expect_pass('2.0.0-beta.1')

        expect_fail('potato')
        expect_fail('1.')
        expect_fail(' asdf 1 hello')


class TestErrorHandler(CliTestCase):
    def test_handle_hostname_lookup_error(self):
        def raise_hostname_lookup_error():
            raise HostnameLookupError()

        mock_gethostname = MagicMock(return_value='MagicBox')

        args = MagicMock(**{})
        stdout = MagicMock()
        stderr = MagicMock()
        logging_setup.configure_logging(args, stdout, stderr)

        with patch('socket.gethostname', mock_gethostname):
            function_to_call = validation.handle_hostname_lookup_error(raise_hostname_lookup_error)
            function_to_call()

        mock_gethostname.assert_called_once_with()

        self.assertEqual(self.output(stdout), '')

        expected_output = as_error(strip_margin("""|Error: Hostname lookup on your machine will take more than 5 seconds which will result in a ConductR startup failure
                                                   |Error: This is known Java 8 issue on macOS: http://stackoverflow.com/questions/39636792/jvm-takes-a-long-time-to-resolve-ip-address-for-localhost
                                                   |Error: To speed up the hostname lookup add your macOS hostname to /etc/hosts
                                                   |Error: Resolves your hostname on the terminal with: hostname
                                                   |Error: Sample /etc/hosts file:
                                                   |Error: 127.0.0.1   localhost MagicBox
                                                   |Error: ::1         localhost MagicBox
                                                   |"""))
        self.assertEqual(self.output(stderr), expected_output)

    def test_handle_bundle_resolution_error_with_bundle_errors(self):
        error1 = Exception('error 1')
        error2 = Exception('error 2')

        mock_resolver_name = 'mock resolver 2'
        mock_resolver = MagicMock(name=mock_resolver_name)
        mock_resolver.__name__ = mock_resolver_name

        def raise_error():
            raise BundleResolutionError('test error',
                                        cache_resolution_errors=[],
                                        bundle_resolution_errors=[
                                            (bintray_resolver, error1),
                                            (mock_resolver, error2),
                                        ])

        args = MagicMock(**{})
        stdout = MagicMock()
        stderr = MagicMock()
        logging_setup.configure_logging(args, stdout, stderr)

        function_to_call = validation.handle_bundle_resolution_error(raise_error)
        function_to_call()

        self.assertEqual('', self.output(stdout))

        expected_error = as_error(strip_margin(
            """|Error: test error
               |Error: RESOLVER         ERROR
               |Error: Bintray          error 1
               |Error: mock resolver 2  error 2
               |"""
        ))
        self.assertEqual(expected_error, self.output(stderr))

    def test_handle_bundle_resolution_error_with_cache_errors(self):
        error1 = Exception('error 1')
        error2 = Exception('error 2')

        mock_resolver_name = 'mock resolver 2'
        mock_resolver = MagicMock(name=mock_resolver_name)
        mock_resolver.__name__ = mock_resolver_name

        def raise_error():
            raise BundleResolutionError('test error',
                                        cache_resolution_errors=[
                                            (bintray_resolver, error1),
                                            (mock_resolver, error2),
                                        ],
                                        bundle_resolution_errors=[])

        args = MagicMock(**{})
        stdout = MagicMock()
        stderr = MagicMock()
        logging_setup.configure_logging(args, stdout, stderr)

        function_to_call = validation.handle_bundle_resolution_error(raise_error)
        function_to_call()

        self.assertEqual('', self.output(stdout))

        expected_error = as_error(strip_margin(
            """|Error: test error
               |Error: RESOLVER         ERROR
               |Error: Bintray          error 1
               |Error: mock resolver 2  error 2
               |"""
        ))
        self.assertEqual(expected_error, self.output(stderr))

    def test_handle_bundle_resolution_error_with_bundle_and_cache_errors(self):
        error1 = Exception('error 1')
        error2 = Exception('error 2')
        error3 = Exception('error 2')

        mock_resolver_name = 'mock resolver 2'
        mock_resolver = MagicMock(name=mock_resolver_name)
        mock_resolver.__name__ = mock_resolver_name

        def raise_error():
            raise BundleResolutionError('test error',
                                        cache_resolution_errors=[
                                            (mock_resolver, error3)
                                        ],
                                        bundle_resolution_errors=[
                                            (bintray_resolver, error1),
                                            (mock_resolver, error2),
                                        ])

        args = MagicMock(**{})
        stdout = MagicMock()
        stderr = MagicMock()
        logging_setup.configure_logging(args, stdout, stderr)

        function_to_call = validation.handle_bundle_resolution_error(raise_error)
        function_to_call()

        self.assertEqual('', self.output(stdout))

        expected_error = as_error(strip_margin(
            """|Error: test error
               |Error: RESOLVER         ERROR
               |Error: Bintray          error 1
               |Error: mock resolver 2  error 2
               |"""
        ))
        self.assertEqual(expected_error, self.output(stderr))
