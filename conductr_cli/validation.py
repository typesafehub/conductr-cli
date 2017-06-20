import dcos
import json
import logging
import urllib
import arrow
import platform
import socket

from pyhocon.exceptions import ConfigException
from requests import status_codes
from requests.exceptions import ConnectionError, HTTPError, ReadTimeout
from urllib.error import URLError
from zipfile import BadZipFile
from conductr_cli import screen_utils
from conductr_cli.exceptions import BindAddressNotFound, BundleScaleError, ConductrStartupError, \
    InstanceCountError, MalformedBundleError, BundleConfValidationError, \
    BintrayCredentialsNotFoundError, MalformedBintrayCredentialsError, BintrayResolutionError, \
    BintrayUnreachableError, BundleResolutionError, WaitTimeoutError, InsecureFilePermissions, \
    SandboxImageFetchError, SandboxImageNotFoundError, JavaCallError, HostnameLookupError, JavaUnsupportedVendorError, \
    JavaUnsupportedVersionError, JavaVersionParseError, DockerValidationError, SandboxImageNotAvailableOfflineError, \
    SandboxUnsupportedOsError, SandboxUnsupportedOsArchError, LicenseLoadError, LicenseDownloadError, NOT_FOUND_ERROR
from conductr_cli.resolvers import bintray_resolver, docker_offline_resolver, docker_resolver, offline_resolver, \
    stdin_resolver, uri_resolver


def connection_error(log, err, args):
    log.error('Unable to contact ConductR.')
    log.error('Reason: {}'.format(err.args[0]))
    if args.local_connection:
        log.error('Start the ConductR sandbox with: sandbox run IMAGE_VERSION')
    else:
        log.error('Make sure it can be accessed at {}'.format(err.request.url))


def pretty_json(s):
    s_json = json.loads(s)
    return json.dumps(s_json, sort_keys=True, indent=2, separators=(',', ': '))


def handle_connection_error(func):
    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ConnectionError as err:
            log = get_logger_for_func(func)
            connection_error(log, err, *args)
            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_http_error(func):
    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HTTPError as err:
            log = get_logger_for_func(func)
            log.error('{} {}'.format(err.response.status_code, err.response.reason))
            if err.response.text != '':
                log.error(err.response.text)
        except dcos.errors.DCOSHTTPException as err:
            log = get_logger_for_func(func)
            log.error(err)
            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_conductr_startup_error(func):
    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ConductrStartupError as err:
            log = get_logger_for_func(func)
            log.error('ConductR has not been started within {} seconds'.format(err.timeout))
            log.error('Set the env CONDUCTR_SANDBOX_WAIT_RETRIES to increase the wait timeout')
            if err.error_log_file:
                log.error('For more information check the ConductR log file at: {}'.format(err.error_log_file))
            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_invalid_config(func):
    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ConfigException as err:
            log = get_logger_for_func(func)
            log.error('Unable to parse bundle.conf.')
            log.error('{}.'.format(err.args[0]))
            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_no_file(func):
    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except urllib.error.HTTPError as err:
            log = get_logger_for_func(func)
            log.error('Resource not found: {}'.format(err.url))
            return False
        except URLError as err:
            log = get_logger_for_func(func)
            log.error('File not found: {}'.format(err.args[0]))
            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_bad_zip(func):
    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BadZipFile as err:
            log = get_logger_for_func(func)
            log.error('Problem with the bundle: {}'.format(err.args[0]))
            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_malformed_bundle(func):
    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except MalformedBundleError as err:
            log = get_logger_for_func(func)
            log.error('Problem with the bundle: {}'.format(err.args[0]))
            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_bundle_resolution_error(func):
    display_padding = 2

    resolver_display_name = {
        bintray_resolver: 'Bintray',
        docker_offline_resolver: 'Docker (Offline)',
        docker_resolver: 'Docker',
        offline_resolver: 'Offline',
        stdin_resolver: 'Stdin',
        uri_resolver: 'URI',
    }

    def get_resolver_display_name(resolver):
        return resolver_display_name[resolver] if resolver in resolver_display_name else resolver.__name__

    def display_errors(log, resolver_errors):
        if resolver_errors:
            data = [{'resolver_name': 'RESOLVER', 'error': 'ERROR'}]
            for entry in resolver_errors:
                (resolver, error) = entry
                data.append({
                    'resolver_name': get_resolver_display_name(resolver),
                    'error': '{}'.format(error)
                })
            column_widths = dict(screen_utils.calc_column_widths(data), **{'padding': ' ' * display_padding})

            for row in data:
                log.error('''\
{resolver_name: <{resolver_name_width}}{padding}\
{error: <{error_width}}'''.format(**dict(row, **column_widths)).rstrip())

    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BundleResolutionError as err:
            log = get_logger_for_func(func)

            log.error(err.value)

            if err.bundle_resolution_errors:
                display_errors(log, err.bundle_resolution_errors)

            elif err.cache_resolution_errors:
                display_errors(log, err.cache_resolution_errors)

            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_wait_timeout_error(func):
    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except WaitTimeoutError as err:
            log = get_logger_for_func(func)
            log.error('Timed out: {}'.format(err.args[0]))
            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_conduct_load_read_timeout_error(func):
    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ReadTimeout as err:
            log = get_logger_for_func(func)
            log.error('Timed out waiting for response from the server: {}'.format(err.args[0]))
            log.error('One possible issue may be that there are not enough resources or machines with the roles '
                      'that your bundle requires')
            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_insecure_file_permissions(func):
    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except InsecureFilePermissions as err:
            log = get_logger_for_func(func)
            log.error('File permissions are not secure: {}'.format(err.args[0]))
            log.error('Please choose a file where only the owner has access, e.g. 700')
            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def raise_for_status_inc_3xx(response):
    """
    raise status when status code is 3xx
    """

    response.raise_for_status()
    if response.status_code >= 300:
        raise HTTPError(status_codes._codes[response.status_code], response=response)  # FIXME: _codes is protected


