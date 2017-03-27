from conductr_cli import bndl_docker
from conductr_cli.test.cli_test_case import CliTestCase
from io import BytesIO
import json
import os
import shutil
import tarfile
import tempfile


class TestBndlDocker(CliTestCase):
    def test_docker_parse_cmd(self):
        self.assertEqual(
            bndl_docker.docker_parse_cmd('CMD /bin/bash test.sh'),
            ['/bin/bash', 'test.sh']
        )

        self.assertEqual(
            bndl_docker.docker_parse_cmd('CMD [/bin/bash test.sh]'),
            ['/bin/bash', 'test.sh']
        )

        self.assertEqual(
            bndl_docker.docker_parse_cmd('CMD ["hello", "world"]'),
            ['hello', 'world']
        )

        self.assertEqual(
            bndl_docker.docker_parse_cmd('CMD ["hello world"]'),
            ['hello world']
        )

        self.assertEqual(
            bndl_docker.docker_parse_cmd('CMD hello\\ world'),
            ['hello world']
        )

        self.assertEqual(
            bndl_docker.docker_parse_cmd('CMD ["quoted" "no" "commas"]'),
            ['quoted', 'no', 'commas']
        )

        self.assertEqual(
            bndl_docker.docker_parse_cmd('CMD ["escaped \\"quote\\""]'),
            ['escaped "quote"']
        )

        self.assertEqual(
            bndl_docker.docker_parse_cmd('CMD ["weird"quotes""]'),
            ['weird', 'quotes', '']
        )

        self.assertEqual(
            bndl_docker.docker_parse_cmd('CMD [hello, "mismatched quote add anyways]'),
            ['hello', 'mismatched quote add anyways']
        )

    def test_docker_parse_image_name(self):
        self.assertEqual(bndl_docker.docker_parse_image_name('alpine:latest'), ('alpine', 'latest'))
        self.assertEqual(bndl_docker.docker_parse_image_name('lightbend/conductr:2'), ('conductr', '2'))

        with self.assertRaises(ValueError):
            bndl_docker.docker_parse_image_name('alpine')

    def test_docker_tag_matches(self):
        self.assertTrue(bndl_docker.docker_image_name_matches('conductr', None, 'conductr:latest'))
        self.assertFalse(bndl_docker.docker_image_name_matches('sherpa', None, 'conductr:latest'))
        self.assertTrue(bndl_docker.docker_image_name_matches('conductr', None, 'lightbend/conductr:latest'))
        self.assertFalse(bndl_docker.docker_image_name_matches('conductr', None, 'lightbend/sherpa:latest'))
        self.assertTrue(bndl_docker.docker_image_name_matches('conductr', 'latest', 'conductr:latest'))
        self.assertTrue(bndl_docker.docker_image_name_matches('conductr', 'latest', 'lightbend/conductr:latest'))
        self.assertFalse(bndl_docker.docker_image_name_matches('conductr', 'oldest', 'conductr:latest'))
        self.assertFalse(bndl_docker.docker_image_name_matches('conductr', 'oldest', 'lightbend/conductr:latest'))
        self.assertFalse(bndl_docker.docker_image_name_matches('conductr', 'latest', 'conductr:oldest'))
        self.assertFalse(bndl_docker.docker_image_name_matches('conductr', 'latest', 'lightbend/conductr:oldest'))

    def test_docker_config_to_oci_image(self):
        data = bndl_docker.docker_config_to_oci_image(
            manifest={
                'Config': '4a415e3663882fbc554ee830889c68a33b3585503892cc718a4698e91ef2a526.json',
                'RepoTags': ['alpine:latest'],
                'Layers': [
                    '693bdf455e7bf0952f8a4539f9f96aa70c489ca239a7dbed0afb481c87cbe131/layer.tar'
                ]
            },
            config={
                'created': '2017-01-13T22:50:56.415736637Z',
                'os': 'linux',
                'architecture': 'amd64',
                'history': [{'created': '2017-01-13T22:50:55.903893599Z', 'created_by': '/bin/sh'}],
                'rootfs': {
                    'type': 'layers',
                    'diff_ids': [
                        'sha256:98c944e98de8d35097100ff70a31083ec57704be0991a92c51700465e4544d08'
                    ]
                },
                'config': {
                    'Env': ['TEST=123'],
                    'Cmd': ['/bin']
                }
            },
            sizes={'some digest': 1234},
            layers_to_digests={
                '693bdf455e7bf0952f8a4539f9f96aa70c489ca239a7dbed0afb481c87cbe131/layer.tar': 'some digest'
            },
            docker_cmd=None,
            docker_entrypoint=None,
            docker_env=None
        )

        self.assertEqual(json.loads(data['config'].decode('UTF-8')), {
            'rootfs': {
                'type': 'layers',
                'diff_ids': ['sha256:98c944e98de8d35097100ff70a31083ec57704be0991a92c51700465e4544d08']
            },
            'created': '2017-01-13T22:50:56.415736637Z',
            'history': [{'created': '2017-01-13T22:50:55.903893599Z', 'created_by': '/bin/sh'}],
            'config': {
                'Cmd': ['/bin'],
                'Env': ['TEST=123']
            },
            'os': 'linux',
            'architecture': 'amd64'
        })

        self.assertEqual(json.loads(data['manifest'].decode('UTF-8')), {
            'layers': [{
                'digest': 'sha256:some digest',
                'size': 1234,
                'mediaType': 'application/vnd.oci.image.layer.v1.tar+gzip'
            }],
            'config': {
                'digest': 'sha256:d1cbc4434ff3dc404a0fe22c7c2d232edb3bf39ced50952144924570878ea043',
                'size': 339,
                'mediaType': 'application/vnd.oci.image.config.v1+json'
            },
            'schemaVersion': 2
        })

        self.assertEqual(json.loads(data['refs'].decode('UTF-8')), {
            'digest': 'sha256:9dadab903288242e1732b4a4f038d5a9ce57c1e0a9e1398093e7ba1ddd13357d',
            'mediaType': 'application/vnd.oci.image.manifest.v1+json',
            'size': 307
        })

    def test_docker_config_to_oci_image_overrides(self):
        data = bndl_docker.docker_config_to_oci_image(
            manifest={
                'Config': '4a415e3663882fbc554ee830889c68a33b3585503892cc718a4698e91ef2a526.json',
                'RepoTags': ['alpine:latest'],
                'Layers': [
                    '693bdf455e7bf0952f8a4539f9f96aa70c489ca239a7dbed0afb481c87cbe131/layer.tar'
                ]
            },
            config={
                'created': '2017-01-13T22:50:56.415736637Z',
                'os': 'linux',
                'architecture': 'amd64',
                'history': [{'created': '2017-01-13T22:50:55.903893599Z', 'created_by': '/bin/sh'}],
                'rootfs': {
                    'type': 'layers',
                    'diff_ids': [
                        'sha256:98c944e98de8d35097100ff70a31083ec57704be0991a92c51700465e4544d08'
                    ]
                },
                'config': {
                    'Env': ['TEST=123'],
                    'Cmd': ['/bin']
                }
            },
            sizes={'some digest': 1234},
            layers_to_digests={
                '693bdf455e7bf0952f8a4539f9f96aa70c489ca239a7dbed0afb481c87cbe131/layer.tar': 'some digest'
            },
            docker_cmd=['/bin/sh', 'testing'],
            docker_entrypoint=['/bin/bash', 'testing'],
            docker_env=['ENV=/bin']
        )

        self.assertEqual(json.loads(data['config'].decode('UTF-8')), {
            'rootfs': {
                'type': 'layers',
                'diff_ids': ['sha256:98c944e98de8d35097100ff70a31083ec57704be0991a92c51700465e4544d08']
            },
            'created': '2017-01-13T22:50:56.415736637Z',
            'history': [{'created': '2017-01-13T22:50:55.903893599Z', 'created_by': '/bin/sh'}],
            'config': {
                'Cmd': ['/bin/sh', 'testing'],
                'Env': ['ENV=/bin'],
                'Entrypoint': ['/bin/bash', 'testing']
            },
            'os': 'linux',
            'architecture': 'amd64'
        })

        self.assertEqual(json.loads(data['manifest'].decode('UTF-8')), {
            'layers': [{
                'digest': 'sha256:some digest',
                'size': 1234,
                'mediaType': 'application/vnd.oci.image.layer.v1.tar+gzip'
            }],
            'config': {
                'digest': 'sha256:f6e13c6d7b63f73e7c9cf10b2b93374690eec8e151622f066d6d92a9b77eb7b2',
                'size': 393,
                'mediaType': 'application/vnd.oci.image.config.v1+json'
            },
            'schemaVersion': 2
        })

        self.assertEqual(json.loads(data['refs'].decode('UTF-8')), {
            'digest': 'sha256:81107b157193a030f625a9db8dbe2ac6e1826ac0218db4e3df26c83a4912b795',
            'mediaType': 'application/vnd.oci.image.manifest.v1+json',
            'size': 307
        })

    def test_docker_unpack_tar_wrong_format(self):
        file = tempfile.NamedTemporaryFile()
        dest_tmpdir = tempfile.mkdtemp()

        try:
            with tarfile.open(fileobj=file, mode='w') as tar:
                tar.addfile(tarfile.TarInfo('testing'), BytesIO(b'hello'))

            file.seek(0)

            with tarfile.open(fileobj=file, mode='r') as tar:
                self.assertIsNone(
                    bndl_docker.docker_unpack(
                        dest_tmpdir,
                        tar,
                        False,
                        None,
                        None,
                        None,
                        None,
                        None
                    )
                )
        finally:
            shutil.rmtree(dest_tmpdir)

    def test_docker_unpack_dir_wrong_format(self):
        tmpdir = tempfile.mkdtemp()
        dest_tmpdir = tempfile.mkdtemp()

        try:
            with open(os.path.join(tmpdir, 'testing'), 'wb') as file:
                file.write('hello'.encode('UTF-8'))

            self.assertFalse(
                bndl_docker.docker_unpack(
                    dest_tmpdir,
                    tmpdir,
                    True,
                    None,
                    None,
                    None,
                    None,
                    None
                )
            )
        finally:
            shutil.rmtree(tmpdir)
            shutil.rmtree(dest_tmpdir)
