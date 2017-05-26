from unittest import TestCase
from conductr_cli.resolvers import resolvers_util
import os
import shutil
import tempfile


class TestResolveBundle(TestCase):
    def test_is_local_file_with_file(self):
        with tempfile.NamedTemporaryFile() as temp:
            self.assertTrue(resolvers_util.is_local_file(temp.name, require_bundle_conf=True))
            self.assertTrue(resolvers_util.is_local_file(temp.name, require_bundle_conf=False))

    def test_is_local_file_with_empty_dir(self):
        temp = tempfile.mkdtemp()

        try:
            self.assertFalse(resolvers_util.is_local_file(temp, require_bundle_conf=True))
            self.assertTrue(resolvers_util.is_local_file(temp, require_bundle_conf=False))
        finally:
            shutil.rmtree(temp)

    def test_is_local_file_with_bundle_dir(self):
        temp = tempfile.mkdtemp()
        open(os.path.join(temp, 'bundle.conf'), 'w').close()

        try:
            self.assertTrue(resolvers_util.is_local_file(temp, require_bundle_conf=True))
            self.assertTrue(resolvers_util.is_local_file(temp, require_bundle_conf=False))
        finally:
            shutil.rmtree(temp)

    def test_is_local_file_with_bundle_conf_dir(self):
        temp = tempfile.mkdtemp()
        open(os.path.join(temp, 'runtime-config.sh'), 'w').close()

        try:
            self.assertFalse(resolvers_util.is_local_file(temp, require_bundle_conf=True))
            self.assertTrue(resolvers_util.is_local_file(temp, require_bundle_conf=False))
        finally:
            shutil.rmtree(temp)
