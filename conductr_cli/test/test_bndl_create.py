from conductr_cli import bndl_create, logging_setup
from conductr_cli.test.cli_test_case import CliTestCase, create_attributes_object, as_error, strip_margin
from conductr_cli.bndl_utils import ApplicationType, BndlFormat
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
                'format': BndlFormat.OCI_IMAGE,
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
                    'format': BndlFormat.OCI_IMAGE,
                    'image_tag': 'latest',
                    'output': output.name,
                    'with_defaults': None
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
                'format': BndlFormat.OCI_IMAGE,
                'image_tag': 'latest',
                'output': tmpfile,
                'use_shazar': True,
                'use_default_endpoints': True,
                'annotations': [],
                'validation_excludes': [],
                'use_default_volumes': True,
                'with_defaults': None
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
                'format': BndlFormat.OCI_IMAGE,
                'image_tag': 'latest',
                'output': tmpfile,
                'use_shazar': False,
                'use_default_endpoints': True,
                'annotations': [],
                'validation_excludes': [],
                'use_default_volumes': True,
                'with_defaults': None
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
                'format': BndlFormat.OCI_IMAGE,
                'image_tag': 'latest',
                'output': tmpfile,
                'use_shazar': True,
                'use_default_endpoints': True,
                'annotations': [],
                'validation_excludes': [],
                'use_default_volumes': True,
                'with_defaults': None
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
                'format': BndlFormat.OCI_IMAGE,
                'image_tag': 'latest',
                'output': tmpfile2,
                'use_shazar': True,
                'use_default_endpoints': True,
                'annotations': [],
                'validation_excludes': [],
                'use_default_volumes': True,
                'with_defaults': None
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
                'format': BndlFormat.OCI_IMAGE,
                'image_tag': 'latest',
                'output': tmpfile,
                'use_shazar': True,
                'use_default_endpoints': True,
                'annotations': [],
                'validation_excludes': [],
                'use_default_volumes': True,
                'with_defaults': None
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
                'format': BndlFormat.OCI_IMAGE,
                'image_tag': 'latest',
                'output': tmpfile,
                'use_shazar': False,
                'use_default_endpoints': True,
                'annotations': [],
                'validation_excludes': [],
                'use_default_volumes': True,
                'with_defaults': None
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
                'format': BndlFormat.OCI_IMAGE,
                'image_tag': 'latest',
                'output': tmpfile2,
                'use_shazar': False,
                'use_default_endpoints': True,
                'annotations': [],
                'validation_excludes': [],
                'use_default_volumes': True,
                'with_defaults': None
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

    def test_validation_excludes(self):
        temp_dir = tempfile.mkdtemp()
        bundle_conf = 'invalid-name = "1"\nversion=""'

        try:
            with \
                    open(os.path.join(temp_dir, 'bundle.conf'), 'wb') as bundle_conf_file, \
                    tempfile.NamedTemporaryFile() as file_out:

                bundle_conf_file.write(bundle_conf.encode('UTF-8'))
                bundle_conf_file.flush()

                args = create_attributes_object({
                    'name': 'test',
                    'format': BndlFormat.BUNDLE,
                    'source': temp_dir,
                    'output': file_out.name,
                    'use_shazar': False,
                    'use_default_endpoints': False,
                    'validation_excludes': ['empty-property', 'required', 'property-name'],
                    'with_defaults': None
                })

                self.assertEqual(bndl_create.bndl_create(args), 0)
                self.assertTrue(tarfile.is_tarfile(file_out.name))

                with tarfile.open(file_out.name, 'r') as tar:
                    for entry in tar:
                        self.assertEqual('test/bundle.conf', entry.name)
                        self.assertEqual(
                            tar.extractfile(entry).read().decode('UTF-8'),
                            'invalid-name = "1"\nversion = ""\nname = "test"'
                        )
        finally:
            shutil.rmtree(temp_dir)

    def test_no_input_configuration(self):
        with tempfile.NamedTemporaryFile() as file_out:
            args = create_attributes_object({
                'name': 'test',
                'format': BndlFormat.CONFIGURATION,
                'source': None,
                'output': file_out.name,
                'use_shazar': False,
                'use_default_endpoints': False,
                'roles': ['test'],
                'validation_excludes': [],
                'with_defaults': None
            })

            self.assertEqual(bndl_create.bndl_create(args), 0)
            self.assertTrue(tarfile.is_tarfile(file_out.name))

            # check that config bundle is named properly and contains arguments

            with tarfile.open(file_out.name, 'r') as tar:
                for entry in tar:
                    self.assertEqual('test/bundle.conf', entry.name)
                    self.assertEqual(
                        tar.extractfile(entry).read().decode('UTF-8'),
                        strip_margin(
                            '''|name = "test"
                               |roles = [
                               |  "test"
                               |]''')
                    )

    def test_no_input_bundle(self):
        with tempfile.NamedTemporaryFile() as file_out:
            args = create_attributes_object({
                'endpoints': [],
                'name': 'test',
                'format': BndlFormat.BUNDLE,
                'source': None,
                'start_commands': [
                    create_attributes_object({
                        'start_command': '["bin/start"]'
                    })
                ],
                'output': file_out.name,
                'use_shazar': False,
                'use_default_endpoints': False,
                'roles': ['test'],
                'validation_excludes': [],
                'with_defaults': ApplicationType.GENERIC
            })

            self.assertEqual(bndl_create.bndl_create(args), 0)
            self.assertTrue(tarfile.is_tarfile(file_out.name))

            # check that config bundle is named properly and contains arguments

            with tarfile.open(file_out.name, 'r') as tar:
                for entry in tar:
                    self.assertEqual('test/bundle.conf', entry.name)
                    self.assertEqual(
                        tar.extractfile(entry).read().decode('UTF-8'),
                        strip_margin(
                            '''|annotations {}
                               |compatibilityVersion = "0"
                               |components {
                               |  test {
                               |    endpoints {}
                               |    start-command = [
                               |      "bin/start"
                               |    ]
                               |    description = ""
                               |    file-system-type = "universal"
                               |  }
                               |}
                               |diskSpace = 1073741824
                               |memory = 402653184
                               |name = "test"
                               |nrOfCpus = 0.1
                               |roles = [
                               |  "test"
                               |]
                               |system = "test"
                               |systemVersion = "0"
                               |tags = [
                               |  "0.0.1"
                               |]
                               |version = "1"''')
                    )

    def test_bundle_conf(self):
        with tempfile.NamedTemporaryFile() as file_in, tempfile.NamedTemporaryFile() as file_out:
            file_in.write(b'name = "testing"\n'
                          b'roles = ["web", "web2"]\n'
                          b'components {'
                          b'  "test1" {'
                          b'    start-command = []'
                          b'  }'
                          b'  "test2": {'
                          b'    start-command = []'
                          b'  }'
                          b'}')
            file_in.flush()

            args = create_attributes_object({
                'name': 'test',
                'format': BndlFormat.CONFIGURATION,
                'source': file_in.name,
                'output': file_out.name,
                'use_shazar': False,
                'use_default_endpoints': True,
                'use_default_volumes': True,
                'roles': ['test'],
                'start_commands': [
                    create_attributes_object({
                        'start_command': '["abc", "test"]',
                        'component': 'test2'
                    }),
                    create_attributes_object({
                        'start_command': '["xyz", "test"]',
                        'component': 'test1'
                    })
                ],
                'validation_excludes': [],
                'volumes': [
                    create_attributes_object({
                        'name': 'my-vol',
                        'mount_point': '/data',
                        'component': 'test2'
                    }),
                    create_attributes_object({
                        'name': 'my-vol',
                        'mount_point': '/other-data',
                        'component': 'test1'
                    }),
                    create_attributes_object({
                        'name': 'my-vol2',
                        'mount_point': '/data',
                        'component': 'test1'
                    })
                ],
                'descriptions': [
                    create_attributes_object({
                        'description': 'this is a test',
                        'component': 'test2'
                    })
                ],
                'with_defaults': None
            })

            self.assertEqual(bndl_create.bndl_create(args), 0)
            self.assertTrue(tarfile.is_tarfile(file_out.name))

            # check that config bundle is named properly and is ignoring arguments

            with tarfile.open(file_out.name, 'r') as tar:
                for entry in tar:
                    self.assertEqual('test/bundle.conf', entry.name)
                    self.assertEqual(
                        tar.extractfile(entry).read().decode('UTF-8'),
                        strip_margin(
                            '''|name = "test"
                               |roles = [
                               |  "test"
                               |]
                               |components {
                               |  test1 {
                               |    start-command = [
                               |      "xyz"
                               |      "test"
                               |    ]
                               |    volumes {
                               |      my-vol = "/other-data"
                               |      my-vol2 = "/data"
                               |    }
                               |  }
                               |  test2 {
                               |    start-command = [
                               |      "abc"
                               |      "test"
                               |    ]
                               |    description = "this is a test"
                               |    volumes {
                               |      my-vol = "/data"
                               |    }
                               |  }
                               |}''')
                    )

    def test_bundle_configuration_arg_no_name(self):
        with tempfile.NamedTemporaryFile() as file_in, tempfile.NamedTemporaryFile() as file_out:
            file_in.write(b'name = "test"\nroles = ["web", "web2"]')
            file_in.flush()

            args = create_attributes_object({
                'name': None,
                'format': BndlFormat.CONFIGURATION,
                'source': file_in.name,
                'output': file_out.name,
                'use_shazar': False,
                'use_default_endpoints': True,
                'validation_excludes': [],
                'with_defaults': None
            })

            self.assertEqual(bndl_create.bndl_create(args), 0)
            self.assertTrue(tarfile.is_tarfile(file_out.name))

            with tarfile.open(file_out.name, 'r') as tar:
                for entry in tar:
                    self.assertEqual('test/bundle.conf', entry.name)
                    self.assertEqual(
                        tar.extractfile(entry).read().decode('UTF-8'),
                        strip_margin(
                            '''|name = "test"
                               |roles = [
                               |  "web"
                               |  "web2"
                               |]''')
                    )

    def test_bundle_conf_no_name(self):
        with tempfile.NamedTemporaryFile() as file_in, tempfile.NamedTemporaryFile() as file_out:
            file_in.write(b'version = "1"\nroles = ["web", "web2"]')
            file_in.flush()

            args = create_attributes_object({
                'name': None,
                'format': BndlFormat.CONFIGURATION,
                'source': file_in.name,
                'output': file_out.name,
                'use_shazar': False,
                'use_default_endpoints': True,
                'validation_excludes': [],
                'with_defaults': None
            })

            self.assertEqual(bndl_create.bndl_create(args), 0)
            self.assertTrue(tarfile.is_tarfile(file_out.name))

            with tarfile.open(file_out.name, 'r') as tar:
                for entry in tar:
                    self.assertEqual('bundle/bundle.conf', entry.name)
                    self.assertEqual(
                        tar.extractfile(entry).read().decode('UTF-8'),
                        strip_margin(
                            '''|version = "1"
                               |roles = [
                               |  "web"
                               |  "web2"
                               |]''')
                    )

    def test_bundle(self):
        temp_dir = tempfile.mkdtemp()
        bundle_conf = strip_margin(
            """|version = "1"
               |name = "testing"
               |compatibilityVersion = "1"
               |system = "my-system"
               |systemVersion = "1"
               |nrOfCpus = 1.0
               |memory = 402653184
               |diskSpace = 200000000
               |roles = ["web", "web2"]
               |annotations = {},
               |tags = ["1.0.0"]
               |components {
               |  test-bundle {
               |    description = "test-bundle"
               |    file-system-type = "universal"
               |    start-command = [
               |      "test-bundle/bin/test-bundle"
               |    ]
               |    endpoints {
               |      test {
               |        bind-protocol = "tcp"
               |        bind-port = 0
               |        acls = "some-acl"
               |      }
               |    }
               |  }
               |}""")

        try:
            with \
                    open(os.path.join(temp_dir, 'bundle.conf'), 'wb') as bundle_conf_file, \
                    tempfile.NamedTemporaryFile() as file_out:

                bundle_conf_file.write(bundle_conf.encode('UTF-8'))
                bundle_conf_file.flush()

                args = create_attributes_object({
                    'name': 'test',
                    'format': BndlFormat.BUNDLE,
                    'source': temp_dir,
                    'output': file_out.name,
                    'use_shazar': False,
                    'use_default_endpoints': True,
                    'roles': ['test'],
                    'annotations': [
                        'my.test=testing'
                    ],
                    'validation_excludes': [],
                    'with_defaults': None
                })

                self.assertEqual(bndl_create.bndl_create(args), 0)
                self.assertTrue(tarfile.is_tarfile(file_out.name))

                with tarfile.open(file_out.name, 'r') as tar:
                    for entry in tar:
                        self.assertEqual('test/bundle.conf', entry.name)
                        self.assertEqual(
                            tar.extractfile(entry).read().decode('UTF-8'),
                            strip_margin(
                                """|version = "1"
                                   |name = "test"
                                   |compatibilityVersion = "1"
                                   |system = "my-system"
                                   |systemVersion = "1"
                                   |nrOfCpus = 1.0
                                   |memory = 402653184
                                   |diskSpace = 200000000
                                   |roles = [
                                   |  "test"
                                   |]
                                   |annotations {
                                   |  my {
                                   |    test = "testing"
                                   |  }
                                   |}
                                   |tags = [
                                   |  "1.0.0"
                                   |]
                                   |components {
                                   |  test-bundle {
                                   |    description = "test-bundle"
                                   |    file-system-type = "universal"
                                   |    start-command = [
                                   |      "test-bundle/bin/test-bundle"
                                   |    ]
                                   |    endpoints {
                                   |      test {
                                   |        bind-protocol = "tcp"
                                   |        bind-port = 0
                                   |        acls = "some-acl"
                                   |      }
                                   |    }
                                   |  }
                                   |}""")
                        )
        finally:
            shutil.rmtree(temp_dir)

    def test_bundle_conf_dir(self):
        temp_dir = tempfile.mkdtemp()

        try:
            with \
                    open(os.path.join(temp_dir, 'bundle.conf'), 'wb') as bundle_conf_file, \
                    tempfile.NamedTemporaryFile() as file_out:
                bundle_conf_file.write(b'name = "testing"\nroles = ["web", "web2"]')
                bundle_conf_file.flush()

                args = create_attributes_object({
                    'name': 'test',
                    'format': BndlFormat.CONFIGURATION,
                    'source': temp_dir,
                    'output': file_out.name,
                    'use_shazar': False,
                    'use_default_endpoints': True,
                    'annotations': [
                        'my.test=testing'
                    ],
                    'validation_excludes': [],
                    'with_defaults': None
                })

                self.assertEqual(bndl_create.bndl_create(args), 0)
                self.assertTrue(tarfile.is_tarfile(file_out.name))

                # config bundles shouldn't have any defaults added

                with tarfile.open(file_out.name, 'r') as tar:
                    for entry in tar:
                        self.assertEqual('test/bundle.conf', entry.name)
                        self.assertEqual(
                            tar.extractfile(entry).read().decode('UTF-8'),
                            strip_margin(
                                '''|name = "test"
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

    def test_bundle_envs(self):
        temp_dir = tempfile.mkdtemp()

        try:
            with tempfile.NamedTemporaryFile() as file_out:
                args = create_attributes_object({
                    'name': None,
                    'format': BndlFormat.BUNDLE,
                    'source': temp_dir,
                    'output': file_out.name,
                    'use_shazar': False,
                    'envs': [
                        'ENV1=123',
                        'ENV2=456',
                        'ENV3=$BUNDLE_HOST_IP',
                        'ENV4=`escapes properly`'
                    ],
                    'with_defaults': None
                })

                self.assertEqual(bndl_create.bndl_create(args), 0)
                self.assertTrue(tarfile.is_tarfile(file_out.name))

                with tarfile.open(file_out.name, 'r') as tar:
                    saw_bundle = False
                    saw_config = False

                    for entry in tar:
                        if entry.name == 'bundle/bundle.conf':
                            saw_bundle = True
                            self.assertEqual(tar.extractfile(entry).read().decode('UTF-8'), '{}')

                        elif entry.name == 'bundle/runtime-config.sh':
                            saw_config = True
                            self.assertEqual(
                                tar.extractfile(entry).read().decode('UTF-8'),
                                strip_margin(
                                    '''|export "ENV1=123"
                                       |export "ENV2=456"
                                       |export "ENV3=$BUNDLE_HOST_IP"
                                       |export "ENV4=\\`escapes properly\\`"''')
                            )

                    self.assertTrue(saw_bundle)
                    self.assertTrue(saw_config)
        finally:
            shutil.rmtree(temp_dir)

    def test_bundle_envs_append(self):
        temp_dir = tempfile.mkdtemp()

        try:
            with tempfile.NamedTemporaryFile() as file_out:
                args = create_attributes_object({
                    'name': None,
                    'format': BndlFormat.BUNDLE,
                    'source': temp_dir,
                    'output': file_out.name,
                    'use_shazar': False,
                    'envs': [
                        'ENV1=123',
                        'ENV2=456'
                    ],
                    'with_defaults': None
                })

                with open(os.path.join(temp_dir, 'runtime-config.sh'), 'w') as config:
                    config.write(
                        strip_margin(
                            '''|export MY_ENV=hello'''
                        )
                    )

                self.assertEqual(bndl_create.bndl_create(args), 0)
                self.assertTrue(tarfile.is_tarfile(file_out.name))

                with tarfile.open(file_out.name, 'r') as tar:
                    saw_bundle = False
                    saw_config = False

                    for entry in tar:
                        if entry.name == 'bundle/bundle.conf':
                            saw_bundle = True
                            self.assertEqual(tar.extractfile(entry).read().decode('UTF-8'), '{}')

                        elif entry.name == 'bundle/runtime-config.sh':
                            saw_config = True
                            self.assertEqual(
                                tar.extractfile(entry).read().decode('UTF-8'),
                                strip_margin(
                                    '''|export MY_ENV=hello
                                       |export "ENV1=123"
                                       |export "ENV2=456"''')
                            )

                    self.assertTrue(saw_bundle)
                    self.assertTrue(saw_config)
        finally:
            shutil.rmtree(temp_dir)

    def test_oci_env(self):
        stdout_mock = MagicMock()
        tmpdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tmpdir, 'output')

        try:
            attributes = create_attributes_object({
                'name': 'test',
                'source': tmpdir,
                'format': BndlFormat.OCI_IMAGE,
                'image_tag': 'latest',
                'output': tmpfile,
                'use_shazar': True,
                'use_default_endpoints': True,
                'use_default_volumes': True,
                'annotations': [],
                'envs': [
                    'ENV1=123',
                    'ENV2=456'
                ],
                'validation_excludes': [],
                'with_defaults': None
            })

            os.mkdir(os.path.join(tmpdir, 'refs'))
            open(os.path.join(tmpdir, 'oci-layout'), 'w').close()
            refs = open(os.path.join(tmpdir, 'refs/latest'), 'w')
            refs.write('{}')
            refs.close()

            with \
                    patch('sys.stdin', MagicMock(**{'buffer': BytesIO(b'')})), \
                    patch('sys.stdout.buffer.write', stdout_mock):
                self.assertEqual(bndl_create.bndl_create(attributes), 0)

            self.assertTrue(zipfile.is_zipfile(tmpfile))

            files = {}

            with zipfile.ZipFile(tmpfile) as zip:
                infos = zip.infolist()
                for info in infos:
                    files[info.filename] = zip.read(info.filename)

            self.assertEqual(
                files['test/runtime-config.sh'],
                b'export "ENV1=123"\nexport "ENV2=456"'
            )
        finally:
            shutil.rmtree(tmpdir)
