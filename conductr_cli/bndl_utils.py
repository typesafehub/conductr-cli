from conductr_cli.constants import \
    BNDL_DEFAULT_ANNOTATIONS, \
    BNDL_DEFAULT_COMPATIBILITY_VERSION, \
    BNDL_DEFAULT_DISK_SPACE, \
    BNDL_IGNORE_TAGS, \
    BNDL_DEFAULT_MEMORY, \
    BNDL_DEFAULT_NAME, \
    BNDL_DEFAULT_NR_OF_CPUS, \
    BNDL_DEFAULT_ROLES, \
    BNDL_DEFAULT_TAGS, \
    BNDL_DEFAULT_VERSION, \
    MAGIC_NUMBER_TAR, \
    MAGIC_NUMBER_TAR_OFFSET, \
    MAGIC_NUMBERS_ZIP
from pyhocon import ConfigFactory, ConfigTree
import hashlib
import os
import re
import time
import zipfile


def detect_format_dir(dir):
    """
    Detects the format of a directory on disk.
    :param dir:
    :return: one of 'docker', 'oci-image', 'bundle', or None
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
    elif \
            os.path.isfile(os.path.join(dir, 'runtime-config.sh')):
        return 'bundle'
    elif \
            os.path.isfile(os.path.join(dir, 'bundle.conf')):
        return 'bundle'
    else:
        return None


def detect_format_stream(initial_chunk):
    """
    Detects the format of a stream given some initial chunk of data. This is fairly crude
    but does work pretty well with detecting `docker save` streams. OCI detection may need
    to be expanded as the tooling matures.

    :param initial_chunk:
    :return: one of 'docker', 'oci-image', or None
    """

    def try_match(pattern, slice):
        try:
            return not not re.match(pattern, slice.decode('UTF-8'))
        except UnicodeError:
            # we're attempting to decode binary data as UTF8 to check for certain markers,
            # but it's possible we aren't actually given UTF8 data so in that case the
            # decode calls above will throw a UnicodeError.

            return False

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
    elif b'\x00' not in initial_chunk and initial_chunk != b'' and data_is_bundle_conf(initial_chunk):
        return 'bundle'
    elif data_is_zip(initial_chunk):
        return 'bundle'
    elif data_is_tar(initial_chunk):
        # TAR marker
        return 'bundle'
    else:
        return None


def data_is_bundle_conf(data):
    try:
        ConfigFactory.parse_string(data.decode('UTF-8'))
        return True
    except:
        return False


def data_is_tar(data):
    """
    Detects if an initial 1KB+ chunk of data from a stream indicates the stream
    is a tar file. This is determined by TAR's magic number.
    https://en.wikipedia.org/wiki/Tar_(computing)
    :param data: first chunk from a tar stream
    :return: True if tar
    """
    return \
        len(data) >= MAGIC_NUMBER_TAR_OFFSET + len(MAGIC_NUMBER_TAR) and \
        data[MAGIC_NUMBER_TAR_OFFSET:MAGIC_NUMBER_TAR_OFFSET + len(MAGIC_NUMBER_TAR)] == MAGIC_NUMBER_TAR


def data_is_zip(data):
    """
    Detects if an initial 1KB+ chunk of data from a stream indicates the stream
    is a zip file. This is determined by ZIP's magic numbers.
    https://en.wikipedia.org/wiki/Zip_(file_format)
    :param data: first chunk from a zip stream
    :return: True if zip
    """
    return any(data.startswith(number) for number in MAGIC_NUMBERS_ZIP)


def load_bundle_args_into_conf(config, args, with_defaults):
    # this is unrolled because it's actually pretty complicated to get the order
    # correct given that some attributes need special handling and defaults

    args_compatibility_version = getattr(args, 'compatibility_version', None)
    args_disk_space = getattr(args, 'disk_space', None)
    args_endpoints = getattr(args, 'endpoints', None)
    args_memory = getattr(args, 'memory', None)
    args_name = getattr(args, 'name', None)
    args_nr_of_cpus = getattr(args, 'nr_of_cpus', None)
    args_roles = getattr(args, 'roles', None)
    args_system = getattr(args, 'system', None)
    args_system_version = getattr(args, 'system_version', None)
    args_version = getattr(args, 'version', None)

    if hasattr(args, 'annotations') and len(args.annotations) > 0:
        annotations_tree = ConfigTree()

        invalid_annotations = []

        for annotation in args.annotations:
            if '=' in annotation:
                annotation_parts = annotation.split('=', 1)
                annotations_tree.put(annotation_parts[0], annotation_parts[1])
            else:
                invalid_annotations.append(annotation)

        if len(invalid_annotations) > 0:
            raise ValueError(
                'Invalid annotation format for {}. Specify as name=value'.format(', '.join(invalid_annotations))
            )

        config.put('annotations', annotations_tree)
    if with_defaults and 'annotations' not in config:
        config.put('annotations', ConfigTree(BNDL_DEFAULT_ANNOTATIONS.copy()))

    if args_compatibility_version is not None:
        config.put('compatibilityVersion', args_compatibility_version)
    if with_defaults and 'compatibilityVersion' not in config:
        config.put('compatibilityVersion', BNDL_DEFAULT_COMPATIBILITY_VERSION)

    if args_disk_space is not None:
        config.put('diskSpace', args_disk_space)
    if with_defaults and 'diskSpace' not in config:
        config.put('diskSpace', BNDL_DEFAULT_DISK_SPACE)

    if args_endpoints is not None:
        # Delete existing endpoints if exist in configuration
        for endpoint in args_endpoints:
            endpoint_key = 'components.{}.endpoints'.format(endpoint.component)
            if endpoint_key in config:
                config.put(endpoint_key, None)
        # Add endpoints to bundle components based on the --endpoint argument
        for endpoint in args_endpoints:
            endpoint_key = 'components.{}.endpoints'.format(endpoint.component)
            config.put(endpoint_key, endpoint.hocon())

    if args_memory is not None:
        config.put('memory', args_memory)
    if with_defaults and 'memory' not in config:
        config.put('memory', BNDL_DEFAULT_MEMORY)

    if args_name is not None:
        config.put('name', args_name)
    if with_defaults and 'name' not in config:
        config.put('name', BNDL_DEFAULT_NAME)

    if args_nr_of_cpus is not None:
        config.put('nrOfCpus', args_nr_of_cpus)
    if with_defaults and 'nrOfCpus' not in config:
        config.put('nrOfCpus', BNDL_DEFAULT_NR_OF_CPUS)

    if args_roles is not None:
        config.put('roles', args_roles)
    if with_defaults and 'roles' not in config:
        config.put('roles', BNDL_DEFAULT_ROLES.copy())

    if args_system is not None:
        config.put('system', args_system)
    if with_defaults and 'system' not in config:
        config.put('system', config.get('name') if 'name' in config else BNDL_DEFAULT_NAME)

    if args_system_version is not None:
        config.put('systemVersion', args_system_version)
    if with_defaults and 'systemVersion' not in config:
        config.put('systemVersion', config.get('version') if 'version' in config else BNDL_DEFAULT_VERSION)

    if hasattr(args, 'image_tag'):
        tags = config.get('tags') if 'tags' in config else []

        if args.image_tag is not None and args.image_tag not in tags and args.image_tag not in BNDL_IGNORE_TAGS:
            tags.append(args.image_tag)
            config.put('tags', tags)
    if hasattr(args, 'tags') and len(args.tags) > 0:
        tags = []

        for tag in args.tags:
            if tag not in tags:
                tags.append(tag)

        config.put('tags', tags)
    if with_defaults and 'tags' not in config:
        config.put('tags', BNDL_DEFAULT_TAGS.copy())

    if args_version is not None:
        config.put('version', args_version)
    if with_defaults and 'version' not in config:
        config.put('version', BNDL_DEFAULT_VERSION)


def file_write_bytes(path, bs):
    with open(path, 'wb') as file:
        file.write(bs)


def find_bundle_conf_dir(dir):
    for dir_path, dir_names, file_names in os.walk(dir):
        for file_name in file_names:
            if file_name == 'bundle.conf' or file_name == 'runtime-config.sh':
                return dir_path
    return None


def first_mtime(path, default=0):
    for (dir_path, dir_names, file_names) in os.walk(path):
        for file_name in file_names:
            return os.path.getmtime(os.path.join(dir_path, file_name))

    return default


def zip_extract_with_dates(zip_file, into):
    with zipfile.ZipFile(file=zip_file, mode='r') as zip:
        for info in zip.infolist():
            zip.extract(info, into)
            t = time.mktime(info.date_time + (0, 0, -1))
            os.utime(os.path.join(into, info.filename), (t, t))
            # Preserve bits 0-8 only: rwxrwxrwx
            mode = info.external_attr >> 16 & 0x1FF
            os.chmod(os.path.join(into, info.filename), mode)


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
