from conductr_cli import bndl_utils
from conductr_cli.test.cli_test_case import CliTestCase
from io import BytesIO
import os
import shutil
import tempfile


class TestBndlUtils(CliTestCase):
    def test_detect_format_stream(self):
        # empty stream is none
        self.assertEqual(
            bndl_utils.detect_format_stream(b''),
            None
        )

        # unrelated stream is none
        self.assertEqual(
            bndl_utils.detect_format_stream(b'hello world this is a test'),
            None
        )

        # docker save without tag starts with a hex digest tar dir entry
        self.assertEqual(
            bndl_utils.detect_format_stream(b'194853445611786369d26c17093e481cdc14c838375091037f780fe22aa760e7/'
                                            b'\x00\x00\x00'),
            'docker'
        )

        # docker save with a tag starts with a json tar file entry
        self.assertEqual(
            bndl_utils.detect_format_stream(b'4a415e3663882fbc554ee830889c68a33b3585503892cc718a4698e91ef2a526.json'
                                            b'\x00\x00\x00'),
            'docker'
        )

        # docker from a tar stream of a dir on disk, we just hope the order works out
        self.assertEqual(
            bndl_utils.detect_format_stream(b'\x00/manifest.json\x00\x00\x00/layer.tar\x00\x00\x00'),
            'docker'
        )

        # oci image from a tar stream of a dir on disk, we just hope the order works out
        self.assertEqual(
            bndl_utils.detect_format_stream(b'\x00/oci-layout\x00\x00\x00/refs/\x00\x00\x00'),
            'oci-image'
        )

    def test_detect_format_dir(self):
        docker_dir = tempfile.mkdtemp()
        oci_image_dir = tempfile.mkdtemp()
        nothing_dir = tempfile.mkdtemp()

        try:
            os.mkdir(os.path.join(oci_image_dir, 'refs'))
            os.mkdir(os.path.join(oci_image_dir, 'blobs'))

            open(os.path.join(oci_image_dir, 'oci-layout'), 'a').close()
            open(os.path.join(docker_dir, 'repositories'), 'a').close()
            open(os.path.join(docker_dir, 'manifest.json'), 'a').close()
            open(os.path.join(nothing_dir, 'hello'), 'a').close()

            self.assertEqual(bndl_utils.detect_format_dir(oci_image_dir), 'oci-image')
            self.assertEqual(bndl_utils.detect_format_dir(docker_dir), 'docker')
            self.assertEqual(bndl_utils.detect_format_dir(nothing_dir), None)
        finally:
            shutil.rmtree(docker_dir)
            shutil.rmtree(oci_image_dir)
            shutil.rmtree(nothing_dir)

    def test_digest_reader_writer(self):
        data = b'some data'
        digest = '1307990e6ba5ca145eb35e99182a9bec46531bc54ddf656a602c780fa0240dee'
        digest_empty = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'

        bytes_io = BytesIO(data)

        reader = bndl_utils.DigestReaderWriter(bytes_io)
        writer = bndl_utils.DigestReaderWriter(BytesIO())

        shutil.copyfileobj(reader, writer)

        self.assertEqual(reader.digest_in.hexdigest(), digest)
        self.assertEqual(reader.digest_out.hexdigest(), digest_empty)
        self.assertEqual(reader.size_in, 9)
        self.assertEqual(reader.size_out, 0)
        self.assertEqual(writer.digest_in.hexdigest(), digest_empty)
        self.assertEqual(writer.digest_out.hexdigest(), digest)
        self.assertEqual(writer.size_in, 0)
        self.assertEqual(writer.size_out, 9)
