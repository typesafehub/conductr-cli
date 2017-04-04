from collections import OrderedDict
from conductr_cli.constants import \
    BNDL_DEFAULT_COMPATIBILITY_VERSION, \
    BNDL_DEFAULT_DISK_SPACE, \
    BNDL_IGNORE_TAGS, \
    BNDL_DEFAULT_MEMORY, \
    BNDL_DEFAULT_NR_OF_CPUS, \
    BNDL_DEFAULT_ROLES, \
    BNDL_DEFAULT_VERSION
from pyhocon import ConfigTree
import hashlib
import os
import re

mappings = OrderedDict([
    ('--name', 'name'),
    ('--version', 'version'),
    ('--compatibility-version', 'compatibilityVersion'),
    ('--system', 'system'),
    ('--system-version', 'systemVersion'),
    ('--nr-of-cpus', 'nrOfCpus'),
    ('--memory', 'memory'),
    ('--disk-space', 'diskSpace'),
    ('--roles', 'roles')
])


def detect_format_dir(dir):
    """
    Detects the format of a directory on disk.
    :param dir:
    :return: one of 'docker', 'oci-image', or None
    """
    if \
            os.path.isfile(os.path.join(dir, 'oci-layout')) and \
            os.path.isdir(os.path.join(dir, 'refs')) and \
            os.path.isdir(os.path.join(dir, 'blobs')):
        return 'oci-image'
    elif \
            os.path.isfile(os.path.join(dir, 'repositories')) and \
            os.path.isfile(os.path.join(dir, 'manifest.json')):
        return 'docker'
    else:
        return None


def detect_format_stream(initial_chunk):
    def try_match(pattern, slice):
        try:
            return not not re.match(pattern, slice.decode('UTF-8'))
        except UnicodeError:
            # we're attempting to decode binary data as UTF8 to check for certain markers,
            # but it's possible we aren't actually given UTF8 data so in that case the
            # decode calls above will throw a UnicodeError.

            return False

    """
    Detects the format of a stream given some initial chunk of data. This is fairly crude
    but does work pretty well with detecting `docker save` streams. OCI detection may need
    to be expanded as the tooling matures.

    :param initial_chunk:
    :return: one of 'docker', 'oci-image', or None
    """
    if try_match('^[0-9a-f]{64}[/]', initial_chunk[0:65]):
        # docker save <image>
        return 'docker'
    elif try_match('^[0-9a-f]{64}[.]json$', initial_chunk[0:69]):
        # docker save <image>:<tag>
        return 'docker'
    elif b'/oci-layout\x00\x00\x00' in initial_chunk and b'/refs/\x00\x00\x00' in initial_chunk:
        # tar c on an oci folder (somewhat unreliable)
        return 'oci-image'
    elif b'/manifest.json\x00\x00\x00' in initial_chunk and b'/layer.tar\x00\x00\x00' in initial_chunk:
        # tar c on a docker folder (somewhat unreliable)
        return 'docker'
    else:
        return None


def load_bundle_args_into_conf(config, args):
    if args.name is not None:
        config.put('name', args.name)

    for argument, bundle_key in mappings.items():
        value = getattr(args, bundle_key, None)

        if value is not None:
            config.put(bundle_key, value)

    if 'roles' not in config:
        config.put('roles', BNDL_DEFAULT_ROLES)

    if 'compatibilityVersion' not in config:
        config.put('compatibilityVersion', BNDL_DEFAULT_COMPATIBILITY_VERSION)

    if 'diskSpace' not in config:
        config.put('diskSpace', BNDL_DEFAULT_DISK_SPACE)

    if 'memory' not in config:
        config.put('memory', BNDL_DEFAULT_MEMORY)

    if 'nrOfCpus' not in config:
        config.put('nrOfCpus', BNDL_DEFAULT_NR_OF_CPUS)

    if 'version' not in config:
        config.put('version', BNDL_DEFAULT_VERSION)

    if 'system' not in config:
        config.put('system', config.get('name'))

    if 'systemVersion' not in config:
        config.put('systemVersion', config.get('version'))

    tags = config.get('tags') if 'tags' in config else []

    if args.tag not in tags and args.tag not in BNDL_IGNORE_TAGS:
        tags.append(args.tag)

    config.put('tags', tags)

    annotations_tree = ConfigTree()

    for annotation in args.annotations:
        if '=' not in annotation:
            raise ValueError('Invalid annotation format. Specify as name=value')

        annotation_parts = annotation.split('=', 1)
        annotations_tree.put(annotation_parts[0], annotation_parts[1])

    config.put('annotations', annotations_tree)


def file_write_bytes(path, bs):
    with open(path, 'wb') as file:
        file.write(bs)


class DigestReaderWriter(object):
    def __init__(self, fileobj):
        self.digest_in = hashlib.sha256()
        self.digest_out = hashlib.sha256()
        self.fileobj = fileobj
        self.size_in = 0
        self.size_out = 0

    def read(self, size):
        data = self.fileobj.read(size)

        self.digest_in.update(data)
        self.size_in += len(data)

        return data

    def write(self, data):
        length = self.fileobj.write(data)

        self.digest_out.update(data)
        self.size_out += len(data)

        return length
