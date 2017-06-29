from conductr_cli import conduct_main, host, license_validation, pyinstaller_info, sandbox_stop, sandbox_common, \
    sandbox_version
from conductr_cli.constants import DEFAULT_SCHEME, DEFAULT_PORT, DEFAULT_BASE_PATH, DEFAULT_API_VERSION, \
    DEFAULT_LICENSE_FILE, DEFAULT_SERVICE_LOCATOR_PORT, FEATURE_PROVIDE_PROXYING, DEFAULT_SANDBOX_IMAGE_DIR
from conductr_cli.exceptions import BindAddressNotFound, BintrayUnreachableError, InstanceCountError, \
    SandboxImageFetchError, SandboxImageNotFoundError, SandboxImageNotAvailableOfflineError, \
    SandboxUnsupportedOsArchError, SandboxUnsupportedOsError, JavaCallError, JavaUnsupportedVendorError, \
    JavaUnsupportedVersionError, JavaVersionParseError, HostnameLookupError, LicenseValidationError
from conductr_cli.resolvers import bintray_resolver
from conductr_cli.resolvers.bintray_resolver import BINTRAY_API_BASE_URL, BINTRAY_LIGHTBEND_ORG, \
    BINTRAY_CONDUCTR_COMMERCIAL_REPO, BINTRAY_CONDUCTR_GENERIC_REPO, BINTRAY_CONDUCTR_CORE_PACKAGE_NAME
from conductr_cli.sandbox_common import flatten
from conductr_cli.sandbox_version import is_conductr_on_private_bintray
from conductr_cli.screen_utils import h1, h2
from requests.exceptions import HTTPError, ConnectionError
from subprocess import CalledProcessError
from urllib.error import URLError

import glob
import json
import logging
import os
import re
import requests
import semver
import shutil
import subprocess


NR_OF_INSTANCE_EXPRESSION = '[0-9]+\\:[0-9]+'
BIND_TEST_PORT = 19991  # The port used for testing if an address can be bound.
CONDUCTR_AKKA_REMOTING_PORT = 9004  # The port used by ConductR's Akka remoting.
NR_OF_PROXY_INSTANCE = 1  # Only run 1 instance of ConductR HAProxy since there's only one HAProxy running per machine.
SUPPORTED_JVM_VENDOR = ["java", "openjdk"]  # Oracle JVM vendor is `java`, OpenJDK is `openjdk`
SUPPORTED_JVM_VERSION = (1, 8)  # Supports JVM version 1.8 and above.


class SandboxRunResult:
    def __init__(self,
                 core_pids, core_addrs, agent_pids, agent_addrs,
                 wait_for_conductr, license_validation_error,
                 sandbox_upgrade_requirements):
        self.core_pids = core_pids
        self.core_addrs = core_addrs
        self.agent_pids = agent_pids
        self.agent_addrs = agent_addrs
        self.host = str(core_addrs[0])
        self.wait_for_conductr = wait_for_conductr
        self.conductr_log_file = '{}/core/logs/conductr.log'.format(DEFAULT_SANDBOX_IMAGE_DIR)
        self.license_validation_error = license_validation_error
        self.sandbox_upgrade_requirements = sandbox_upgrade_requirements

    scheme = DEFAULT_SCHEME
    port = DEFAULT_PORT
    base_path = DEFAULT_BASE_PATH
    api_version = DEFAULT_API_VERSION

    def __eq__(self, other):
        return self.__dict__ == other.__dict__ if isinstance(other, self.__class__) else False


class SandboxUpgradeRequirement:
    def __init__(self, is_upgrade_required, current_version, latest_version):
        self.is_upgrade_required = is_upgrade_required
        self.current_version = current_version
        self.latest_version = latest_version

    def __eq__(self, other):
        return self.__dict__ == other.__dict__ if isinstance(other, self.__class__) else False


class WaitForConductrArgs:
    def __init__(self, core_addr):
        self.host = str(core_addr)
        self.conductr_log_file = '{}/core/logs/conductr.log'.format(DEFAULT_SANDBOX_IMAGE_DIR)

    scheme = DEFAULT_SCHEME
    port = DEFAULT_PORT
    base_path = DEFAULT_BASE_PATH
    api_version = DEFAULT_API_VERSION

    def __eq__(self, other):
        return self.__dict__ == other.__dict__ if isinstance(other, self.__class__) else False


