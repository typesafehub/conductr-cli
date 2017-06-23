from conductr_cli.constants import BNDL_IGNORE_TAGS, MAGIC_NUMBER_TAR, MAGIC_NUMBER_TAR_OFFSET, MAGIC_NUMBERS_ZIP
from enum import Enum
from pyhocon import ConfigFactory, ConfigTree
import hashlib
import os
import re
import time
import zipfile


class BndlFormat(Enum):
    BUNDLE = 'bundle'
    CONFIGURATION = 'configuration'
    DOCKER = 'docker'
    OCI_IMAGE = 'oci-image'

    def to_file_system_type(self):
        if self == BndlFormat.BUNDLE or self == BndlFormat.CONFIGURATION:
            return 'universal'
        elif self == BndlFormat.DOCKER:
            return 'docker'
        elif self == BndlFormat.OCI_IMAGE:
            return 'oci-image'


class ApplicationType(Enum):
    AKKA = 'akka'
    GENERIC = 'generic'
    LAGOM = 'lagom'
    PLAY = 'play'

    def config_defaults(self, file_system_type):
        if self == ApplicationType.PLAY or self == ApplicationType.LAGOM:
            return {
                'annotations': {},
                'compatibilityVersion': '0',
                'components': {
                    'description': '',
                    'file-system-type': file_system_type
                },
                'diskSpace': 1677721600,
                'memory': 402653184,
                'name': 'bundle',
                'nrOfCpus': 0.1,
                'roles': ['web'],
                'system': 'bundle',
                'systemVersion': '0',
                'tags': [],
                'version': '1'
            }
        else:
            return {
                'annotations': {},
                'compatibilityVersion': '0',
                'components': {
                    'description': '',
                    'file-system-type': file_system_type
                },
                'diskSpace': 1073741824,
                'memory': 402653184,
                'name': 'bundle',
                'nrOfCpus': 0.1,
                'roles': ['web'],
                'system': 'bundle',
                'systemVersion': '0',
                'tags': ['0.0.1'],
                'version': '1'
            }


def detect_format_dir(dir):
    """
    Detects the format of a directory on disk.
    :param dir:
    :return: one of 'BndlFormat.DOCKER', 'BndlFormat.OCI_IMAGE', 'BndlFormat.BUNDLE'
    """
    if os.path.isfile(os.path.join(dir, 'oci-layout')) and \
            os.path.isdir(os.path.join(dir, 'refs')) and \
            os.path.isdir(os.path.join(dir, 'blobs')):
        return BndlFormat.OCI_IMAGE
    elif os.path.isfile(os.path.join(dir, 'repositories')) and \
            os.path.isfile(os.path.join(dir, 'manifest.json')):
        return BndlFormat.DOCKER
    else:
        return BndlFormat.BUNDLE


