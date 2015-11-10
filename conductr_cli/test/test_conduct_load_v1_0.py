from conductr_cli.test.conduct_load_test_base import ConductLoadTestBase
from conductr_cli.test.cli_test_case import create_temp_bundle, strip_margin
from conductr_cli import conduct_load
from unittest import TestCase
import os


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
            'api_version': '1.0',
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
        self.base_test_success_with_configuration()

    def test_failure(self):
        self.base_test_failure()

    def test_failure_invalid_address(self):
        self.base_test_failure_invalid_address()

    def test_failure_no_nr_of_cpus(self):
        self.base_test_failure_no_nr_of_cpus()

    def test_failure_no_memory(self):
        self.base_test_failure_no_memory()

    def test_failure_no_disk_space(self):
        self.base_test_failure_no_disk_space()

    def test_failure_no_roles(self):
        self.base_test_failure_no_roles()

    def test_failure_roles_not_a_list(self):
        self.base_test_failure_roles_not_a_list()

    def test_failure_no_bundle(self):
        self.base_test_failure_no_bundle()

    def test_failure_no_configuration(self):
        self.base_test_failure_no_configuration()


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