def run(args, features):
    """
    Starts the ConductR core and agent.

    :param args: args parsed from the input arguments
    :param features: list of features which are specified via -f switch.
                     This is only relevant for Docker based sandbox since the features decides what port to expose
    :return: SandboxRunResult
    """
    nr_of_core_instances, nr_of_agent_instances = instance_count(args.image_version, args.nr_of_instances)

    validate_jvm_support()
    validate_hostname_lookup()
    validate_64bit_support()
    validate_bintray_credentials(args.image_version, args.offline_mode)

    sandbox_stop.stop(args)

    log = logging.getLogger(__name__)
    log.info(h1('Starting ConductR'))

    cleanup_tmp_dir(args.tmp_dir)

    bind_addrs = find_bind_addrs(max(nr_of_core_instances, nr_of_agent_instances), args.addr_range)

    core_extracted_dir, agent_extracted_dir, sandbox_upgrade_requirements = obtain_sandbox_image(args.image_dir,
                                                                                                 args.image_version,
                                                                                                 args.offline_mode)

    core_addrs = bind_addrs[0:nr_of_core_instances]
    core_pids = start_core_instances(core_extracted_dir,
                                     args.tmp_dir,
                                     args.envs,
                                     args.envs_core,
                                     args.args,
                                     args.args_core,
                                     core_addrs,
                                     args.conductr_roles,
                                     features,
                                     args.log_level)

    sandbox_common.wait_for_start(WaitForConductrArgs(core_addrs[0]))

    license_validation_error = None
    try:
        license_validation.validate_license(args.image_version,
                                            core_addrs[0],
                                            nr_of_agent_instances,
                                            DEFAULT_LICENSE_FILE)
    except LicenseValidationError as e:
        license_validation_error = e

    agent_addrs = bind_addrs[0:nr_of_agent_instances]
    agent_pids = start_agent_instances(agent_extracted_dir,
                                       args.tmp_dir,
                                       args.envs,
                                       args.envs_agent,
                                       args.args,
                                       args.args_agent,
                                       bind_addrs[0:nr_of_agent_instances],
                                       core_addrs,
                                       args.conductr_roles,
                                       features,
                                       args.log_level)
    return SandboxRunResult(core_pids, core_addrs, agent_pids, agent_addrs,
                            wait_for_conductr=False,
                            license_validation_error=license_validation_error,
                            sandbox_upgrade_requirements=sandbox_upgrade_requirements)


def log_run_attempt(args, run_result, feature_results, feature_provided):
    """
    Logs the run attempt. This method will be called after the completion of run method and when all the features has
    been started.

    :param args: args parsed from the input arguments
    :param run_result: the result from calling sandbox_run_jvm.run() - instance of sandbox_run_jvm.SandboxRunResult
    :param feature_results: the feature result
    :param feature_provided: the values provided by all started features
    :return:
    """
    log = logging.getLogger(__name__)
    log.info(h1('Summary'))
    log.info(h2('ConductR'))
    log.info('ConductR has been started:')
    plural_core = 's' if len(run_result.core_addrs) > 1 else ''
    log.info('  core instance{} on {}'.format(plural_core, ', '.join(str(i) for i in run_result.core_addrs)))
    plural_agent = 's' if len(run_result.agent_addrs) > 1 else ''
    log.info('  agent instance{} on {}'.format(plural_agent, ', '.join(str(i) for i in run_result.agent_addrs)))
    log.info('ConductR service locator has been started on:')
    log.info('  {}:{}'.format(run_result.host, DEFAULT_SERVICE_LOCATOR_PORT))

    log.info(h2('Proxy'))
    if FEATURE_PROVIDE_PROXYING in feature_provided:
        log.info('HAProxy has been started')
        log.info('By default, your bundles are accessible on:')
        log.info('  {}:{}'.format(run_result.host, args.bundle_http_port))
    else:
        log.info('HAProxy has not been started')
        log.info('To enable proxying ensure Docker is running and restart the sandbox')

    if feature_results:
        log.info(h2('Features'))
        log.info('The following feature related bundles have been started:')
        for feature_result in feature_results:
            if FEATURE_PROVIDE_PROXYING in feature_provided:
                uri = '{}:{}'.format(run_result.host, feature_result.port)
            else:
                uri = '{}:{}/services/{}'.format(run_result.host, DEFAULT_SERVICE_LOCATOR_PORT,
                                                 feature_result.name)
            log.info('  {} on {}'.format(feature_result.name, uri))

    log.info(h2('Bundles'))
    log.info('Check latest bundle status with:')
    log.info('  conduct info')
    log.info('Current bundle status:')
    conduct_main.run(['info', '--host', run_result.host], configure_logging=False)

    if run_result.license_validation_error:
        for message in run_result.license_validation_error.messages:
            log.warning(message)

    elif run_result.sandbox_upgrade_requirements and run_result.sandbox_upgrade_requirements.is_upgrade_required:
        def format_version(version_info):
            return semver.format_version(version_info.major,
                                         version_info.minor,
                                         version_info.patch,
                                         version_info.prerelease,
                                         version_info.build)

        upgrade_requirements = run_result.sandbox_upgrade_requirements
        latest_version_str = format_version(upgrade_requirements.latest_version)
        log.info('')
        log.warning('A newer ConductR version is available. '
                    'Please upgrade the sandbox to {} by running'.format(latest_version_str))
        log.warning('  sandbox run {}'.format(latest_version_str))


