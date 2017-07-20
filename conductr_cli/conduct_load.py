from pyhocon import ConfigFactory, ConfigTree
from pyhocon.exceptions import ConfigMissingException
from conductr_cli import bndl_main, bundle_utils, conduct_request, conduct_url, constants, screen_utils, validation
from conductr_cli.exceptions import MalformedBundleError, InsecureFilePermissions
from conductr_cli import resolver, bundle_installation
from conductr_cli.constants import DEFAULT_BUNDLE_RESOLVE_CACHE_DIR, \
    DEFAULT_CONFIGURATION_RESOLVE_CACHE_DIR
from conductr_cli.bndl_utils import BndlFormat
from conductr_cli.conduct_url import conductr_host
from functools import partial
from requests_toolbelt.multipart.encoder import MultipartEncoder, MultipartEncoderMonitor

import glob
import io
import os
import stat
import sys
import time
import json
import logging
import tempfile
import zipfile


# A mapping of respected `bndl` arguments to their defaults
BNDL_ARGS = {
    'endpoint_dicts': [],
    'envs': [],
    'check_addresses': None,
    'check_connection_timeout': None,
    'check_initial_delay': None,
    'annotations': [],
    'compatibility_version': None,
    'disk_space': None,
    'memory': None,
    'name': None,
    'nr_of_cpus': None,
    'start_command_dicts': [],
    'roles': [],
    'system': None,
    'system_version': None,
    'tags': [],
    'version': None,
    'volume_dicts': []
}

# A list of arguments that will need `component` added because
# it cannot be detected from the configuration
BNDL_ARGS_WITH_COMPONENT = ['endpoint_dicts', 'start_command_dicts', 'volume_dicts']

# The number of old bundle versions to keep when performing housekeeping, apart from the recently loaded bundle.
KEEP_BUNDLE_VERSIONS = 1


@validation.handle_connection_error
@validation.handle_http_error
@validation.handle_invalid_config
@validation.handle_no_file
@validation.handle_bad_zip
@validation.handle_malformed_bundle
@validation.handle_bundle_resolution_error
@validation.handle_wait_timeout_error
@validation.handle_conduct_load_read_timeout_error
@validation.handle_insecure_file_permissions
@validation.handle_bintray_resolution_error
@validation.handle_bintray_credentials_error
def load(args):
    if args.api_version == '1':
        return load_v1(args)
    else:
        return load_v2(args)


def load_v1(args):
    log = logging.getLogger(__name__)

    log.info('Retrieving bundle..')
    custom_settings = args.custom_settings
    bundle_resolve_cache_dir = args.bundle_resolve_cache_dir
    configuration_cache_dir = args.configuration_resolve_cache_dir

    validate_cache_dir_permissions(bundle_resolve_cache_dir, configuration_cache_dir, log)

    initial_bundle_file_name, bundle_file = resolver.resolve_bundle(custom_settings, bundle_resolve_cache_dir,
                                                                    args.bundle, args.offline_mode)

    configuration_file_name, configuration_file = (None, None)
    if args.configuration is not None:
        log.info('Retrieving configuration..')
        configuration_file_name, configuration_file = \
            resolver.resolve_bundle_configuration(custom_settings, configuration_cache_dir,
                                                  args.configuration, args.offline_mode)

    bundle_conf_text = bundle_utils.conf(bundle_file)

    bundle_conf = ConfigFactory.parse_string(bundle_conf_text)

    bundle_file_name, bundle_open_file = open_bundle(initial_bundle_file_name, bundle_file, bundle_conf_text)

    overlay_bundle_conf = None if configuration_file is None else \
        ConfigFactory.parse_string(bundle_utils.conf(configuration_file))

    with_bundle_configurations = partial(apply_to_configurations, bundle_conf, overlay_bundle_conf)

    url = conduct_url.url('bundles', args)
    files = get_payload(bundle_file_name, bundle_open_file, with_bundle_configurations)
    if configuration_file is not None:
        open_configuration_file, config_digest = bundle_utils.digest_extract_and_open(configuration_file)
        files.append(('configuration', (configuration_file_name, open_configuration_file)))

    # TODO: Delete the bundle configuration file.
    # Currently, this results into a permission error on Windows.
    # Therefore, the deletion is disabled for now.
    # Issue: https://github.com/typesafehub/conductr-cli/issues/175
    # if configuration_file and os.path.exists(configuration_file):
    #    os.remove(configuration_file)

    log.info('Loading bundle to ConductR..')
    multipart = create_multipart(log, files)
    response = conduct_request.post(args.dcos_mode, conductr_host(args), url,
                                    data=multipart,
                                    auth=args.conductr_auth,
                                    verify=args.server_verification_file,
                                    headers={'Content-Type': multipart.content_type})
    validation.raise_for_status_inc_3xx(response)

    if log.is_verbose_enabled():
        log.verbose(validation.pretty_json(response.text))

    response_json = json.loads(response.text)
    bundle_id = response_json['bundleId'] if args.long_ids else bundle_utils.short_id(response_json['bundleId'])

    if not args.no_wait:
        bundle_installation.wait_for_installation(response_json['bundleId'], args)

    cleanup_old_bundles(bundle_resolve_cache_dir, bundle_file_name, excluded=bundle_file)

    log.info('Bundle loaded.')
    if not args.disable_instructions:
        log.info('Start bundle with:        {} run{} {}'.format(args.command, args.cli_parameters, bundle_id))
        log.info('Unload bundle with:       {} unload{} {}'.format(args.command, args.cli_parameters, bundle_id))
        log.info('Print ConductR info with: {} info{}'.format(args.command, args.cli_parameters))
        log.info('Print bundle info with:   {} info{} {}'.format(args.command, args.cli_parameters, bundle_id))

    if not log.is_info_enabled() and log.is_quiet_enabled():
        log.quiet(response_json['bundleId'])

    return True