def handle_instance_count_error(func):

    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except InstanceCountError as e:
            log = get_logger_for_func(func)
            log.error('Invalid number of containers {} '
                      'for ConductR version {}'.format(e.nr_of_containers, e.conductr_version))
            log.error(e.message)
            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_bind_address_not_found(func):

    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BindAddressNotFound as e:
            log = get_logger_for_func(func)
            log.info(e.message)
            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_sandbox_image_not_found_error(func):

    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SandboxImageNotFoundError as e:
            log = get_logger_for_func(func)
            log.error('Unable to fetch ConductR {} artifact {} from Bintray.'.format(e.component_type, e.image_version))
            log.error('Please specify a valid ConductR version.')
            log.error('The latest version can be found on: https://www.lightbend.com/product/conductr/developer')
            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_sandbox_image_fetch_error(func):

    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SandboxImageFetchError as e:
            log = get_logger_for_func(func)
            log.error('Failure to fetch ConductR {} artifact {} from Bintray.'.format(e.component_type, e.image_version))
            log.error('{}'.format(e.cause))
            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_sandbox_image_not_available_offline_error(func):

    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SandboxImageNotAvailableOfflineError as e:
            log = get_logger_for_func(func)
            log.error('ConductR {} is not available locally.'.format(e.image_version))
            log.error('Please run sandbox without --offline option to obtain the ConductR artefacts.')
            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_sandbox_unsupported_os_error(func):

    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SandboxUnsupportedOsError:
            log = get_logger_for_func(func)
            log.error('ConductR does not support {} operating system.'.format(platform.system()))
            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_sandbox_unsupported_os_arch_error(func):

    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SandboxUnsupportedOsArchError:
            log = get_logger_for_func(func)
            log.error('ConductR does not support {} architecture.'.format(platform.architecture()))
            log.error('Only 64-bit architecture is supported.')
            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_sandbox_restart_error(func):

    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except NOT_FOUND_ERROR:
            log = get_logger_for_func(func)
            log.error('ConductR cannot be restarted.')
            log.error('Please start ConductR first with: sandbox run')
            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_bintray_resolution_error(func):

    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BintrayResolutionError as e:
            log = get_logger_for_func(func)
            log.error(e.message)
            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_bintray_unreachable_error(func):

    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BintrayUnreachableError as e:
            log = get_logger_for_func(func)
            log.error('Artifact can not be resolved from Bintray.')
            log.error('It seems that Bintray is unreachable.')
            log.error('Please check your internet connection and try again.')
            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_bintray_credentials_error(func):

    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BintrayCredentialsNotFoundError as e:
            log = get_logger_for_func(func)
            log.error('Nearly there! The ConductR artifacts are hosted on private Bintray repository.')
            log.error('It is therefore necessary to create a Bintray credentials file at {}'
                      .format(e.credential_file_path))
            log.error('For more information how to setup the Lightbend Bintray credentials please follow:')
            log.error('  http://developers.lightbend.com/docs/reactive-platform/2.0/setup/setup-sbt.html')
            return False
        except MalformedBintrayCredentialsError as e:
            log = get_logger_for_func(func)
            log.error('Malformed Bintray credentials in {}'.format(e.credential_file_path))
            log.error('Please follow the instructions to setup the Lightbend Bintray credentials:')
            log.error('  http://developers.lightbend.com/docs/reactive-platform/2.0/setup/setup-sbt.html')
            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_jvm_validation_error(func):

    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except JavaCallError as e:
            log = get_logger_for_func(func)
            log.error('Unable to obtain java version.')
            log.error(e.message)
            log.error('Please ensure Oracle or OpenJDK JVM 1.8 and above is installed.')
            return False
        except JavaUnsupportedVendorError as e:
            log = get_logger_for_func(func)
            log.error('Unsupported JVM vendor: {}'.format(e.vendor))
            log.error('Please ensure Oracle or OpenJDK JVM 1.8 and above is installed.')
            return False
        except JavaUnsupportedVersionError as e:
            log = get_logger_for_func(func)
            log.error('Unsupported JVM version: {}'.format(e.jvm_version))
            log.error('Please ensure Oracle or OpenJDK JVM 1.8 and above is installed.')
            return False
        except JavaVersionParseError as e:
            log = get_logger_for_func(func)
            log.error('Unable to obtain java version from the `java -version` command.')
            log.error('Please ensure Oracle or OpenJDK JVM 1.8 and above is installed.')
            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_hostname_lookup_error(func):

    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HostnameLookupError:
            machine_hostname = socket.gethostname()

            log = get_logger_for_func(func)
            log.error('\n\tUnfortunately, because of a known Java 8 issue on macOS,'
                      '\n\thostname lookups on your machine will take more than 5 seconds.'
                      '\n\n\tThis will prevent ConductR from starting.'
                      '\n\n\tFortunately, there is an easy, quick fix. Just add \'{}\' to your /etc/hosts file. e.g.:'
                      '\n\n\t\t127.0.0.1   localhost {}'
                      '\n\t\t::1         localhost {}'
                      '\n\n\tNote that you will need to use sudo to edit the /etc/hosts file.'
                      '\n\tUse your favorite editor to do this e.g. \'sudo vi /etc/hosts\''
                      '\n\n\tTo learn more about the Java 8 issue: http://stackoverflow.com/questions/39636792/'
                      'jvm-takes-a-long-time-to-resolve-ip-address-for-localhost'
                      '\n'.format(machine_hostname, machine_hostname, machine_hostname))
            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_docker_validation_error(func):

    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DockerValidationError as e:
            log = get_logger_for_func(func)
            for message in e.messages:
                log.error(message)
            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_license_load_error(func):

    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except LicenseLoadError as e:
            log = get_logger_for_func(func)
            log.error('Error loading license into ConductR')
            log.error(e.message)
            log.error('Use `conduct load-license -f` to re-download your license.')
            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_license_download_error(func):

    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except LicenseDownloadError as e:
            log = get_logger_for_func(func)
            for message in e.messages:
                log.error(message)
            log.error('Use `conduct load-license -f` to re-download your license.')
            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_bndl_create_error(func):
    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ValueError, SyntaxError) as e:
            log = get_logger_for_func(func)
            log.error('bndl: {}'.format(e))
            return 2
        except BundleConfValidationError as e:
            log = get_logger_for_func(func)
            log.error('bndl: bundle.conf validation errors: \n  {}'.format('\n  '.join(e.messages)))
            return 1

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def handle_bundle_scale_error(func):
    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BundleScaleError:
            return False

    # Do not change the wrapped function name,
    # so argparse configuration can be tested.
    handler.__name__ = func.__name__

    return handler


def format_timestamp(timestamp, args):
    date = arrow.get(timestamp)
    date_display = date.to('UTC') if args.utc else date.to('local')
    date_format = '%a %Y-%m-%dT%H:%M:%SZ' if args.utc else '%a %Y-%m-%dT%H:%M:%S%z'
    return date_display.strftime(date_format)


def get_logger_for_func(func):
    return logging.getLogger('conductr_cli.{}'.format(func.__name__))


def argparse_version(value):
    import argparse
    import re

    if re.match("^[0-9]+([.][0-9]+)*(\\-[a-z]+\\.[0-9]+)?$", value):
        return value

    raise argparse.ArgumentTypeError("'%s' is not a valid version number" % value)