def instance_count(image_version, instance_expression):
    """
    Parses the instance expressions into number of core and agent instances, i.e.

    The expression `2` translates to 1 core instance and 2 agent instances.
    The expression `2:3` translates to 2 core instances and 3 agent instances.

    :param image_version:
    :param instance_expression:
    :return: a tuple containing number of core instances and number of agent instances.
    """
    try:
        nr_of_instances = int(instance_expression)
        return 1, nr_of_instances
    except ValueError:
        match = re.search(NR_OF_INSTANCE_EXPRESSION, instance_expression)
        if match:
            parts = instance_expression.split(':')
            nr_of_core_instances = int(parts[0])
            nr_of_agent_instances = int(parts[-1])
            return nr_of_core_instances, nr_of_agent_instances
        else:
            raise InstanceCountError(image_version,
                                     instance_expression,
                                     'Number of containers must be an integer or '
                                     'a valid instance expression, i.e. 2:3 '
                                     'which translates to 2 core instances and 3 agent instances')


def validate_jvm_support():
    """
    Validates for the presence of supported JVM (i.e. Oracle or OpenJDK JVM 8),
    else raise an exception to fail the sandbox run.
    """
    try:
        raw_output = subprocess.getoutput('java -version')
        lines = raw_output.splitlines()

        parts = None

        for line in lines:
            maybe_parts = line.split(' ')

            if len(maybe_parts) == 3 and maybe_parts[1] == 'version':
                parts = maybe_parts

        if parts is not None:
            jvm_vendor = parts[0]

            if jvm_vendor in SUPPORTED_JVM_VENDOR:
                jvm_version = parts[2].replace('"', '')
                jvm_version_parts = jvm_version.split('.')
                if len(jvm_version_parts) >= 2:
                    jvm_version_major = int(jvm_version_parts[0])
                    jvm_version_minor = int(jvm_version_parts[1])
                    jvm_version_tuple = (jvm_version_major, jvm_version_minor)

                    if jvm_version_tuple >= SUPPORTED_JVM_VERSION:
                        return
                    else:
                        raise JavaUnsupportedVersionError(jvm_version)
            else:
                raise JavaUnsupportedVendorError(jvm_vendor)

        raise JavaVersionParseError(raw_output)
    except CalledProcessError:
        raise JavaCallError('Failure calling `java -version`')


def validate_hostname_lookup():
    """
    Validates if the hostname lookup by Java is slow given the issue https://github.com/akka/akka/issues/22160
    Validation fails if the hostname is not part of at least one localhost entry in the /etc/hosts file
    and the OS is macOS.
    A HostnameLookupError is raised if the validation fails
    """
    if host.is_macos():
        with open('/etc/hosts', 'r') as file:
            hostname = host.hostname()
            lines = [line.split('#')[0] for line in file.readlines() if not line.strip().startswith('#')]
            localhost_lines = [line for line in lines if 'localhost' in line]
            if not any(hostname in words for words in (line.split() for line in localhost_lines)):
                raise HostnameLookupError()


