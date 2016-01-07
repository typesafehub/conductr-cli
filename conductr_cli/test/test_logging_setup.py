from conductr_cli.test.cli_test_case import CliTestCase, as_error, as_warn, strip_margin
from conductr_cli import logging_setup
import logging

try:
    from unittest.mock import MagicMock  # 3.3 and beyond
except ImportError:
    from mock import MagicMock


class TestRootLogger(CliTestCase):
    def test_should_display_error_only(self):
        stdout = MagicMock()
        stderr = MagicMock()
        logging_setup.configure_logging(MagicMock(), stdout, stderr)

        log = logging.getLogger()
        log.debug('this is debug')
        log.verbose('this is verbose')
        log.info('this is info')
        log.quiet('this is quiet')
        log.warning('this is warning')
        log.error('this is error')

        self.assertFalse(log.is_debug_enabled())
        self.assertFalse(log.is_verbose_enabled())
        self.assertFalse(log.is_info_enabled())
        self.assertFalse(log.is_quiet_enabled())
        self.assertFalse(log.is_warn_enabled())

        self.assertEqual('', self.output(stdout))
        self.assertEqual(as_error('Error: this is error\n'), self.output(stderr))


class TestConductrCliLogger(CliTestCase):
    def test_default_settings(self):
        stdout = MagicMock()
        stderr = MagicMock()
        logging_setup.configure_logging(MagicMock(), stdout, stderr)

        log = logging.getLogger('conductr_cli')
        log.debug('this is debug')
        log.verbose('this is verbose')
        log.info('this is info')
        log.progress('this is progress', flush=True)
        log.quiet('this is quiet')
        log.warning('this is warning')
        log.error('this is error')
        log.screen('this is screen')

        self.assertFalse(log.is_debug_enabled())
        self.assertFalse(log.is_verbose_enabled())
        self.assertTrue(log.is_info_enabled())
        self.assertTrue(log.is_progress_enabled())
        self.assertTrue(log.is_quiet_enabled())
        self.assertTrue(log.is_warn_enabled())

        self.assertEqual(as_warn(strip_margin("""|this is info
                                                 |this is progress
                                                 |this is quiet
                                                 |Warning: this is warning
                                                 |this is screen
                                                 |""")), self.output(stdout))
        self.assertEqual(as_error('Error: this is error\n'), self.output(stderr))

    def test_verbose_settings(self):
        stdout = MagicMock()
        stderr = MagicMock()
        logging_setup.configure_logging(MagicMock(**{'verbose': True}), stdout, stderr)

        log = logging.getLogger('conductr_cli')
        log.debug('this is debug')
        log.verbose('this is verbose')
        log.info('this is info')
        log.progress('this is progress', flush=True)
        log.quiet('this is quiet')
        log.warning('this is warning')
        log.error('this is error')
        log.screen('this is screen')

        self.assertFalse(log.is_debug_enabled())
        self.assertTrue(log.is_verbose_enabled())
        self.assertTrue(log.is_info_enabled())
        self.assertTrue(log.is_progress_enabled())
        self.assertTrue(log.is_quiet_enabled())
        self.assertTrue(log.is_warn_enabled())

        self.assertEqual(as_warn(strip_margin("""|this is verbose
                                                 |this is info
                                                 |this is progress
                                                 |this is quiet
                                                 |Warning: this is warning
                                                 |this is screen
                                                 |""")), self.output(stdout))
        self.assertEqual(as_error('Error: this is error\n'), self.output(stderr))

    def test_quiet_settings(self):
        stdout = MagicMock()
        stderr = MagicMock()
        logging_setup.configure_logging(MagicMock(**{'quiet': True}), stdout, stderr)

        log = logging.getLogger('conductr_cli')
        log.debug('this is debug')
        log.verbose('this is verbose')
        log.info('this is info')
        log.progress('this is progress', flush=True)
        log.quiet('this is quiet')
        log.warning('this is warning')
        log.error('this is error')
        log.screen('this is screen')

        self.assertFalse(log.is_debug_enabled())
        self.assertFalse(log.is_verbose_enabled())
        self.assertFalse(log.is_info_enabled())
        self.assertFalse(log.is_progress_enabled())
        self.assertTrue(log.is_quiet_enabled())
        self.assertTrue(log.is_warn_enabled())

        self.assertEqual(as_warn(strip_margin("""|this is quiet
                                                 |Warning: this is warning
                                                 |this is screen
                                                 |""")), self.output(stdout))
        self.assertEqual(as_error('Error: this is error\n'), self.output(stderr))

    def test_progress_terminal_replace_characters(self):
        stdout = MagicMock()
        stderr = MagicMock()
        logging_setup.configure_logging(MagicMock(), stdout, stderr)

        log = logging.getLogger('conductr_cli')
        log.progress('1', flush=False)
        log.progress('**', flush=False)
        log.progress('XYZ', flush=True)

        char_output = [c for c in self.output(stdout)]
        self.assertEqual(['1', '\r',
                          '*', '*', '\r',
                          'X', 'Y', 'Z', '\n'], char_output)
