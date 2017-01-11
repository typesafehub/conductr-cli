from conductr_cli import host, sandbox_stop
from conductr_cli.sandbox_common import ConductrComponent
from requests.exceptions import HTTPError, ConnectionError
from conductr_cli.exceptions import InstanceCountError, BindAddressNotFoundError, SandboxImageNotFoundError, \
    BintrayUnreachableError
from conductr_cli.resolvers import bintray_resolver
from conductr_cli.resolvers.bintray_resolver import BINTRAY_DOWNLOAD_REALM, BINTRAY_LIGHTBEND_ORG, \
    BINTRAY_CONDUCTR_REPO, BINTRAY_CONDUCTR_CORE_PACKAGE_NAME, BINTRAY_CONDUCTR_AGENT_PACKAGE_NAME

import logging
import re
import os
import shutil


NR_OF_INSTANCE_EXPRESSION = '[0-9]+\\:[0-9]+'
BIND_TEST_PORT = 19991  # The port used for testing if an address can be bound.


def run(args, features):
    """
    Starts the ConductR core and agent.

    :param args: args parsed from the input arguments
    :param features: list of features which are specified via -f switch.
                     This is only relevant for Docker based sandbox since the features decides what port to expose
    :return: a tuple containing list of core pids and list of agent pids
    """
    nr_of_core_instances, nr_of_agent_instances = instance_count(args.image_version, args.nr_of_containers)

    validate_jvm_support()
    bind_addrs = find_bind_addrs(max(nr_of_core_instances, nr_of_agent_instances), args.addr_range)

    core_extracted_dir, agent_extracted_dir = obtain_sandbox_image(args.image_dir, args.image_version)

    sandbox_stop.stop(args)

    core_pids = start_core_instances(core_extracted_dir, bind_addrs[0:nr_of_core_instances])
    agent_pids = start_agent_instances(agent_extracted_dir, bind_addrs[0:nr_of_agent_instances])

    return (core_pids, agent_pids)


def log_run_attempt(args, pids, is_started, wait_timeout):
    """
    Logs the run attempt. This method will be called after the completion of run method and when all the features has been started.

    :param args: args parsed from the input arguments
    :param pids: a tuple containing list of core pids and list of agent pids
    :param is_started: sets to true if sandbox is started
    :param wait_timeout: the amount of timeout waiting for sandbox to be started
    :return:
    """
    core_pids, agent_pids = pids
    pass


def instance_count(image_version, instance_expression):
    """
    Parses the instance expressions into number of core and agent instances, i.e.

    The expression `2` translates to 2 core instances and 2 agent instances.
    The expression `2:3` translates to 2 core instances and 3 agent instances.

    :param image_version:
    :param instance_expression:
    :return: a tuple containing number of core instances and number of agent instances.
    """
    try:
        nr_of_instances = int(instance_expression)
        return nr_of_instances, nr_of_instances
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
    Validates for the presence of supported JVM (i.e. Oracle JVM 8), else raise an exception to fail the sandbox run.
    """
    pass


def find_bind_addrs(nr_of_addrs, addr_range):
    """
    Finds for the presence of address which can be bound to the sandbox given an address range, i.e.
    - Let's say 3 address aliases is required.
    - The address range is 192.168.128.0/24

    These addresses requires setup using ifconfig as such (MacOS example):

    sudo ifconfig lo0 alias 192.168.128.1 255.255.255.0
    sudo ifconfig lo0 alias 192.168.128.2 255.255.255.0
    sudo ifconfig lo0 alias 192.168.128.3 255.255.255.0

    This command will check if 192.168.128.1, 192.168.128.2, and 192.168.128.3 can be bound. The check is done by
    binding a socket to each of these address using a test port.

    If the number of required address is not present, provide the commands so the end user is able to copy-paste and
    execute these commands.

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
        setup_instructions = host.addr_alias_setup_instructions(addrs_unavailable[0:nr_of_addr_setup],
                                                                addr_range.netmask)
        raise BindAddressNotFoundError(setup_instructions)
    else:
        return addrs_to_bind