def validate_64bit_support():
    """
    Validates if current machine that's running the Sandbox is 64-bit,
    else raise an exception to fail the sandbox run.
    """
    if not host.is_64bit():
        raise SandboxUnsupportedOsArchError()


def validate_bintray_credentials(image_version, offline_mode):
    """
    Validates if the necessary Bintray credentials exists to start the ConductR cluster.
    Credentials are necessary prior to ConductR 2.1.0. From onwards 2.1.0, no credentials are needed.
    :param image_version: the ConductR image version
    :param offline_mode: the offline mode flag
    """
    if not offline_mode and is_conductr_on_private_bintray(image_version):
        bintray_resolver.load_bintray_credentials(raise_error=True, disable_instructions=True)


def cleanup_tmp_dir(tmp_dir):
    """
    Clears the content of the sandbox tmp dir
    """
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)

    os.makedirs(tmp_dir, exist_ok=True)


def find_bind_addrs(nr_of_addrs, addr_range):
    """
    Finds for the presence of address which can be bound to the sandbox given an address range, i.e.
    - Let's say 3 address aliases is required.
    - The address range is 192.168.128.0/24

    These addresses requires setup using ifconfig as such (macOS example):

    sudo ifconfig lo0 alias 192.168.128.1 255.255.255.255
    sudo ifconfig lo0 alias 192.168.128.2 255.255.255.255
    sudo ifconfig lo0 alias 192.168.128.3 255.255.255.255

    This command will check if 192.168.128.1, 192.168.128.2, and 192.168.128.3 can be bound. The check is done by
    binding a socket to each of these address using a test port.

    If the number of required address is not present, prompt the user for sudo password so that we can add the aliases.

    :param nr_of_addrs: number of address aliases required
    :param addr_range: the range of address which is available to core and agent to bind to.
                       The address is specified in the CIDR format, i.e. 192.168.128.0/24
    """

    addrs_to_bind = []
    addrs_unavailable = []
    for ip_addr in addr_range.hosts():
        if host.can_bind(ip_addr, BIND_TEST_PORT):
            addrs_to_bind.append(ip_addr)
        else:
            addrs_unavailable.append(ip_addr)

        if len(addrs_to_bind) >= nr_of_addrs:
            break

    if len(addrs_to_bind) < nr_of_addrs:
        nr_of_addr_setup = nr_of_addrs - len(addrs_to_bind)
        addr_aliases_commands = host.addr_alias_commands(addrs_unavailable[0:nr_of_addr_setup],
                                                         addr_range.version)
        if addr_aliases_commands:
            log = logging.getLogger(__name__)
            log.info('Network address aliases are required so that the sandbox can operate as a cluster of machines.'
                     '\nTo add the network aliases sudo privileges are required.')
            for command in addr_aliases_commands:
                try:
                    subprocess.check_call(command)
                    log.info(' '.join(command))
                except CalledProcessError:
                    commands_str = '\n'.join([' '.join(command) for command in addr_aliases_commands])
                    raise BindAddressNotFound('Not able to add the network address aliases. Please add them manually:'
                                              '\n\n{}'.format(commands_str))
            return find_bind_addrs(nr_of_addrs, addr_range)
        else:
            subnet_mask = host.get_subnet_mask(addr_range.version)
            addrs_formatted = ', '.join(['{}'.format(addr) for addr in addrs_unavailable[0:nr_of_addr_setup]])
            setup_instructions = 'Setup aliases for {} addresses with {} subnet mask'.format(addrs_formatted,
                                                                                             subnet_mask)
            raise BindAddressNotFound(setup_instructions)
    else:
        return addrs_to_bind