def apply_to_configurations(base_conf, overlay_conf, method, key):
    if overlay_conf is None:
        return method(base_conf, key)
    else:
        try:
            return method(overlay_conf, key)
        except ConfigMissingException:
            return method(base_conf, key)


def get_payload(bundle_name, bundle_open_file, bundle_configuration):
    return [
        ('nrOfCpus', bundle_configuration(ConfigTree.get_string, 'nrOfCpus')),
        ('memory', bundle_configuration(ConfigTree.get_string, 'memory')),
        ('diskSpace', bundle_configuration(ConfigTree.get_string, 'diskSpace')),
        ('roles', ' '.join(bundle_configuration(ConfigTree.get_list, 'roles'))),
        ('bundleName', bundle_configuration(ConfigTree.get_string, 'name')),
        ('system', bundle_configuration(ConfigTree.get_string, 'system')),
        ('bundle', (bundle_name, bundle_open_file))
    ]


def validate_cache_dir_permissions(bundle_cache_dir, configuration_cache_dir, log):
    def validate(cache_dir, default_cache_dir):
        if os.path.exists(cache_dir):
            permissions = oct(stat.S_IMODE(os.lstat(cache_dir).st_mode))[-3:]
            if permissions[-2:] != '00':
                if cache_dir == default_cache_dir:
                    log.info('Cache directory {} has the permissions {}. Setting permissions to 700.'
                             .format(cache_dir, permissions))
                    os.chmod(cache_dir, 0o700)
                else:
                    raise InsecureFilePermissions('The cache directory {} has the permissions: {}'
                                                  .format(cache_dir, permissions))
    validate(bundle_cache_dir, DEFAULT_BUNDLE_RESOLVE_CACHE_DIR)
    validate(configuration_cache_dir, DEFAULT_CONFIGURATION_RESOLVE_CACHE_DIR)


def is_bundle(input):
    return os.path.isfile(input) and zipfile.is_zipfile(input)


def bndl_arguments_present(args):
    for arg in BNDL_ARGS:
        if hasattr(args, arg) and getattr(args, arg) != BNDL_ARGS[arg]:
            return True

    return False


