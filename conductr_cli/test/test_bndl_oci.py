from conductr_cli import bndl_utils, bndl_oci
from conductr_cli.test.cli_test_case import CliTestCase, create_attributes_object, strip_margin
from io import BytesIO
from pyhocon import ConfigFactory
import os
import shutil
import tarfile
import tempfile


class TestBndlOci(CliTestCase):
    def test_oci_image_unpack_tar_wrong_format(self):
        file = tempfile.NamedTemporaryFile()
        dest_tmpdir = tempfile.mkdtemp()

        try:
            with tarfile.open(fileobj=file, mode='w') as tar:
                tar.addfile(tarfile.TarInfo('testing'), BytesIO(b'hello'))

            file.seek(0)

            with tarfile.open(fileobj=file, mode='r') as tar:
                self.assertFalse(bndl_oci.oci_image_unpack(dest_tmpdir, tar, is_dir=False))
        finally:
            shutil.rmtree(dest_tmpdir)

    def test_oci_image_unpack_dir_wrong_format(self):
        tmpdir = tempfile.mkdtemp()
        dest_tmpdir = tempfile.mkdtemp()

        try:
            with open(os.path.join(tmpdir, 'testing'), 'wb') as file:
                file.write('hello'.encode('UTF-8'))

            self.assertFalse(bndl_oci.oci_image_unpack(dest_tmpdir, tmpdir, is_dir=True))
        finally:
            shutil.rmtree(tmpdir)
            shutil.rmtree(dest_tmpdir)

    def test_oci_image_unpack_toplevel_tar(self):
        file = tempfile.NamedTemporaryFile()
        dest_tmpdir = tempfile.mkdtemp()

        try:
            with tarfile.open(fileobj=file, mode='w') as tar:
                tar.addfile(tarfile.TarInfo('oci-layout'), BytesIO(b'hello'))

            file.seek(0)

            with tarfile.open(fileobj=file, mode='r') as tar:
                self.assertTrue(bndl_oci.oci_image_unpack(dest_tmpdir, tar, is_dir=False))

            self.assertTrue(os.path.exists(os.path.join(dest_tmpdir, 'oci-layout')))
        finally:
            shutil.rmtree(dest_tmpdir)

    def test_oci_image_unpack_nested_tar(self):
        file = tempfile.NamedTemporaryFile()
        dest_tmpdir = tempfile.mkdtemp()

        try:
            with tarfile.open(fileobj=file, mode='w') as tar:
                tar.addfile(tarfile.TarInfo('testing/nested/dirs/oci-layout'), BytesIO(b'hello'))

            file.seek(0)

            with tarfile.open(fileobj=file, mode='r') as tar:
                self.assertTrue(bndl_oci.oci_image_unpack(dest_tmpdir, tar, is_dir=False))

            self.assertTrue(os.path.exists(os.path.join(dest_tmpdir, 'oci-layout')))
        finally:
            shutil.rmtree(dest_tmpdir)

    def test_oci_image_unpack_toplevel_dir(self):
        tmpdir = tempfile.mkdtemp()
        dest_tmpdir = tempfile.mkdtemp()

        try:
            with open(os.path.join(tmpdir, 'oci-layout'), 'wb') as file:
                file.write('testing'.encode('UTF-8'))

            self.assertTrue(bndl_oci.oci_image_unpack(dest_tmpdir, tmpdir, is_dir=True))

            self.assertTrue(os.path.exists(os.path.join(dest_tmpdir, 'oci-layout')))
        finally:
            shutil.rmtree(tmpdir)
            shutil.rmtree(dest_tmpdir)

    def test_oci_image_unpack_nested_dir(self):
        tmpdir = tempfile.mkdtemp()
        dest_tmpdir = tempfile.mkdtemp()

        try:
            os.makedirs(os.path.join(tmpdir, 'testing', 'nested', 'dirs'))

            with open(os.path.join(tmpdir, 'testing', 'nested', 'dirs', 'oci-layout'), 'wb') as file:
                file.write('testing'.encode('UTF-8'))

            self.assertTrue(bndl_oci.oci_image_unpack(dest_tmpdir, tmpdir, True))

            self.assertTrue(os.path.exists(os.path.join(dest_tmpdir, 'oci-layout')))
        finally:
            shutil.rmtree(tmpdir)
            shutil.rmtree(dest_tmpdir)

    def test_oci_image_bundle_conf(self):
        base_args = create_attributes_object({
            'name': 'world',
            'component_description': 'testing desc 1',
            'tag': 'testing'
        })

        extended_args = create_attributes_object({
            'name': 'world',
            'component_description': 'testing desc 2',
            'version': '4',
            'compatibilityVersion': '5',
            'system': 'myapp',
            'systemVersion': '3',
            'nrOfCpus': '8',
            'memory': '65536',
            'diskSpace': '16384',
            'roles': ['web', 'backend'],
            'tag': 'latest'
        })

        # test that config value is specified
        simple_config = ConfigFactory.parse_string('')
        bndl_utils.load_bundle_args_into_conf(simple_config, base_args)
        self.assertEqual(simple_config.get('name'), 'world')

        # test that config value is overwritten
        name_config = ConfigFactory.parse_string('name = "hello"')
        bndl_utils.load_bundle_args_into_conf(name_config, base_args)
        self.assertEqual(name_config.get('name'), 'world')

        # test that config value is retained
        cpu_config = ConfigFactory.parse_string('nrOfCpus = 0.1')
        bndl_utils.load_bundle_args_into_conf(cpu_config, base_args)
        self.assertEqual(cpu_config.get('nrOfCpus'), 0.1)

        config = ConfigFactory.parse_string('')
        bndl_utils.load_bundle_args_into_conf(config, extended_args)

        # test that various args are set correctly
        self.assertEqual(config.get('name'), 'world')
        self.assertEqual(config.get('version'), '4')
        self.assertEqual(config.get('compatibilityVersion'), '5')
        self.assertEqual(config.get('system'), 'myapp')
        self.assertEqual(config.get('systemVersion'), '3')
        self.assertEqual(config.get('nrOfCpus'), '8')
        self.assertEqual(config.get('memory'), '65536')
        self.assertEqual(config.get('diskSpace'), '16384')
        self.assertEqual(config.get('roles'), ['web', 'backend'])
        self.assertEqual(
            bndl_oci.oci_image_bundle_conf(base_args, 'my-component'),
            strip_margin('''|name = "world"
                            |roles = []
                            |components {
                            |  my-component {
                            |    description = "testing desc 1"
                            |    file-system-type = "oci-image"
                            |    start-command = [
                            |      "ociImageTag"
                            |      "testing"
                            |    ]
                            |    endpoints {}
                            |  }
                            |}''')
        )

        self.assertEqual(
            bndl_oci.oci_image_bundle_conf(extended_args, 'my-other-component'),
            strip_margin('''|name = "world"
                            |version = "4"
                            |compatibilityVersion = "5"
                            |system = "myapp"
                            |systemVersion = "3"
                            |nrOfCpus = "8"
                            |memory = "65536"
                            |diskSpace = "16384"
                            |roles = [
                            |  "web"
                            |  "backend"
                            |]
                            |components {
                            |  my-other-component {
                            |    description = "testing desc 2"
                            |    file-system-type = "oci-image"
                            |    start-command = [
                            |      "ociImageTag"
                            |      "latest"
                            |    ]
                            |    endpoints {}
                            |  }
                            |}''')
        )