def obtain_sandbox_image(image_dir, image_version, offline_mode):
    """
    Obtains the sandbox image.

    The sandbox image is the .tgz binary of ConductR core and agent which is available as a download from Bintray.

    First the local cache is interrogated for the presence of the .tgz binary.

    If the binary is not yet available within the local cache, then it will be downloaded from Bintray. If the binary
    is present within the local cache, they will be used instead.

    The core binary will be expanded into the `${image_dir}/core`. The directory `${image_dir}/core` will be emptied
    before the binary is expanded.

    Similarly, the agent binary will be expanded into the `${image_dir}/agent`. The directory `${image_dir}/agent` will
    be emptied before the binary is expanded.

    Once this is done, upgrade requirement is then checked. Upgrade is deemed to be required if:
    - There is newer image having same Semver major and minor version as the currently run image, and
    - The newer image is not yet downloaded.

    Upgrade requirement check will be disabled if the offline mode is enabled.

    :param image_dir: the directory where ConductR core and agent binaries will be cached, also the base directory
                      containing the expanded ConductR core and agent binaries.
    :param image_version: the version of the sandbox to be downloaded.
    :param offline_mode: sets to `True` if sandbox is operating in the offline mode.
                         The offline mode means no network, and hence attempt to download new sandbox image will result
                         in an error being raised.
    :return: the pair containing path to the expanded core directory and path to the expanded agent directory
    """
    def resolve_binaries():
        """
        Resolves ConductR binaries given the `${bintray_package_name}` and `${image_version}`.
        First, the core and agent binaries are resolved from the `${image_dir}` cache directory. If not available,
        the binaries are downloaded from Bintray.

        The artifacts are available under the following Bintray repo:

        https://bintray.com/lightbend/commercial-releases/`${bintray_package_name}`

        As part of the download:
        - A progress bar will be displayed.
        - The download will be saved into `${image_dir}/${filename}.tgz.tmp`.
        Once download is complete, this file will be moved to `${image_dir}/${filename}.tgz`.

        Once downloaded, the binaries are cached in `${image_dir}`.

        Once image is resolved, upgrade requirement check will be performed unless sandbox offline mode is enabled.

        :return: tuple of (core_path, agent_path, sandbox_upgrade_requirements)
        """
        bintray_auth = bintray_resolver.load_bintray_credentials(raise_error=False)

        core_path = resolve_binary_from_cache(image_dir, 'conductr', image_version)
        agent_path = resolve_binary_from_cache(image_dir, 'conductr-agent', image_version)

        if (not core_path) or (not agent_path):
            if offline_mode:
                raise SandboxImageNotAvailableOfflineError(image_version)
            else:
                if not core_path:
                    core_path = download_sandbox_image(bintray_auth, image_dir,
                                                       package_name=core_info['bintray_package_name'],
                                                       artefact_type=core_info['type'],
                                                       image_version=image_version)

                if not agent_path:
                    agent_path = download_sandbox_image(bintray_auth, image_dir,
                                                        package_name=agent_info['bintray_package_name'],
                                                        artefact_type=agent_info['type'],
                                                        image_version=image_version)

        upgrade_requirements = None if offline_mode else check_upgrade_requirements(bintray_auth,
                                                                                    image_dir,
                                                                                    image_version)

        return core_path, agent_path, upgrade_requirements

    def extract_binary(path, conductr_info):
        """
        The binary will be expanded into the `${extraction_dir}`.
        The directory `${extraction_dir}` will be emptied before the binary is expanded.

        :param path: the path to the core binary to be expanded.
        :param conductr_info: the information of the ConductR universal binary
        :return: path to the directory containing expanded core binary.
        """
        log = logging.getLogger(__name__)
        extraction_dir = conductr_info['extraction_dir']
        if os.path.exists(extraction_dir):
            shutil.rmtree(extraction_dir)
        os.makedirs(extraction_dir, mode=0o700)
        log.info('Extracting ConductR {} to {}'.format(conductr_info['type'], extraction_dir))
        shutil.unpack_archive(path, extraction_dir)
        top_level_archive_dir = os.listdir(extraction_dir)[0]
        extraction_subdir = '{}/{}'.format(extraction_dir, top_level_archive_dir)
        for filename in os.listdir(extraction_subdir):
            shutil.move('{}/{}'.format(extraction_subdir, filename), '{}/{}'.format(extraction_dir, filename))
        os.rmdir(extraction_subdir)
        return extraction_dir

    core_info, agent_info = sandbox_common.resolve_conductr_info(image_dir)

    core_binary_path, agent_binary_path, sandbox_upgrade_requirements = resolve_binaries()

    core_extracted_dir = extract_binary(core_binary_path, core_info)
    agent_extracted_dir = extract_binary(agent_binary_path, agent_info)

    return core_extracted_dir, agent_extracted_dir, sandbox_upgrade_requirements