def invoke_bndl(input, format=None, additional_args=None, bundle_conf=None):
    temp_file = tempfile.NamedTemporaryFile()
    args = [input, '-o', temp_file.name]
    arg_keys = {}

    if format is not None:
        args.append('-f')
        args.append(format)

    if additional_args is not None:
        parsed_bundle_conf = ConfigFactory.parse_string(bundle_conf)
        for arg in BNDL_ARGS:
            if hasattr(additional_args, arg):
                arg_keys[arg] = getattr(additional_args, arg)
                if arg in BNDL_ARGS_WITH_COMPONENT:
                    for entry in arg_keys[arg]:
                        if 'component' not in entry and 'components' in parsed_bundle_conf:
                            components = parsed_bundle_conf.get_config('components').as_plain_ordered_dict().keys()

                            first_component = next(iter(components), None)

                            if first_component:
                                entry['component'] = first_component

    return_code = bndl_main.invoke(args, arg_keys)

    if return_code != 0:
        sys.exit(return_code)

    return temp_file


def load_v2(args):
    log = logging.getLogger(__name__)

    log.info('Retrieving bundle..')
    custom_settings = args.custom_settings
    bundle_resolve_cache_dir = args.bundle_resolve_cache_dir
    configuration_cache_dir = args.configuration_resolve_cache_dir

    validate_cache_dir_permissions(bundle_resolve_cache_dir, configuration_cache_dir, log)

    initial_bundle_file_name, bundle_file = resolver.resolve_bundle(custom_settings, bundle_resolve_cache_dir,
                                                                    args.bundle, args.offline_mode)

    if not is_bundle(bundle_file):
        bundle_fileobj = invoke_bndl(bundle_file)
        bundle_file = bundle_fileobj.name

    bundle_conf = bundle_utils.conf(bundle_file)

    if bundle_conf is None:
        raise MalformedBundleError('Unable to find bundle.conf within the bundle file')

    bundle_file_name, bundle_open_file = open_bundle(initial_bundle_file_name, bundle_file, bundle_conf)

    configuration_file_name, configuration_file, bundle_conf_overlay = (None, None, None)
    if args.configuration is not None:
        log.info('Retrieving configuration..')
        configuration_file_name, configuration_file = \
            resolver.resolve_bundle_configuration(custom_settings, configuration_cache_dir,
                                                  args.configuration, args.offline_mode)
        if not is_bundle(configuration_file) or bndl_arguments_present(args):
            configuration_fileobj = invoke_bndl(configuration_file, BndlFormat.CONFIGURATION.value, args, bundle_conf)
            configuration_file = configuration_fileobj.name
            configuration_file_name = os.path.basename(configuration_file)
        bundle_conf_overlay = bundle_utils.conf(configuration_file)
    elif bndl_arguments_present(args):
        with tempfile.NamedTemporaryFile() as empty_file:
            os.utime(empty_file.name, (constants.SHAZAR_TIMESTAMP_MIN, constants.SHAZAR_TIMESTAMP_MIN))
            configuration_fileobj = invoke_bndl(empty_file.name, BndlFormat.CONFIGURATION.value, args, bundle_conf)
            configuration_file = configuration_fileobj.name
            configuration_file_name = os.path.basename(configuration_file)
            bundle_conf_overlay = bundle_utils.conf(configuration_file)

    files = [('bundleConf', ('bundle.conf', string_io(bundle_conf)))]
    if bundle_conf_overlay is not None:
        files.append(('bundleConfOverlay', ('bundle.conf', string_io(bundle_conf_overlay))))
    files.append(('bundle', (bundle_file_name, bundle_open_file)))
    if configuration_file is not None:
        open_configuration_file, config_digest = bundle_utils.digest_extract_and_open(configuration_file)
        if config_digest is not None and not configuration_file_name.endswith('-{}.zip'.format(config_digest)):
            configuration_file_name = 'config-{}.zip'.format(config_digest[1])

        files.append(('configuration', (configuration_file_name, open_configuration_file)))

    # TODO: Delete the bundle configuration file.
    # Currently, this results into a permission error on Windows.
    # Therefore, the deletion is disabled for now.
    # Issue: https://github.com/typesafehub/conductr-cli/issues/175
    # if configuration_file and os.path.exists(configuration_file):
    #     os.remove(configuration_file)

    url = conduct_url.url('bundles', args)

    log.info('Loading bundle to ConductR..')
    multipart = create_multipart(log, files)

    response = conduct_request.post(args.dcos_mode, conductr_host(args), url,
                                    data=multipart,
                                    auth=args.conductr_auth,
                                    verify=args.server_verification_file,
                                    headers={'Content-Type': multipart.content_type})
    validation.raise_for_status_inc_3xx(response)

    if log.is_verbose_enabled():
        log.verbose(validation.pretty_json(response.text))

    response_json = json.loads(response.text)
    bundle_id = response_json['bundleId'] if args.long_ids else bundle_utils.short_id(response_json['bundleId'])

    if not args.no_wait:
        bundle_installation.wait_for_installation(response_json['bundleId'], args)

    cleanup_old_bundles(bundle_resolve_cache_dir, bundle_file_name, excluded=bundle_file)

    log.info('Bundle loaded.')
    if not args.disable_instructions:
        log.info('Start bundle with:        {} run{} {}'.format(args.command, args.cli_parameters, bundle_id))
        log.info('Unload bundle with:       {} unload{} {}'.format(args.command, args.cli_parameters, bundle_id))
        log.info('Print ConductR info with: {} info{}'.format(args.command, args.cli_parameters))
        log.info('Print bundle info with:   {} info{} {}'.format(args.command, args.cli_parameters, bundle_id))

    if not log.is_info_enabled() and log.is_quiet_enabled():
        log.quiet(response_json['bundleId'])

    return True


