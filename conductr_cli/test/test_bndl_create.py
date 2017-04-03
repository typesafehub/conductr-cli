from conductr_cli import bndl_create, logging_setup
from conductr_cli.test.cli_test_case import CliTestCase, create_attributes_object, as_error
from io import BytesIO
from unittest.mock import patch, MagicMock
import os
import shutil
import tempfile
import zipfile


class TestBndlCreate(CliTestCase):
    def test_no_format(self):
        attributes = create_attributes_object({
            'source': None,
            'format': None,
            'tag': 'latest',
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
                'tag': 'latest',
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

        with tempfile.NamedTemporaryFile() as output:
            attributes = create_attributes_object({
                'name': 'test',
                'source': tmpdir,
                'format': 'oci-image',
                'tag': 'latest',
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

    def test_with_shazar(self):
        stdout_mock = MagicMock()
        tmpdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tmpdir, 'output')

        try:
            attributes = create_attributes_object({
                'name': 'test',
                'source': tmpdir,
                'format': 'oci-image',
                'tag': 'latest',
                'output': tmpfile,
                'component_description': '',
                'use_shazar': True,
                'use_default_endpoints': True,
                'annotations': []
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
        finally:
            shutil.rmtree(tmpdir)

    def test_without_shazar(self):
        stdout_mock = MagicMock()
        extract_config_mock = MagicMock()
        tmpdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tmpdir, 'output')

        try:
            attributes = create_attributes_object({
                'name': 'test',
                'source': tmpdir,
                'format': 'oci-image',
                'tag': 'latest',
                'output': tmpfile,
                'component_description': '',
                'use_shazar': False,
                'use_default_endpoints': True,
                'annotations': []
            })

            os.mkdir(os.path.join(tmpdir, 'refs'))
            open(os.path.join(tmpdir, 'oci-layout'), 'w').close()
            refs = open(os.path.join(tmpdir, 'refs/latest'), 'w')
            refs.write('{}')
            refs.close()

            with \
                    patch('conductr_cli.bndl_oci.oci_image_extract_manifest_config', extract_config_mock), \
                    patch('sys.stdin', MagicMock(**{'buffer': BytesIO(b'')})), \
                    patch('sys.stdout.buffer.write', stdout_mock):
                self.assertEqual(bndl_create.bndl_create(attributes), 0)

            self.assertFalse(zipfile.is_zipfile(tmpfile))
        finally:
            shutil.rmtree(tmpdir)