def download_sandbox_image(bintray_auth, image_dir, package_name, artefact_type, image_version):
    try:
        if sandbox_version.is_conductr_on_private_bintray(image_version):
            bintray_repo = BINTRAY_CONDUCTR_COMMERCIAL_REPO
        else:
            bintray_repo = BINTRAY_CONDUCTR_COMMERCIAL_REPO if bintray_auth[0] else BINTRAY_CONDUCTR_GENERIC_REPO

        if artefact_type == 'core':
            file_prefix = 'conductr-{}-{}'.format(image_version, artefact_os_name())
        else:
            file_prefix = 'conductr-agent-{}-{}'.format(image_version, artefact_os_name())

        def is_matching_artefact(download_url):
            artefact_file_name = os.path.basename(download_url)
            return artefact_file_name.startswith(file_prefix) and artefact_file_name.endswith('64.tgz')

        artefacts = [
            artefact
            for artefact in bintray_resolver.bintray_artefacts_by_version(bintray_auth,
                                                                          BINTRAY_LIGHTBEND_ORG,
                                                                          bintray_repo,
                                                                          package_name,
                                                                          image_version)
            if is_matching_artefact(artefact['download_url'])
        ]
        if len(artefacts) == 1:
            is_success, _, download_path, _ = bintray_resolver.bintray_download_artefact(image_dir,
                                                                                         artefacts[0],
                                                                                         bintray_auth,
                                                                                         raise_error=True)

            if is_success:
                return download_path

        raise SandboxImageNotFoundError(artefact_type, image_version)
    except ConnectionError:
        raise BintrayUnreachableError('Bintray is unreachable.')

    except HTTPError as e:
        if e.response.status_code == 404:
            raise SandboxImageNotFoundError(artefact_type, image_version)
        else:
            raise SandboxImageFetchError(artefact_type, image_version, e)

    except URLError as e:
        raise SandboxImageFetchError(artefact_type, image_version, e)


def check_upgrade_requirements(bintray_auth, image_dir, image_version):
    def get_major_minor_patch(version_info):
        return version_info.major, version_info.minor, version_info.patch

    try:
        if sandbox_version.is_conductr_on_private_bintray(image_version):
            bintray_repo = BINTRAY_CONDUCTR_COMMERCIAL_REPO
        else:
            bintray_repo = BINTRAY_CONDUCTR_COMMERCIAL_REPO if bintray_auth[0] else BINTRAY_CONDUCTR_GENERIC_REPO

        latest_version_url = '{}/packages/{}/{}/{}'.format(BINTRAY_API_BASE_URL,
                                                           BINTRAY_LIGHTBEND_ORG,
                                                           bintray_repo,
                                                           BINTRAY_CONDUCTR_CORE_PACKAGE_NAME)
        if bintray_auth[0]:
            _, bintray_username, bintray_password = bintray_auth
            response = requests.get(latest_version_url, auth=(bintray_username, bintray_password))
        else:
            response = requests.get(latest_version_url)

        response.raise_for_status()
        json_response = json.loads(response.text)
        all_versions = [semver.parse_version_info(version) for version in json_response['versions']]

        current_version = semver.parse_version_info(image_version)
        applicable_versions = sorted(
            [v for v in all_versions if v.major == current_version.major and v.minor == current_version.minor],
            key=get_major_minor_patch)

        if len(applicable_versions) > 0:
            latest_version = applicable_versions[-1]
            latest_version_str = semver.format_version(latest_version.major, latest_version.minor, latest_version.patch)
            is_upgrade_required = current_version < latest_version and \
                resolve_binary_from_cache(image_dir, 'conductr', latest_version_str) is None
            return SandboxUpgradeRequirement(is_upgrade_required=is_upgrade_required,
                                             current_version=current_version,
                                             latest_version=latest_version)

        return None
    except (ConnectionError, HTTPError, URLError):
        # Ignore problem checking upgrade requirement as it's not mandatory when starting sandbox.
        return None


