from conductr_cli import bndl_create, logging_setup
from conductr_cli.test.cli_test_case import CliTestCase, create_attributes_object, as_error, strip_margin
from io import BytesIO
from unittest.mock import patch, MagicMock
import os
import shutil
import tarfile
import tempfile
import time
import zipfile


class TestBndlCreate(CliTestCase):
    def test_no_format(self):
        attributes = create_attributes_object({
            'name': 'test',
            'source': None,
            'format': None,
            'image_tag': 'latest',
            'output': None
        })

        stdout_mock = MagicMock()
        stderr_mock = MagicMock()
        logging_setup.configure_logging(MagicMock(), stdout_mock, stderr_mock)

        with \
                patch('sys.stdin', MagicMock(**{'buffer': BytesIO(b'')})), \
                patch('sys.stdout.buffer.write', stdout_mock):
            bndl_create.bndl_create(attributes)

        self.assertEqual(
            self.output(stderr_mock),
            as_error('Error: bndl: Unable to detect format. Provide a -f or --format argument\n')
        )

    def test_not_oci(self):
        tmpdir = tempfile.mkdtemp()

        with tempfile.NamedTemporaryFile() as output:
            attributes = create_attributes_object({
                'name': 'test',
                'source': tmpdir,
                'format': 'oci-image',
                'image_tag': 'latest',
                'output': output.name
            })

        stdout_mock = MagicMock()
        stderr_mock = MagicMock()
        logging_setup.configure_logging(MagicMock(), stdout_mock, stderr_mock)

        with \
                patch('sys.stdin', MagicMock(**{'buffer': BytesIO(b'')})), \
                patch('sys.stdout.buffer.write', stdout_mock):
            bndl_create.bndl_create(attributes)

        self.assertEqual(
            self.output(stderr_mock),
            as_error('Error: bndl: Not an OCI Image\n')
        )

    def test_no_ref(self):
        tmpdir = tempfile.mkdtemp()

        try:
            with tempfile.NamedTemporaryFile() as output:
                attributes = create_attributes_object({
                    'name': 'test',
                    'source': tmpdir,
                    'format': 'oci-image',
                    'image_tag': 'latest',
                    'output': output.name
                })

            stdout_mock = MagicMock()
            stderr_mock = MagicMock()
            logging_setup.configure_logging(MagicMock(), stdout_mock, stderr_mock)

            os.mkdir(os.path.join(tmpdir, 'refs'))
            open(os.path.join(tmpdir, 'oci-layout'), 'w').close()

            with \
                    patch('sys.stdin', MagicMock(**{'buffer': BytesIO(b'')})), \
                    patch('sys.stdout.buffer.write', stdout_mock):
                bndl_create.bndl_create(attributes)

            self.assertEqual(
                self.output(stderr_mock),
                as_error('Error: bndl: Invalid OCI Image. Cannot find requested tag "latest" in OCI Image\n')
            )
        finally:
            shutil.rmtree(tmpdir)

    def test_with_shazar(self):
        stdout_mock = MagicMock()
        tmpdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tmpdir, 'output')

        try:
            attributes = create_attributes_object({
                'name': 'test',
                'source': tmpdir,
                'format': 'oci-image',
                'image_tag': 'latest',
                'output': tmpfile,
                'component_description': '',
                'use_shazar': True,
                'use_default_endpoints': True,
                'annotations': []
            })

            os.mkdir(os.path.join(tmpdir, 'refs'))
            open(os.path.join(tmpdir, 'oci-layout'), 'w').close()
            os.utime(os.path.join(tmpdir, 'oci-layout'), (1234567890, 1234567890))
            refs = open(os.path.join(tmpdir, 'refs/latest'), 'w')
            refs.write('{}')
            refs.close()
            os.utime(os.path.join(tmpdir, 'refs/latest'), (1234567890, 1234567890))

            with \
                    patch('sys.stdin', MagicMock(**{'buffer': BytesIO(b'')})), \
                    patch('sys.stdout.buffer.write', stdout_mock):
                self.assertEqual(bndl_create.bndl_create(attributes), 0)

            self.assertTrue(zipfile.is_zipfile(tmpfile))

            with zipfile.ZipFile(tmpfile) as zip:
                infos = zip.infolist()

                self.assertEqual(infos[0].date_time, time.localtime(1234567890)[:6])
        finally:
            shutil.rmtree(tmpdir)

    def test_without_shazar(self):
        stdout_mock = MagicMock()
        tmpdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tmpdir, 'output')

        try:
            attributes = create_attributes_object({
                'name': 'test',
                'source': tmpdir,
                'format': 'oci-image',
                'image_tag': 'latest',
                'output': tmpfile,
                'component_description': '',
                'use_shazar': False,
                'use_default_endpoints': True,
                'annotations': []
            })

            os.mkdir(os.path.join(tmpdir, 'refs'))
            open(os.path.join(tmpdir, 'oci-layout'), 'w').close()
            os.utime(os.path.join(tmpdir, 'oci-layout'), (1234567890, 1234567890))
            refs = open(os.path.join(tmpdir, 'refs/latest'), 'w')
            refs.write('{}')
            refs.close()
            os.utime(os.path.join(tmpdir, 'refs/latest'), (1234567890, 1234567890))

            with \
                    patch('conductr_cli.bndl_oci.oci_image_extract_manifest_config', lambda a, b: ({}, {})), \
                    patch('sys.stdin', MagicMock(**{'buffer': BytesIO(b'')})), \
                    patch('sys.stdout.buffer.write', stdout_mock):
                self.assertEqual(bndl_create.bndl_create(attributes), 0)

            self.assertFalse(zipfile.is_zipfile(tmpfile))

            with tarfile.TarFile.open(tmpfile) as tar:
                for entry in tar:
                    self.assertEqual(entry.mtime, 1234567890)
                    break
        finally:
            shutil.rmtree(tmpdir)

    def test_deterministic_with_shazar(self):
        stdout_mock = MagicMock()
        tmpdir = tempfile.mkdtemp()
        tmpdir2 = tempfile.mkdtemp()
        tmpfile = os.path.join(tmpdir, 'output')
        tmpfile2 = os.path.join(tmpdir2, 'output')

        try:
            attributes = create_attributes_object({
                'name': 'test',
                'source': tmpdir,
                'format': 'oci-image',
                'image_tag': 'latest',
                'output': tmpfile,
                'component_description': '',
                'use_shazar': True,
                'use_default_endpoints': True,
                'annotations': []
            })

            os.mkdir(os.path.join(tmpdir, 'refs'))
            open(os.path.join(tmpdir, 'oci-layout'), 'w').close()
            os.utime(os.path.join(tmpdir, 'oci-layout'), (1234567890, 1234567890))
            refs = open(os.path.join(tmpdir, 'refs/latest'), 'w')
            refs.write('{}')
            refs.close()
            os.utime(os.path.join(tmpdir, 'refs/latest'), (1234567890, 1234567890))

            attributes2 = create_attributes_object({
                'name': 'test',
                'source': tmpdir2,
                'format': 'oci-image',
                'image_tag': 'latest',
                'output': tmpfile2,
                'component_description': '',
                'use_shazar': True,
                'use_default_endpoints': True,
                'annotations': []
            })

            os.mkdir(os.path.join(tmpdir2, 'refs'))
            open(os.path.join(tmpdir2, 'oci-layout'), 'w').close()
            os.utime(os.path.join(tmpdir2, 'oci-layout'), (1234567890, 1234567890))
            refs2 = open(os.path.join(tmpdir2, 'refs/latest'), 'w')
            refs2.write('{}')
            refs2.close()
            os.utime(os.path.join(tmpdir2, 'refs/latest'), (1234567890, 1234567890))

            with \
                    patch('sys.stdin', MagicMock(**{'buffer': BytesIO(b'')})), \
                    patch('sys.stdout.buffer.write', stdout_mock):
                bndl_create.bndl_create(attributes)
                bndl_create.bndl_create(attributes2)

            with open(tmpfile, 'rb') as fileobj, open(tmpfile2, 'rb') as fileobj2:
                self.assertEqual(fileobj.read(), fileobj2.read())

        finally:
            shutil.rmtree(tmpdir)
            shutil.rmtree(tmpdir2)

    def test_mtime_from_config(self):
        config = {
            'created': '2017-02-27T19:42:10.522384312Z'
        }
        stdout_mock = MagicMock()
        tmpdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tmpdir, 'output')

        try:
            attributes = create_attributes_object({
                'name': 'test',
                'source': tmpdir,
                'format': 'oci-image',
                'image_tag': 'latest',
                'output': tmpfile,
                'component_description': '',
                'use_shazar': True,
                'use_default_endpoints': True,
                'annotations': []
            })

            os.mkdir(os.path.join(tmpdir, 'refs'))
            open(os.path.join(tmpdir, 'oci-layout'), 'w').close()
            os.utime(os.path.join(tmpdir, 'oci-layout'), (1234567890, 1234567890))
            refs = open(os.path.join(tmpdir, 'refs/latest'), 'w')
            refs.write('{}')
            refs.close()
            os.utime(os.path.join(tmpdir, 'refs/latest'), (1234567890, 1234567890))

            with \
                    patch('conductr_cli.bndl_oci.oci_image_extract_manifest_config', lambda a, b: ({}, config)), \
                    patch('sys.stdin', MagicMock(**{'buffer': BytesIO(b'')})), \
                    patch('sys.stdout.buffer.write', stdout_mock):
                self.assertEqual(bndl_create.bndl_create(attributes), 0)

            with zipfile.ZipFile(tmpfile) as zip:
                infos = zip.infolist()

                self.assertEqual(infos[0].date_time, time.localtime(1488224530)[:6])

        finally:
            shutil.rmtree(tmpdir)

    def test_deterministic_without_shazar(self):
        stdout_mock = MagicMock()
        tmpdir = tempfile.mkdtemp()
        tmpdir2 = tempfile.mkdtemp()
        tmpfile = os.path.join(tmpdir, 'output')
        tmpfile2 = os.path.join(tmpdir2, 'output')

        try:
            attributes = create_attributes_object({
                'name': 'test',
                'source': tmpdir,
                'format': 'oci-image',
                'image_tag': 'latest',
                'output': tmpfile,
                'component_description': '',
                'use_shazar': False,
                'use_default_endpoints': True,
                'annotations': []
            })

            os.mkdir(os.path.join(tmpdir, 'refs'))
            open(os.path.join(tmpdir, 'oci-layout'), 'w').close()
            os.utime(os.path.join(tmpdir, 'oci-layout'), (1234567890, 1234567890))
            refs = open(os.path.join(tmpdir, 'refs/latest'), 'w')
            refs.write('{}')
            refs.close()
            os.utime(os.path.join(tmpdir, 'refs/latest'), (1234567890, 1234567890))

            attributes2 = create_attributes_object({
                'name': 'test',
                'source': tmpdir2,
                'format': 'oci-image',
                'image_tag': 'latest',
                'output': tmpfile2,
                'component_description': '',
                'use_shazar': False,
                'use_default_endpoints': True,
                'annotations': []
            })

            os.mkdir(os.path.join(tmpdir2, 'refs'))
            open(os.path.join(tmpdir2, 'oci-layout'), 'w').close()
            os.utime(os.path.join(tmpdir2, 'oci-layout'), (1234567890, 1234567890))
            refs2 = open(os.path.join(tmpdir2, 'refs/latest'), 'w')
            refs2.write('{}')
            refs2.close()
            os.utime(os.path.join(tmpdir2, 'refs/latest'), (1234567890, 1234567890))

            with \
                    patch('sys.stdin', MagicMock(**{'buffer': BytesIO(b'')})), \
                    patch('sys.stdout.buffer.write', stdout_mock):
                self.assertEqual(bndl_create.bndl_create(attributes), 0)
                self.assertEqual(bndl_create.bndl_create(attributes2), 0)

            with open(tmpfile, 'rb') as fileobj, open(tmpfile2, 'rb') as fileobj2:
                self.assertEqual(fileobj.read(), fileobj2.read())

        finally:
            shutil.rmtree(tmpdir)
            shutil.rmtree(tmpdir2)

    def test_bundle_conf(self):
        with tempfile.NamedTemporaryFile() as file_in, tempfile.NamedTemporaryFile() as file_out:
            file_in.write(b'name = "testing"\ndescription = "my test description"\nroles = ["web", "web2"]')
            file_in.flush()

            args = create_attributes_object({
                'name': 'test',
                'format': None,
                'source': file_in.name,
                'output': file_out.name,
                'use_shazar': False,
                'use_default_endpoints': True,
                'roles': ['test']
            })

            self.assertEqual(bndl_create.bndl_create(args), 0)
            self.assertTrue(tarfile.is_tarfile(file_out.name))

            # check that config bundle is named properly and is ignoring arguments

            with tarfile.open(file_out.name, 'r') as tar:
                for entry in tar:
                    self.assertEqual('test/bundle.conf', entry.name)
                    self.assertEqual(
                        tar.extractfile(entry).read().decode("UTF-8"),
                        strip_margin(
                            '''|name = "test"
                               |description = "my test description"
                               |roles = [
                               |  "test"
                               |]''')
                    )

    def test_bundle_arg_no_name(self):
        with tempfile.NamedTemporaryFile() as file_in, tempfile.NamedTemporaryFile() as file_out:
            file_in.write(b'name = "test"\ndescription = "my test description"\nroles = ["web", "web2"]')
            file_in.flush()

            args = create_attributes_object({
                'name': None,
                'format': None,
                'source': file_in.name,
                'output': file_out.name,
                'use_shazar': False,
                'use_default_endpoints': True
            })

            self.assertEqual(bndl_create.bndl_create(args), 0)
            self.assertTrue(tarfile.is_tarfile(file_out.name))

            with tarfile.open(file_out.name, 'r') as tar:
                for entry in tar:
                    self.assertEqual('test/bundle.conf', entry.name)
                    self.assertEqual(
                        tar.extractfile(entry).read().decode("UTF-8"),
                        strip_margin(
                            '''|name = "test"
                               |description = "my test description"
                               |roles = [
                               |  "web"
                               |  "web2"
                               |]''')
                    )

    def test_bundle_conf_no_name(self):
        with tempfile.NamedTemporaryFile() as file_in, tempfile.NamedTemporaryFile() as file_out:
            file_in.write(b'description = "my test description"\nroles = ["web", "web2"]')
            file_in.flush()

            args = create_attributes_object({
                'name': None,
                'format': None,
                'source': file_in.name,
                'output': file_out.name,
                'use_shazar': False,
                'use_default_endpoints': True
            })

            self.assertEqual(bndl_create.bndl_create(args), 0)
            self.assertTrue(tarfile.is_tarfile(file_out.name))

            with tarfile.open(file_out.name, 'r') as tar:
                for entry in tar:
                    self.assertEqual('bundle/bundle.conf', entry.name)
                    self.assertEqual(
                        tar.extractfile(entry).read().decode("UTF-8"),
                        strip_margin(
                            '''|description = "my test description"
                               |roles = [
                               |  "web"
                               |  "web2"
                               |]''')
                    )

    def test_bundle(self):
        temp_dir = tempfile.mkdtemp()

        try:
            with \
                    open(os.path.join(temp_dir, 'bundle.conf'), 'wb') as bundle_conf_file, \
                    tempfile.NamedTemporaryFile() as file_out:
                bundle_conf_file.write(b'name = "testing"\ndescription = "my test description"\nroles = ["web", "web2"]')
                bundle_conf_file.flush()

                args = create_attributes_object({
                    'name': 'test',
                    'format': 'bundle',
                    'source': temp_dir,
                    'output': file_out.name,
                    'use_shazar': False,
                    'use_default_endpoints': True,
                    'roles': ['test'],
                    'annotations': [
                        'my.test=testing'
                    ]
                })

                self.assertEqual(bndl_create.bndl_create(args), 0)
                self.assertTrue(tarfile.is_tarfile(file_out.name))

                with tarfile.open(file_out.name, 'r') as tar:
                    for entry in tar:
                        self.assertEqual('test/bundle.conf', entry.name)
                        self.assertEqual(
                            tar.extractfile(entry).read().decode("UTF-8"),
                            strip_margin(
                                '''|name = "test"
                                   |description = "my test description"
                                   |roles = [
                                   |  "test"
                                   |]
                                   |annotations {
                                   |  my {
                                   |    test = "testing"
                                   |  }
                                   |}''')
                        )
        finally:
            shutil.rmtree(temp_dir)

    def test_bundle_conf_dir(self):
        temp_dir = tempfile.mkdtemp()

        try:
            with \
                    open(os.path.join(temp_dir, 'bundle.conf'), 'wb') as bundle_conf_file, \
                    tempfile.NamedTemporaryFile() as file_out:
                bundle_conf_file.write(b'name = "testing"\ndescription = "my test description"\nroles = ["web", "web2"]')
                bundle_conf_file.flush()

                args = create_attributes_object({
                    'name': 'test',
                    'format': 'bundle',
                    'source': temp_dir,
                    'output': file_out.name,
                    'use_shazar': False,
                    'use_default_endpoints': True,
                    'annotations': [
                        'my.test=testing'
                    ]
                })

                self.assertEqual(bndl_create.bndl_create(args), 0)
                self.assertTrue(tarfile.is_tarfile(file_out.name))

                # config bundles shouldn't have any defaults added

                with tarfile.open(file_out.name, 'r') as tar:
                    for entry in tar:
                        self.assertEqual('test/bundle.conf', entry.name)
                        self.assertEqual(
                            tar.extractfile(entry).read().decode("UTF-8"),
                            strip_margin(
                                '''|name = "test"
                                   |description = "my test description"
                                   |roles = [
                                   |  "web"
                                   |  "web2"
                                   |]
                                   |annotations {
                                   |  my {
                                   |    test = "testing"
                                   |  }
                                   |}''')
                        )
        finally:
            shutil.rmtree(temp_dir)