def detect_format_stream(initial_chunk):
    """
    Detects the format of a stream given some initial chunk of data. This is fairly crude
    but does work pretty well with detecting `docker save` streams. OCI detection may need
    to be expanded as the tooling matures.

    :param initial_chunk:
    :return: one of 'BndlFormat.DOCKER', 'BndlFormat.OCI_IMAGE', 'BndlFormat.BUNDLE' or None
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
        return BndlFormat.DOCKER
    elif try_match('^[0-9a-f]{64}[.]json$', initial_chunk[0:69]):
        # docker save <image>:<tag>
        return BndlFormat.DOCKER
    elif b'/oci-layout\x00\x00\x00' in initial_chunk and b'/refs/\x00\x00\x00' in initial_chunk:
        # tar c on an oci folder (somewhat unreliable)
        return BndlFormat.OCI_IMAGE
    elif b'/manifest.json\x00\x00\x00' in initial_chunk and b'/layer.tar\x00\x00\x00' in initial_chunk:
        # tar c on a docker folder (somewhat unreliable)
        return BndlFormat.DOCKER
    elif b'\x00' not in initial_chunk and initial_chunk != b'' and data_is_bundle_conf(initial_chunk):
        return BndlFormat.BUNDLE
    elif data_is_zip(initial_chunk):
        return BndlFormat.BUNDLE
    elif data_is_tar(initial_chunk):
        # TAR marker
        return BndlFormat.BUNDLE
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


def escape_bash_double_quotes(input):
    """
    Given a string, escapes it according to bash rules while still allowing variable substitutions.
    https://www.gnu.org/software/bash/manual/html_node/Double-Quotes.html#Double-Quotes
    :param input:
    :return: escaped value (unquoted)
    """
    return input \
        .replace('\\', '\\\\') \
        .replace('`', '\\`') \
        .replace('"', '\\"')


def load_bundle_args_into_conf(config, args, application_type):
    config_defaults = application_type.config_defaults(args.format.to_file_system_type()) if application_type else None

    args_check_addresses = getattr(args, 'check_addresses', None)
    args_compatibility_version = getattr(args, 'compatibility_version', None)
    args_descriptions = getattr(args, 'descriptions', None)
    args_disk_space = getattr(args, 'disk_space', None)
    args_endpoints = getattr(args, 'endpoints', None)
    args_memory = getattr(args, 'memory', None)
    args_name = getattr(args, 'name', None)
    args_nr_of_cpus = getattr(args, 'nr_of_cpus', None)
    args_start_commands = getattr(args, 'start_commands', None)
    args_system = getattr(args, 'system', None)
    args_system_version = getattr(args, 'system_version', None)
    args_version = getattr(args, 'version', None)
    args_volumes = getattr(args, 'volumes', None)

    # config name need to set first because it is used for other config properties
    if args_name is not None:
        config_name = args_name
    elif 'name' in config:
        config_name = config['name']
    elif config_defaults:
        config_name = config_defaults['name']
    else:
        config_name = None

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
    if config_defaults and 'annotations' not in config:
        config.put('annotations', ConfigTree(config_defaults['annotations']))

    if args_check_addresses is not None:
        check_args = []
        if hasattr(args, 'check_initial_delay') and args.check_initial_delay:
            check_args += ['--initial-delay', str(args.check_initial_delay)]
        if hasattr(args, 'check_connection_timeout') and args.check_connection_timeout:
            check_args += ['--connection-timeout', str(args.check_connection_timeout)]
        check_args += args_check_addresses

        if 'components' not in config:
            config.put('components', ConfigTree())

        if 'bundle-status' in config.get('components'):
            config.put('components.bundle-status.start-command', ['check'] + check_args)
        else:
            check_tree = create_check_hocon(check_args)
            config.put('components.bundle-status', check_tree)

    if args_compatibility_version is not None:
        config.put('compatibilityVersion', args_compatibility_version)
    if config_defaults and 'compatibilityVersion' not in config:
        config.put('compatibilityVersion', config_defaults['compatibilityVersion'])

    # Component properties
    if args_descriptions:
        if 'components' not in config:
            config.put('components', ConfigTree())

        for description in args_descriptions:
            component_name = detect_component(config, description, config_name)
            description_key = 'components.{}.description'.format(component_name)
            config.put(description_key, description.description)

    if args_endpoints is not None:
        if 'components' not in config:
            config.put('components', ConfigTree())

        # Delete existing endpoints if exist in configuration
        for endpoint in args_endpoints:
            component_name = detect_component(config, endpoint, config_name)
            endpoint_key = 'components.{}.endpoints'.format(component_name)
            if endpoint_key in config:
                config.put(endpoint_key, None)
        # Add endpoints to bundle components based on the --endpoint argument
        for endpoint in args_endpoints:
            component_name = detect_component(config, endpoint, config_name)
            endpoint_key = 'components.{}.endpoints'.format(component_name)
            config.put(endpoint_key, endpoint.hocon())
        # Add empty endpoints property if args_endpoints is empty. This is required to be backwards compatible with
        # ConductR 2.0 and below
        if not args_endpoints:
            component_name = detect_component(config, None, config_name)
            endpoint_key = 'components.{}.endpoints'.format(component_name)
            config.put(endpoint_key, ConfigTree())

    if args_start_commands:
        if 'components' not in config:
            config.put('components', ConfigTree())

        for start_command in args_start_commands:
            component_name = detect_component(config, start_command, config_name)
            start_command_key = 'components.{}.start-command'.format(component_name)
            config.put(start_command_key, ConfigFactory.parse_string(start_command.start_command))

    if args_volumes:
        if 'components' not in config:
            config.put('components', ConfigTree())

        for volume in args_volumes:
            component_name = detect_component(config, volume, config_name)
            volume_key = 'components.{}.volumes.{}'.format(component_name, volume.name)
            config.put(volume_key, volume.mount_point)

    if config_defaults and 'components' in config:
        for component_name in config['components']:
            if 'description' not in config['components'][component_name]:
                description_key = 'components.{}.description'.format(component_name)
                config.put(description_key, config_defaults['components']['description'])
            if 'file-system-type' not in config['components'][component_name]:
                file_system_type_key = 'components.{}.file-system-type'.format(component_name)
                config.put(file_system_type_key, config_defaults['components']['file-system-type'])

    if args_disk_space is not None:
        config.put('diskSpace', args_disk_space)
    if config_defaults and 'diskSpace' not in config:
        config.put('diskSpace', config_defaults['diskSpace'])

    if args_memory is not None:
        config.put('memory', args_memory)
    if config_defaults and 'memory' not in config:
        config.put('memory', config_defaults['memory'])

    if config_name:
        config.put('name', config_name)

    if args_nr_of_cpus is not None:
        config.put('nrOfCpus', args_nr_of_cpus)
    if config_defaults and 'nrOfCpus' not in config:
        config.put('nrOfCpus', config_defaults['nrOfCpus'])

    if hasattr(args, 'roles') and len(args.roles) > 0:
        roles = []
        for role in args.roles:
            if role not in roles:
                roles.append(role)
        config.put('roles', roles)
    if config_defaults and 'roles' not in config:
        config.put('roles', config_defaults['roles'])

    if args_system is not None:
        config.put('system', args_system)
    if config_defaults and 'system' not in config:
        config.put('system', config.get('name') if 'name' in config else config_defaults['system'])

    if args_system_version is not None:
        config.put('systemVersion', args_system_version)
    if config_defaults and 'systemVersion' not in config:
        config.put('systemVersion', config.get('version') if 'version' in config else config_defaults['systemVersion'])

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
    if config_defaults and 'tags' not in config:
        config.put('tags', config_defaults['tags'])

    if args_version is not None:
        config.put('version', args_version)
    if config_defaults and 'version' not in config:
        config.put('version', config_defaults['version'])


def create_check_hocon(check_args):
    check_tree = ConfigTree()
    check_tree.put('description', 'Status check for the bundle component')
    check_tree.put('file-system-type', 'universal')
    check_tree.put('start-command', ['check'] + check_args)
    check_tree.put('endpoints', {})  # Necessary to be backward compatible with ConductR 2.0.x and below
    return check_tree


def detect_component(config, args, default_component_name):
    if hasattr(args, 'component'):
        return args.component
    else:
        non_status_component_names = [component for component in config.get('components')
                                      if component != 'bundle-status']
        non_status_component_len = len(non_status_component_names)
        if non_status_component_len == 0:
            if default_component_name:
                return default_component_name
            else:
                raise SyntaxError('Unable to auto-detect the component. '
                                  'Component not specified, bundle.conf does not contain a component and component '
                                  'cannot be derived from the bundle.conf name because name is not declared\n'
                                  'Set a component name by either specifying the --component argument or by '
                                  'specifying the --with-defaults <application_type> argument')
        elif non_status_component_len == 1:
            return non_status_component_names[0]
        else:
            raise SyntaxError('Unable to auto-detect the component. '
                              'Component not specified and bundle.conf contains multiple components: {}'
                              .format(non_status_component_names))


def file_write_bytes(path, bs):
    with open(path, 'wb') as file:
        file.write(bs)


def find_bundle_conf_dir(dir):
    for dir_path, dir_names, file_names in os.walk(dir):
        for file_name in file_names:
            if file_name == 'bundle.conf' or file_name == 'runtime-config.sh':
                return dir_path
    return dir


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
