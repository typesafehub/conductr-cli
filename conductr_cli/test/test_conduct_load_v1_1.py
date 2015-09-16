from unittest import TestCase
from conductr_cli.test.cli_test_case import CliTestCase, create_temp_bundle, strip_margin
from conductr_cli.test.conduct_load_test_base import ConductLoadTestBase
import shutil


class TestConductLoadCommand(TestCase, ConductLoadTestBase, CliTestCase):

    nr_of_cpus = 1.0
    memory = 200
    disk_space = 100
    roles = ['web-server']
    bundleName = 'bundle'
    system = 'bundle'
    systemVersion = '2.3'
    compatibilityVersion = '2.0'

    tmpdir, bundle_file = create_temp_bundle(
        strip_margin("""|nrOfCpus               = {}
                        |memory                 = {}
                        |diskSpace              = {}
                        |roles                  = [{}]
                        |name                   = {}
                        |system                 = {}
                        |systemVersion          = {}
                        |compatibilityVersion   = {}
                        |""").format(nr_of_cpus, memory, disk_space, ', '.join(roles), bundleName, system, systemVersion, compatibilityVersion))

    default_args = {
        'ip': '127.0.0.1',
        'port': 9005,
        'api_version': '1.1',
        'verbose': False,
        'long_ids': False,
        'cli_parameters': '',
        'bundle': bundle_file,
        'configuration': None
    }

    default_url = 'http://127.0.0.1:9005/v1.1/bundles'

    default_files = [
        ('nrOfCpus', str(nr_of_cpus)),
        ('memory', str(memory)),
        ('diskSpace', str(disk_space)),
        ('roles', ' '.join(roles)),
        ('bundleName', bundleName),
        ('system', system),
        ('systemVersion', systemVersion),
        ('compatibilityVersion', compatibilityVersion),
        ('bundle', ('bundle.zip', 1))
    ]

    @classmethod
    def tearDownClass(cls):  # noqa
        shutil.rmtree(cls.tmpdir)
