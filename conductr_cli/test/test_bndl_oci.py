from conductr_cli import bndl_oci
from conductr_cli.test.cli_test_case import CliTestCase, create_attributes_object, strip_margin
from io import BytesIO
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

        self.assertEqual(
            bndl_oci.oci_image_bundle_conf(base_args, 'my-component'),
            strip_margin('''|name = "world"
                            |roles = []
                            |compatibilityVersion = 0
                            |diskSpace = 1073741824
                            |memory = 402653184
                            |nrOfCpus = 0.1
                            |system = "world"
                            |version = 1
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