def obtain_sandbox_image(image_dir, image_version):
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

    :param image_dir: the directory where ConductR core and agent binaries will be cached, also the base directory
                      containing the expanded ConductR core and agent binaries.
    :param image_version: the version of the sandbox to be downloaded.
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

        :return: tuple of (core_path, agent_path)
        """
        core_path = resolve_binary_from_cache(core_binary_info['cache_path'])
        agent_path = resolve_binary_from_cache(agent_binary_info['cache_path'])

        if (not core_path) or (not agent_path):
            try:
                bintray_username, bintray_password = bintray_resolver.load_bintray_credentials()
                bintray_auth = (BINTRAY_DOWNLOAD_REALM, bintray_username, bintray_password)
                if not core_path:
                    _, _, core_path = bintray_resolver.bintray_download(
                        image_dir, BINTRAY_LIGHTBEND_ORG, BINTRAY_CONDUCTR_REPO,
                        core_binary_info['bintray_package_name'], bintray_auth, version=image_version)

                if not agent_path:
                    _, _, agent_path = bintray_resolver.bintray_download(
                        image_dir, BINTRAY_LIGHTBEND_ORG, BINTRAY_CONDUCTR_REPO,
                        agent_binary_info['bintray_package_name'], bintray_auth, version=image_version)
            except ConnectionError:
                raise BintrayUnreachableError('Bintray is unreachable.')
            except HTTPError:
                raise SandboxImageNotFoundError(core_binary_info['type'], image_version)

        return core_path, agent_path

    def resolve_binary_from_cache(binary_cache_path):
        """
        Checks for the presence of the ConductR binary in the cache directory.

        :param binary_cache_path the path of the cached ConductR universal binary.
        :return: If present, return the path to the binary file, else return None.
        """
        if os.path.exists(binary_cache_path):
            return binary_cache_path
        else:
            return None

    def resolve_binary_info(conductr_component):
        """
        Provides information of the ConductR universal binary package.

        :param conductr_component: the type of the ConductR component
               Can be either 'ConductrComponent.CORE' or 'ConductrComponent.AGENT'.
        :return: the following information of the universal binary package:
                 - type
                 - extraction_dir
                 - The path of the cached universal binary package
                 - Bintray package name
        """
        if conductr_component is ConductrComponent.CORE:
            return {
                'type': 'core',
                'extraction_dir': '{}/core'.format(image_dir),
                'cache_path': '{}/conductr-{}.tgz'.format(image_dir, image_version),
                'bintray_package_name': BINTRAY_CONDUCTR_CORE_PACKAGE_NAME
            }
        elif conductr_component is ConductrComponent.AGENT:
            return {
                'type': 'agent',
                'extraction_dir': '{}/agent'.format(image_dir),
                'cache_path': '{}/conductr-agent-{}.tgz'.format(image_dir, image_version),
                'bintray_package_name': BINTRAY_CONDUCTR_AGENT_PACKAGE_NAME
            }
        else:
            raise AssertionError('conductr-component {} is invalid. '
                                 'Need to be either of: ConductrComponent.CORE, ConductRComponent.AGENT'
                                 .format(conductr_component))

    def extract_binary(path, binary_info):
        """
        The binary will be expanded into the `${extraction_dir}`.
        The directory `${extraction_dir}` will be emptied before the binary is expanded.

        :param path: the path to the core binary to be expanded.
        :param binary_info: the information of the ConductR universal binary
        :return: path to the directory containing expanded core binary.
        """
        log = logging.getLogger(__name__)
        extraction_dir = binary_info['extraction_dir']
        if os.path.exists(extraction_dir):
            shutil.rmtree(extraction_dir)
        os.makedirs(extraction_dir, mode=0o700)
        log.info('Extracting ConductR {} to {}'.format(binary_info['type'], extraction_dir))
        shutil.unpack_archive(path, extraction_dir)
        binary_basename = os.path.splitext(os.path.basename(path))[0]
        extraction_subdir = '{}/{}'.format(extraction_dir, binary_basename)
        for filename in os.listdir(extraction_subdir):
            shutil.move('{}/{}'.format(extraction_subdir, filename), '{}/{}'.format(extraction_dir, filename))
        os.rmdir(extraction_subdir)
        return extraction_dir

    core_binary_info = resolve_binary_info(ConductrComponent.CORE)
    agent_binary_info = resolve_binary_info(ConductrComponent.AGENT)

    core_binary_path, agent_binary_path = resolve_binaries()

    core_extracted_dir = extract_binary(core_binary_path, core_binary_info)
    agent_extracted_dir = extract_binary(agent_binary_path, agent_binary_info)

    return core_extracted_dir, agent_extracted_dir


def start_core_instances(core_extracted_dir, bind_addrs):
    """
    Starts the ConductR core process.

    Each instance is allocated an address to be bound based on the address range. For example:
    - Given 3 required core instances
    - Given the address range input of 192.168.128.0/24
    - The instances will be allocated these addresses: 192.168.128.1, 192.168.128.2, 192.168.128.3

    TODO: investigate if each ConductR core process requires its own log files, or all the logs can be sent into the
    same file.

    :param core_extracted_dir: the directory containing the files expanded from core's binary .tgz
    :param bind_addrs: a list of addresses which the core instances will bind to.
                       If there are 3 instances of core required, there will be 3 addresses supplied.
    :return: the pids of the core instances.
    """
    log = logging.getLogger(__name__)
    log.info('Binding ConductR core to the following address: {}'.format(host.display_addrs(bind_addrs)))

    pass


def start_agent_instances(agent_extracted_dir, bind_addrs):
    """
    Starts the ConductR agent process.

    Each instance is allocated an address to be bound based on the address range. For example:
    - Given 3 required agent instances
    - Given the address range input of 192.168.128.0/24
    - The instances will be allocated these addresses: 192.168.128.1, 192.168.128.2, 192.168.128.3

    TODO: investigate if each ConductR agent process requires its own log files, or all the logs can be sent into the
    same file.

    :param agent_extracted_dir: the directory containing the files expanded from agent's binary .tgz
    :param bind_addrs: a list of addresses which the core instances will bind to.
                       If there are 3 instances of core required, there will be 3 addresses supplied.
    :return: the pids of the agent instances.
    """
    log = logging.getLogger(__name__)
    log.info('Binding ConductR agent to the following address: {}'.format(host.display_addrs(bind_addrs)))

    pass