def start_core_instances(core_extracted_dir, tmp_dir,
                         envs, envs_core,
                         args, args_core,
                         bind_addrs, conductr_roles, features, log_level):
    """
    Starts the ConductR core process.

    Each instance is allocated an address to be bound based on the address range. For example:
    - Given 3 required core instances
    - Given the address range input of 192.168.128.0/24
    - The instances will be allocated these addresses: 192.168.128.1, 192.168.128.2, 192.168.128.3

    :param core_extracted_dir: the directory containing the files expanded from core's binary .tgz
    :param tmp_dir: temp directory for ConductR core process.
    :param envs: environment variables declared for both with ConductR core and agent process.
    :param envs_core: environment variables declared for ConductR core process.
    :param args: input arguments for both with ConductR core and agent process.
    :param args_core: input arguments for ConductR core process.
    :param bind_addrs: a list of addresses which the core instances will bind to.
                       If there are 3 instances of core required, there will be 3 addresses supplied.
    :param conductr_roles: list of roles specified by the end user.
    :param features: list of features which needs to be started.
                     This method won't start the feature, but will ensure arguments from the feature flags will be
                     passed to the process accordingly
    :param log_level: the log level of the ConductR core process.
    :return: the pids of the core instances.
    """
    log = logging.getLogger(__name__)

    pids = []

    for f in features:
        f.conductr_pre_core_start(envs,
                                  envs_core,
                                  args,
                                  args_core,
                                  core_extracted_dir,
                                  bind_addrs,
                                  conductr_roles)

    feature_conductr_roles = flatten([f.conductr_roles() for f in features])
    # Role matching is enabled if there's role present for any of the ConductR agent instances.
    # We will check the first instance of the ConductR agent since it's where the bundles from feature flags
    # will be executing from.
    roles_enabled = len(sandbox_common.resolve_conductr_roles_by_instance(conductr_roles,
                                                                          feature_conductr_roles, 0)) > 0

    args_feature = flatten([f.conductr_args() for f in features])
    feature_envs = flatten([f.conductr_core_envs() for f in features])
    process_envs = merge_with_os_envs(feature_envs, envs, envs_core)

    for idx, bind_addr in enumerate(bind_addrs):
        commands = [
            '{}/bin/conductr'.format(core_extracted_dir),
            '-Djava.io.tmpdir={}'.format(tmp_dir),
            '-Dakka.loglevel={}'.format(log_level),
            '-Dconductr.ip={}'.format(bind_addr),
            '-Dconductr.resource-provider.match-offer-roles={}'.format('on' if roles_enabled else 'off')
        ]
        if args:
            commands.extend(args)
        if args_core:
            commands.extend(args_core)
        if args_feature:
            commands.extend(args_feature)
        if idx > 0:
            commands.extend([
                '--seed',
                '{}:{}'.format(bind_addrs[0], CONDUCTR_AKKA_REMOTING_PORT)
            ])

        log.info('Starting ConductR core instance on {}..'.format(bind_addr))
        pid = subprocess.Popen(commands,
                               cwd=core_extracted_dir,
                               start_new_session=True,
                               stdout=subprocess.DEVNULL,
                               stdin=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL,
                               env=process_envs).pid
        pids.append(pid)
    return pids


