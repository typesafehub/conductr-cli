from unittest import TestCase
from conductr_cli import bundle_utils, constants
from conductr_cli.test.cli_test_case import create_temp_bundle_with_contents
import shutil
import tempfile


class ShortId(TestCase):
    def test(self):
        self.assertEqual(
            bundle_utils.short_id('45e0c477d3e5ea92aa8d85c0d8f3e25c'),
            '45e0c47')

        self.assertEqual(
            bundle_utils.short_id('c1ab77e63b722ef8c6ea8a1c274be053-3cc322b62e7608b5cdf37185240f7853'),
            'c1ab77e-3cc322b')


class Conf(TestCase):
    def setUp(self):  # noqa
        self.tmpdir, self.bundle_path = create_temp_bundle_with_contents({
            'bundle.conf': 'bundle conf contents',
            'password.txt': 'monkey',
            'dir/bundle.conf': 'another bundle conf contents'
        })

    def test(self):
        conf_contents = bundle_utils.conf(self.bundle_path)
        self.assertEqual(conf_contents, 'bundle conf contents')

    def tearDown(self):  # noqa
        shutil.rmtree(self.tmpdir)


class Digest(TestCase):
    def test_digest_calculate_short(self):
        data = b'hello\nsha-256/6ae881d57578a07900c4eb37e21afa4c2095beb8e852fb6ed8d0c9f343bc7fa8'

        digest, starts, length = bundle_utils.digest_calculate(data)

        self.assertEqual(digest, ('sha-256', '6ae881d57578a07900c4eb37e21afa4c2095beb8e852fb6ed8d0c9f343bc7fa8'))
        self.assertEqual(starts, 5)
        self.assertEqual(length, 73)

    def test_digest_calculate_long(self):
        some_raw_test_data = b'abc' * 1000

        data = some_raw_test_data + b'\nsha-256/6ae881d57578a07900c4eb37e21afa4c2095beb8e852fb6ed8d0c9f343bc7fa8'

        digest, starts, length = bundle_utils.digest_calculate(data)

        self.assertEqual(digest, ('sha-256', '6ae881d57578a07900c4eb37e21afa4c2095beb8e852fb6ed8d0c9f343bc7fa8'))
        self.assertEqual(starts, 3000)
        self.assertEqual(length, 73)

    def test_digested_read_no_digest_small(self):
        with tempfile.NamedTemporaryFile() as file:
            some_test_data = b'this is a test file'

            self.assertLess(len(some_test_data), constants.DIGEST_TRAIL_SIZE)

            file.write(some_test_data)
            file.flush()
            file.seek(0)

            reader = bundle_utils.DigestedRead(file)

            data = reader.read(1024)

            self.assertEqual(data, some_test_data)
            self.assertEqual(reader.digest, None)

    def test_digested_read_with_digest_small(self):
        with tempfile.NamedTemporaryFile() as file:
            some_raw_test_data = b'this is a test file'

            some_test_data = \
                some_raw_test_data + b'\nsha-256/6ae881d57578a07900c4eb37e21afa4c2095beb8e852fb6ed8d0c9f343bc7fa8'

            self.assertLess(len(some_test_data), constants.DIGEST_TRAIL_SIZE)

            file.write(some_test_data)
            file.flush()
            file.seek(0)

            reader = bundle_utils.DigestedRead(file)

            data = reader.read(1024)

            self.assertEqual(reader.emitted, len(some_raw_test_data))

            self.assertEqual(data, some_raw_test_data)

            self.assertEqual(
                reader.digest,
                ('sha-256', '6ae881d57578a07900c4eb37e21afa4c2095beb8e852fb6ed8d0c9f343bc7fa8')
            )

    def test_digested_read_no_digest_large(self):
        some_test_data = b'abc' * 1000

        self.assertGreater(len(some_test_data), constants.DIGEST_TRAIL_SIZE)

        with tempfile.NamedTemporaryFile() as file:
            file.write(some_test_data)
            file.flush()
            file.seek(0)
            reader = bundle_utils.DigestedRead(file)

            data = b''

            done = False

            while not done:
                chunk = reader.read(128)

                if chunk:
                    data += chunk
                else:
                    done = True

            self.assertEqual(reader.digest, None)
            self.assertEqual(reader.emitted, len(some_test_data))
            self.assertEqual(data, some_test_data)

    def test_digested_read_with_digest_large(self):
        some_raw_test_data = b'abc' * 1000

        some_test_data = \
            some_raw_test_data + b'\nsha-256/6ae881d57578a07900c4eb37e21afa4c2095beb8e852fb6ed8d0c9f343bc7fa8'

        self.assertGreater(len(some_test_data), constants.DIGEST_TRAIL_SIZE)

        with tempfile.NamedTemporaryFile() as file:
            file.write(some_test_data)
            file.flush()
            file.seek(0)
            reader = bundle_utils.DigestedRead(file)

            data = b''

            done = False

            while not done:
                chunk = reader.read(128)

                if chunk:
                    data += chunk
                else:
                    done = True

            self.assertEqual(data, some_raw_test_data)

            self.assertEqual(reader.emitted, len(some_raw_test_data))

            self.assertEqual(
                reader.digest,
                ('sha-256', '6ae881d57578a07900c4eb37e21afa4c2095beb8e852fb6ed8d0c9f343bc7fa8')
            )
