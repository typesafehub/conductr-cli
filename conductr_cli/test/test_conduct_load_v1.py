from conductr_cli.test.conduct_load_test_base import ConductLoadTestBase
from conductr_cli.test.cli_test_case import create_temp_bundle, strip_margin, as_error, \
    create_temp_bundle_with_contents
from conductr_cli import conduct_load
from conductr_cli.conduct_load import LOAD_HTTP_TIMEOUT
from unittest import TestCase
import os
import shutil

try:
    from unittest.mock import call, patch, MagicMock  # 3.3 and beyond
except ImportError:
    from mock import call, patch, MagicMock


class TestConductLoadCommand(ConductLoadTestBase):

    def __init__(self, method_name):
        super().__init__(method_name)

        self.nr_of_cpus = 1.0
        self.memory = 200
        self.disk_space = 100
        self.roles = ['web-server']
        self.bundleName = 'bundle'
        self.system = 'bundle'

        self.tmpdir, self.bundle_file = create_temp_bundle(
            strip_margin("""|nrOfCpus   = {}
                            |memory     = {}
                            |diskSpace  = {}
                            |roles      = [{}]
                            |name       = {}
                            |system     = {}
                            |""").format(self.nr_of_cpus,
                                         self.memory,
                                         self.disk_space,
                                         ', '.join(self.roles),
                                         self.bundleName,
                                         self.system))

        self.default_args = {
            'ip': '127.0.0.1',
            'port': 9005,
            'api_version': '1',
            'verbose': False,
            'long_ids': False,
            'cli_parameters': '',
            'bundle': self.bundle_file,
            'configuration': None
        }

        self.default_url = 'http://127.0.0.1:9005/bundles'

        self.default_files = [
            ('nrOfCpus', str(self.nr_of_cpus)),
            ('memory', str(self.memory)),
            ('diskSpace', str(self.disk_space)),
            ('roles', ' '.join(self.roles)),
            ('bundleName', self.bundleName),
            ('system', self.system),
            ('bundle', ('bundle.zip', 1))
        ]

    def test_success(self):
        self.base_test_success()

    def test_success_verbose(self):
        self.base_test_success_verbose()

    def test_success_long_ids(self):
        self.base_test_success_long_ids()

    def test_success_custom_ip_port(self):
        self.base_test_success_custom_ip_port()

    def test_success_with_configuration(self):
        tmpdir, config_file = create_temp_bundle_with_contents({
            'bundle.conf': '{name="overlaid-name"}',
            'config.sh': 'echo configuring'
        })

        urlretrieve_mock = MagicMock(side_effect=[(self.bundle_file, ()), (config_file, ())])
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()
        open_mock = MagicMock(return_value=1)

        with patch('conductr_cli.conduct_load.urlretrieve', urlretrieve_mock), \
                patch('requests.post', http_method), \
                patch('sys.stdout', stdout), \
                patch('builtins.open', open_mock):
            args = self.default_args.copy()
            args.update({'configuration': config_file})
            conduct_load.load(MagicMock(**args))

        self.assertEqual(
            open_mock.call_args_list,
            [call(self.bundle_file, 'rb'), call(config_file, 'rb')]
        )

        expected_files = self.default_files + [('configuration', ('bundle.zip', 1))]
        expected_files[4] = ('bundleName', 'overlaid-name')
        http_method.assert_called_with(self.default_url, files=expected_files, timeout=LOAD_HTTP_TIMEOUT)

        self.assertEqual(self.default_output(downloading_configuration='Retrieving configuration...\n'),
                         self.output(stdout))

    def test_failure(self):
        self.base_test_failure()

    def test_failure_invalid_address(self):
        self.base_test_failure_invalid_address()

    def test_failure_no_bundle(self):
        self.base_test_failure_no_bundle()

    def test_failure_no_configuration(self):
        self.base_test_failure_no_configuration()

    def test_failure_no_nr_of_cpus(self):
        stderr = MagicMock()

        tmpdir, bundle_file = create_temp_bundle(
            strip_margin("""|memory     = {}
                            |diskSpace  = {}
                            |roles      = [{}]
                            |""").format(self.memory, self.disk_space, ', '.join(self.roles)))

        with patch('sys.stderr', stderr):
            args = self.default_args.copy()
            args.update({'bundle': bundle_file})
            conduct_load.load(MagicMock(**args))

        self.assertEqual(
            as_error(strip_margin("""|Error: Unable to parse bundle.conf.
                                     |Error: No configuration setting found for key nrOfCpus.
                                     |""")),
            self.output(stderr))

        shutil.rmtree(tmpdir)

    def test_failure_no_memory(self):
        stderr = MagicMock()

        tmpdir, bundle_file = create_temp_bundle(
            strip_margin("""|nrOfCpus   = {}
                            |diskSpace  = {}
                            |roles      = [{}]
                            |""").format(self.nr_of_cpus, self.disk_space, ', '.join(self.roles)))

        with patch('sys.stderr', stderr):
            args = self.default_args.copy()
            args.update({'bundle': bundle_file})
            conduct_load.load(MagicMock(**args))

        self.assertEqual(
            as_error(strip_margin("""|Error: Unable to parse bundle.conf.
                                     |Error: No configuration setting found for key memory.
                                     |""")),
            self.output(stderr))

        shutil.rmtree(tmpdir)

    def test_failure_no_disk_space(self):
        stderr = MagicMock()

        tmpdir, bundle_file = create_temp_bundle(
            strip_margin("""|nrOfCpus   = {}
                            |memory     = {}
                            |roles      = [{}]
                            |""").format(self.nr_of_cpus, self.memory, ', '.join(self.roles)))

        with patch('sys.stderr', stderr):
            args = self.default_args.copy()
            args.update({'bundle': bundle_file})
            conduct_load.load(MagicMock(**args))

        self.assertEqual(
            as_error(strip_margin("""|Error: Unable to parse bundle.conf.
                                     |Error: No configuration setting found for key diskSpace.
                                     |""")),
            self.output(stderr))

        shutil.rmtree(tmpdir)

    def test_failure_no_roles(self):
        stderr = MagicMock()

        tmpdir, bundle_file = create_temp_bundle(
            strip_margin("""|nrOfCpus   = {}
                            |memory     = {}
                            |diskSpace  = {}
                            |""").format(self.nr_of_cpus, self.memory, self.disk_space))

        with patch('sys.stderr', stderr):
            args = self.default_args.copy()
            args.update({'bundle': bundle_file})
            conduct_load.load(MagicMock(**args))

        self.assertEqual(
            as_error(strip_margin("""|Error: Unable to parse bundle.conf.
                                     |Error: No configuration setting found for key roles.
                                     |""")),
            self.output(stderr))

        shutil.rmtree(tmpdir)

    def test_failure_roles_not_a_list(self):
        stderr = MagicMock()

        tmpdir, bundle_file = create_temp_bundle(
            strip_margin("""|nrOfCpus   = {}
                            |memory     = {}
                            |diskSpace  = {}
                            |roles      = {}
                            |""").format(self.nr_of_cpus, self.memory, self.disk_space, '-'.join(self.roles)))

        with patch('sys.stderr', stderr):
            args = self.default_args.copy()
            args.update({'bundle': bundle_file})
            conduct_load.load(MagicMock(**args))

        self.assertEqual(
            as_error(strip_margin("""|Error: Unable to parse bundle.conf.
                                     |Error: roles has type 'str' rather than 'list'.
                                     |""")),
            self.output(stderr))

        shutil.rmtree(tmpdir)


class TestGetUrl(TestCase):

    def test_url(self):
        filename, url = conduct_load.get_url(
            'https://site.com/bundle-1.0-e78ed07d4a895e14595a21aef1bf616b1b0e4d886f3265bc7b152acf93d259b5.zip')
        self.assertEqual(
            'bundle-1.0-e78ed07d4a895e14595a21aef1bf616b1b0e4d886f3265bc7b152acf93d259b5.zip', filename)
        self.assertEqual(
            'https://site.com/bundle-1.0-e78ed07d4a895e14595a21aef1bf616b1b0e4d886f3265bc7b152acf93d259b5.zip', url)

    def test_file(self):
        filename, url = conduct_load.get_url(
            'bundle-1.0-e78ed07d4a895e14595a21aef1bf616b1b0e4d886f3265bc7b152acf93d259b5.zip')
        self.assertEqual(
            'bundle-1.0-e78ed07d4a895e14595a21aef1bf616b1b0e4d886f3265bc7b152acf93d259b5.zip', filename)
        self.assertEqual(
            'file://' + os.getcwd() +
            '/bundle-1.0-e78ed07d4a895e14595a21aef1bf616b1b0e4d886f3265bc7b152acf93d259b5.zip', url)