def start_agent_instances(agent_extracted_dir, tmp_dir,
                          envs, envs_agent,
                          args, args_agent,
                          bind_addrs, core_addrs, conductr_roles, features, log_level):
    """
    Starts the ConductR agent process.

    Each instance is allocated an address to be bound based on the address range. For example:
    - Given 3 required agent instances
    - Given the address range input of 192.168.128.0/24
    - The instances will be allocated these addresses: 192.168.128.1, 192.168.128.2, 192.168.128.3

    :param agent_extracted_dir: the directory containing the files expanded from agent's binary .tgz
    :param tmp_dir: temp dir for ConductR agent directory.
    :param envs: environment variables declared for both with ConductR core and agent process.
    :param envs_agent: environment variables declared for ConductR agent process.
    :param args: input arguments declared for both with ConductR core and agent process.
    :param args_agent: input arguments declared for ConductR agent process.
    :param bind_addrs: a list of addresses which the core instances will bind to.
                       If there are 3 instances of core required, there will be 3 addresses supplied.
    :param conductr_roles: list of roles specified by the end user.
    :param features: list of features which needs to be started.
                     This method won't start the feature, but if the roles is enabled (i.e. specified by the end user)
                     the agent must have correct roles assigned in order for features to be started correctly.
                     This method will also ensure extra arguments from the features are being passed into the agent
                     process.
    :param log_level: the log level of the ConductR agent process
    :return: the pids of the agent instances.
    """
    log = logging.getLogger(__name__)
    pids = []

    for f in features:
        f.conductr_pre_agent_start(envs,
                                   envs_agent,
                                   args,
                                   args_agent,
                                   agent_extracted_dir,
                                   bind_addrs,
                                   core_addrs,
                                   conductr_roles)

    feature_conductr_roles = flatten([f.conductr_roles() for f in features])
    args_features = flatten([f.conductr_args() for f in features])
    feature_envs = flatten([f.conductr_agent_envs() for f in features])
    process_envs = merge_with_os_envs(feature_envs, envs, envs_agent)

    for idx, bind_addr in enumerate(bind_addrs):
        core_addr = core_addrs[idx] if len(core_addrs) > idx else core_addrs[0]
        agent_roles = sandbox_common.resolve_conductr_roles_by_instance(conductr_roles,
                                                                        feature_conductr_roles, idx)

        commands = [
            '{}/bin/conductr-agent'.format(agent_extracted_dir),
            '-Djava.io.tmpdir={}'.format(tmp_dir),
            '-Dakka.loglevel={}'.format(log_level),
            '-Dconductr.agent.ip={}'.format(bind_addr),
            '--core-node',
            '{}:{}'.format(core_addr, CONDUCTR_AKKA_REMOTING_PORT)
        ] + [
            '-Dconductr.agent.roles.{}={}'.format(j, role) for j, role in enumerate(agent_roles)
        ]

        if args:
            commands.extend(args)
        if args_agent:
            commands.extend(args_agent)
        if args_features:
            commands.extend(args_features)

        log.info('Starting ConductR agent instance on {}..'.format(bind_addr))
        pid = subprocess.Popen(commands,
                               cwd=agent_extracted_dir,
                               start_new_session=True,
                               stdout=subprocess.DEVNULL,
                               stdin=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL,
                               env=process_envs).pid
        pids.append(pid)
    return pids


def artefact_os_name():
    if host.is_macos():
        return 'Mac_OS_X'
    elif host.is_linux():
        return 'Linux'
    else:
        raise SandboxUnsupportedOsError()


def merge_with_os_envs(*args):
    envs_to_override = [v for list in args for v in list]

    result = os.environ.copy()
    pyinstaller_base_path = pyinstaller_info.sys_meipass()
    if pyinstaller_base_path:
        result = remove_path_from_env(result, 'PATH', pyinstaller_base_path)
        result = remove_path_from_env(result, 'LD_LIBRARY_PATH', pyinstaller_base_path)

    if envs_to_override:
        for env in envs_to_override:
            if '=' in env:
                env_split = env.split('=', 1)
                key = env_split[0]
                value = env_split[-1]
                result.update({key: value})

    return result


def remove_path_from_env(env, key, path_to_remove):
    result = env.copy()

    if key in env:
        paths = env[key].split(':')
        paths_cleaned = [path for path in paths if path != path_to_remove]
        if len(paths_cleaned) > 0:
            result.update({key: ':'.join(paths_cleaned)})
        else:
            del result[key]

    return result


def resolve_binary_from_cache(image_dir, file_prefix, image_version):
    """
    Checks for the presence of the ConductR binary in the cache directory.

    :param image_dir: the directory where image will be stored.
    :param file_prefix: either `conductr` or `conductr-agent`.
    :param image_version: the version of the ConductR to be checked.
    :return: If present, return the path to the binary file, else return None.
    """

    binaries = glob.glob('{}/{}-{}-{}-*64.tgz'.format(image_dir, file_prefix, image_version, artefact_os_name()))
    return binaries[0] if binaries and len(binaries) > 0 else None
