from conductr_cli.constants import IO_CHUNK_SIZE
from conductr_cli.resolvers.schemes import SCHEME_STDIN
import sys
import tempfile

ALLOCATED_FILES = []


def supported_schemes():
    return [SCHEME_STDIN]


def resolve_bundle(cache_dir, uri, auth=None):
    if sys.stdin.isatty() or uri != '-':
        return False, None, None, None
    else:
        temp = tempfile.NamedTemporaryFile(delete=False)

        done = False

        while not done:
            chunk = sys.stdin.buffer.read(IO_CHUNK_SIZE)

            if chunk:
                temp.write(chunk)
            else:
                done = True

        temp.flush()

        # keep a reference to the tempfile around, so it's properly deleted on program exit instead of
        # us having to manually manage that

        ALLOCATED_FILES.append(temp)

        return True, None, temp.name, None


def load_bundle_from_cache(cache_dir, uri):
    return False, None, None, None


def resolve_bundle_configuration(cache_dir, uri, auth=None):
    return False, None, None, None


def load_bundle_configuration_from_cache(cache_dir, uri):
    return False, None, None, None


def resolve_bundle_version(uri):
    return None, None


def continuous_delivery_uri(resolved_version):
    return None


def is_bundle_name(uri):
    return uri.count('/') == 0 and uri.count('.') == 0