def open_bundle(bundle_file_name, bundle_file, bundle_conf):
    # The spec allows streaming from end to end but to reduce simplicity of implementation
    # for now we use a temp file. It is possible someday to increase efficiency here by
    # implementing a streaming zip library and http chunked responses to load this data right
    # into ConductR.

    bundle_open_file, digest = bundle_utils.digest_extract_and_open(bundle_file)

    if digest is None and bundle_file_name is None:
        raise MalformedBundleError('Unable to name bundle due to missing digest. '
                                   'Ensure file is produced with latest shazar')
    elif digest is not None:
        parsed_bundle_conf = ConfigFactory.parse_string(bundle_conf)

        if 'name' in parsed_bundle_conf:
            bundle_file_name = parsed_bundle_conf['name'] + '-' + digest[1] + '.zip'
        elif bundle_file_name is None:
            raise MalformedBundleError('Unable to name bundle. Add a "name" value to bundle.conf')

    return bundle_file_name, bundle_open_file


def create_multipart(log, files):
    encoder = MultipartEncoder(files)
    return MultipartEncoderMonitor(encoder, conduct_load_progress_monitor(log))


def conduct_load_progress_monitor(log):
    # The MultipartEncoderMonitor in the requests-toolbelt will invoke the callback once more after all data has been
    # uploaded.
    # Because of this, the upload_completed flag is required to ensure the callback is not called after all data has
    # been uploaded.
    # Without this flag, the scrollbar will progress until 100% as expected, and when it hits 100% the same scrollbar
    # will be printed twice.
    prev_time = 0.0
    upload_complete = False

    def continue_logging(monitor):
        nonlocal prev_time, upload_complete
        if not upload_complete:
            upload_complete = monitor.encoder.finished
            now_time = time.time()
            if upload_complete or now_time - prev_time >= 0.1:
                percent = 1.0 if upload_complete else monitor.bytes_read * 1.0 / monitor.len
                progress_bar_text = screen_utils.progress_bar(percent)
                log.progress(progress_bar_text, flush=upload_complete)
                prev_time = now_time

    return continue_logging


def string_io(input_text):
    return io.StringIO(input_text)


def cleanup_old_bundles(cache_dir, bundle_file_name, excluded):
    bundle_name_parts = bundle_file_name.split('-')
    # Remove digest, keeping only bundle name and tag
    bundle_name = '-'.join(bundle_name_parts[:-1])

    # List of bundle files having the same name and tag, sorted from oldest to latest.
    # This list excludes the file specified as `excluded`, and normally the `excluded` file is the recently loaded
    # bundle.
    older_bundle_files = sorted([
        file
        for file in glob.glob('{}/*.zip'.format(cache_dir))
        if os.path.isfile(file) and
        os.path.basename(file).startswith(bundle_name) and
        not is_same_path(file, excluded)
    ], key=lambda f: os.path.getmtime(f))

    bundle_files_to_delete = older_bundle_files[:(-1 * KEEP_BUNDLE_VERSIONS)]
    for file in bundle_files_to_delete:
        os.remove(file)


def is_same_path(a, b):
    return os.path.abspath(a) == os.path.abspath(b)
