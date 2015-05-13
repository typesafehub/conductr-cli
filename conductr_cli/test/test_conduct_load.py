from unittest import TestCase
from conductr_cli.test.cli_test_case import CliTestCase, create_temp_bundle, create_temp_bundle_with_contents, strip_margin
from conductr_cli import conduct_load
from urllib.error import URLError
import os
import shutil

try:
    from unittest.mock import call, patch, MagicMock  # 3.3 and beyond
except ImportError:
    from mock import call, patch, MagicMock


class TestConductLoadCommand(TestCase, CliTestCase):

    @property
    def default_response(self):
        return strip_margin("""|{
                               |  "bundleId": "45e0c477d3e5ea92aa8d85c0d8f3e25c"
                               |}
                               |""")

    nr_of_cpus = 1.0
    memory = 200
    disk_space = 100
    roles = ['web-server']
    bundleName = 'bundle'
    system = 'bundle'

    tmpdir, bundle_file = create_temp_bundle(
        strip_margin("""|nrOfCpus   = {}
                        |memory     = {}
                        |diskSpace  = {}
                        |roles      = [{}]
                        |name       = {}
                        |system     = {}
                        |""").format(nr_of_cpus, memory, disk_space, ', '.join(roles), bundleName, system))

    default_args = {
        'ip': '127.0.0.1',
        'port': 9005,
        'verbose': False,
        'long_ids': False,
        'cli_parameters': '',
        'bundle': bundle_file,
        'configuration': None
    }

    default_url = 'http://127.0.0.1:9005/bundles'

    default_files = [
        ('nrOfCpus', str(nr_of_cpus)),
        ('memory', str(memory)),
        ('diskSpace', str(disk_space)),
        ('roles', ' '.join(roles)),
        ('bundleName', bundleName),
        ('system', system),
        ('bundle', ('bundle.zip', 1))
    ]

    output_template = """|Retrieving bundle...
                         |{downloading_configuration}Loading bundle to ConductR...
                         |{verbose}Bundle loaded.
                         |Start bundle with: conduct run{params} {bundle_id}
                         |Unload bundle with: conduct unload{params} {bundle_id}
                         |Print ConductR info with: conduct info{params}
                         |"""

    @classmethod
    def tearDownClass(cls):  # noqa
        shutil.rmtree(cls.tmpdir)

    def default_output(self, params='', bundle_id='45e0c47', downloading_configuration='', verbose=''):
        return strip_margin(self.output_template.format(**{
            'params': params,
            'bundle_id': bundle_id,
            'downloading_configuration': downloading_configuration,
            'verbose': verbose}))

    def test_success(self):
        urlretrieve_mock = MagicMock(return_value=(self.bundle_file, ()))
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()
        open_mock = MagicMock(return_value=1)

        with patch('conductr_cli.conduct_load.urlretrieve', urlretrieve_mock), \
                patch('requests.post', http_method), \
                patch('sys.stdout', stdout), \
                patch('builtins.open', open_mock):
            conduct_load.load(MagicMock(**self.default_args))

        open_mock.assert_called_with(self.bundle_file, 'rb')
        http_method.assert_called_with(self.default_url, files=self.default_files)

        self.assertEqual(self.default_output(), self.output(stdout))

    def test_success_verbose(self):
        urlretrieve_mock = MagicMock(return_value=(self.bundle_file, ()))
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()
        open_mock = MagicMock(return_value=1)

        with patch('conductr_cli.conduct_load.urlretrieve', urlretrieve_mock), \
                patch('requests.post', http_method), \
                patch('sys.stdout', stdout), \
                patch('builtins.open', open_mock):
            args = self.default_args.copy()
            args.update({'verbose': True})
            conduct_load.load(MagicMock(**args))

        open_mock.assert_called_with(self.bundle_file, 'rb')
        http_method.assert_called_with(self.default_url, files=self.default_files)

        self.assertEqual(self.default_output(verbose=self.default_response), self.output(stdout))

    def test_success_long_ids(self):
        urlretrieve_mock = MagicMock(return_value=(self.bundle_file, ()))
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()
        open_mock = MagicMock(return_value=1)

        with patch('conductr_cli.conduct_load.urlretrieve', urlretrieve_mock), \
                patch('requests.post', http_method), \
                patch('sys.stdout', stdout), \
                patch('builtins.open', open_mock):
            args = self.default_args.copy()
            args.update({'long_ids': True})
            conduct_load.load(MagicMock(**args))

        open_mock.assert_called_with(self.bundle_file, 'rb')
        http_method.assert_called_with(self.default_url, files=self.default_files)

        self.assertEqual(self.default_output(bundle_id='45e0c477d3e5ea92aa8d85c0d8f3e25c'), self.output(stdout))

    def test_success_custom_ip_port(self):
        urlretrieve_mock = MagicMock(return_value=(self.bundle_file, ()))
        http_method = self.respond_with(200, self.default_response)
        stdout = MagicMock()
        open_mock = MagicMock(return_value=1)

        cli_parameters = ' --ip 127.0.1.1 --port 9006'
        with patch('conductr_cli.conduct_load.urlretrieve', urlretrieve_mock),\
                patch('requests.post', http_method), \
                patch('sys.stdout', stdout), \
                patch('builtins.open', open_mock):
            args = self.default_args.copy()
            args.update({'cli_parameters': cli_parameters})
            conduct_load.load(MagicMock(**args))

        open_mock.assert_called_with(self.bundle_file, 'rb')
        http_method.assert_called_with(self.default_url, files=self.default_files)

        self.assertEqual(
            self.default_output(params=cli_parameters),
            self.output(stdout))

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
        http_method.assert_called_with(self.default_url, files=expected_files)

        self.assertEqual(self.default_output(downloading_configuration='Retrieving configuration...\n'), self.output(stdout))

    def test_failure(self):
        urlretrieve_mock = MagicMock(return_value=(self.bundle_file, ()))
        http_method = self.respond_with(404)
        stderr = MagicMock()
        open_mock = MagicMock(return_value=1)

        with patch('conductr_cli.conduct_load.urlretrieve', urlretrieve_mock), \
                patch('requests.post', http_method), \
                patch('sys.stderr', stderr), \
                patch('builtins.open', open_mock):
            conduct_load.load(MagicMock(**self.default_args))

        open_mock.assert_called_with(self.bundle_file, 'rb')
        http_method.assert_called_with(self.default_url, files=self.default_files)

        self.assertEqual(
            strip_margin("""|ERROR: 404 Not Found
                            |"""),
            self.output(stderr))

    def test_failure_invalid_address(self):
        urlretrieve_mock = MagicMock(return_value=(self.bundle_file, ()))
        http_method = self.raise_connection_error('test reason', self.default_url)
        stderr = MagicMock()
        open_mock = MagicMock(return_value=1)

        with patch('conductr_cli.conduct_load.urlretrieve', urlretrieve_mock), \
                patch('requests.post', http_method), \
                patch('sys.stderr', stderr), \
                patch('builtins.open', open_mock):
            conduct_load.load(MagicMock(**self.default_args))

        open_mock.assert_called_with(self.bundle_file, 'rb')
        http_method.assert_called_with(self.default_url, files=self.default_files)

        self.assertEqual(
            self.default_connection_error.format(self.default_url),
            self.output(stderr))

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
            strip_margin("""|ERROR: Unable to parse bundle.conf.
                            |ERROR: No configuration setting found for key nrOfCpus.
                            |"""),
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
            strip_margin("""|ERROR: Unable to parse bundle.conf.
                            |ERROR: No configuration setting found for key memory.
                            |"""),
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
            strip_margin("""|ERROR: Unable to parse bundle.conf.
                            |ERROR: No configuration setting found for key diskSpace.
                            |"""),
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
            strip_margin("""|ERROR: Unable to parse bundle.conf.
                            |ERROR: No configuration setting found for key roles.
                            |"""),
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
            strip_margin("""|ERROR: Unable to parse bundle.conf.
                            |ERROR: roles has type 'str' rather than 'list'.
                            |"""),
            self.output(stderr))

        shutil.rmtree(tmpdir)

    def test_failure_no_bundle(self):
        urlretrieve_mock = MagicMock(side_effect=URLError('no_such.bundle'))
        stderr = MagicMock()

        with patch('conductr_cli.conduct_load.urlretrieve', urlretrieve_mock), patch('sys.stderr', stderr):
            args = self.default_args.copy()
            args.update({'bundle': 'no_such.bundle'})
            conduct_load.load(MagicMock(**args))

        self.assertEqual(
            strip_margin("""|ERROR: File not found: no_such.bundle
                            |"""),
            self.output(stderr))

    def test_failure_no_configuration(self):
        urlretrieve_mock = MagicMock(side_effect=[(self.bundle_file, ()), URLError('no_such.conf')])

        stderr = MagicMock()

        with patch('conductr_cli.conduct_load.urlretrieve', urlretrieve_mock), patch('sys.stderr', stderr):
            args = self.default_args.copy()
            args.update({'configuration': 'no_such.conf'})
            conduct_load.load(MagicMock(**args))

        self.assertEqual(
            strip_margin("""|ERROR: File not found: no_such.conf
                            |"""),
            self.output(stderr))


class TestGetUrl(TestCase):

    def test_url(self):
        filename, url = conduct_load.get_url('https://site.com/bundle-1.0-e78ed07d4a895e14595a21aef1bf616b1b0e4d886f3265bc7b152acf93d259b5.zip')
        self.assertEqual('bundle-1.0-e78ed07d4a895e14595a21aef1bf616b1b0e4d886f3265bc7b152acf93d259b5.zip', filename)
        self.assertEqual('https://site.com/bundle-1.0-e78ed07d4a895e14595a21aef1bf616b1b0e4d886f3265bc7b152acf93d259b5.zip', url)

    def test_file(self):
        filename, url = conduct_load.get_url('bundle-1.0-e78ed07d4a895e14595a21aef1bf616b1b0e4d886f3265bc7b152acf93d259b5.zip')
        self.assertEqual('bundle-1.0-e78ed07d4a895e14595a21aef1bf616b1b0e4d886f3265bc7b152acf93d259b5.zip', filename)
        self.assertEqual('file://' + os.getcwd() + '/bundle-1.0-e78ed07d4a895e14595a21aef1bf616b1b0e4d886f3265bc7b152acf93d259b5.zip', url)
