from unittest import TestCase
from conductr_cli.test.cli_test_case import CliTestCase, create_temp_bundle, strip_margin
from conductr_cli.test.conduct_load_test_base import ConductLoadTestBase
from conductr_cli import conduct_load
import os
import shutil


class TestConductLoadCommand(TestCase, ConductLoadTestBase, CliTestCase):

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
        'api_version': '1.0',
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

    @classmethod
    def tearDownClass(cls):  # noqa
        shutil.rmtree(cls.tmpdir)


class TestGetUrl(TestCase):

    def test_url(self):
        filename, url = conduct_load.get_url('https://site.com/bundle-1.0-e78ed07d4a895e14595a21aef1bf616b1b0e4d886f3265bc7b152acf93d259b5.zip')
        self.assertEqual('bundle-1.0-e78ed07d4a895e14595a21aef1bf616b1b0e4d886f3265bc7b152acf93d259b5.zip', filename)
        self.assertEqual('https://site.com/bundle-1.0-e78ed07d4a895e14595a21aef1bf616b1b0e4d886f3265bc7b152acf93d259b5.zip', url)

    def test_file(self):
        filename, url = conduct_load.get_url('bundle-1.0-e78ed07d4a895e14595a21aef1bf616b1b0e4d886f3265bc7b152acf93d259b5.zip')
        self.assertEqual('bundle-1.0-e78ed07d4a895e14595a21aef1bf616b1b0e4d886f3265bc7b152acf93d259b5.zip', filename)
        self.assertEqual('file://' + os.getcwd() + '/bundle-1.0-e78ed07d4a895e14595a21aef1bf616b1b0e4d886f3265bc7b152acf93d259b5.zip', url)
