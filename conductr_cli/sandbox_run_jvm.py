from conductr_cli import sandbox_stop
from conductr_cli.resolvers import bintray_resolver
from conductr_cli.resolvers.bintray_resolver import BINTRAY_DOWNLOAD_REALM


def run(args, features):
    """
    Starts the ConductR core and agent.

    :param args: args parsed from the input arguments
    :param features: list of features which are specified via -f switch.
                     This is only relevant for Docker based sandbox since the features decides what port to expose
    :return: a tuple containing list of core pids and list of agent pids
    """
    nr_of_core_instances, nr_of_agent_instances = instance_count(args.nr_of_containers)

    validate_jvm_support()
    validate_address_aliases(max(nr_of_core_instances, nr_of_agent_instances), args.interface, args.addr_range)

    core_extracted_dir, agent_extracted_dir = obtain_sandbox_image(args.resolve_cache_dir, args.image_dir, args.image_version)

    sandbox_stop.stop(args)

    core_pids = start_core_instances(core_extracted_dir, nr_of_core_instances, args.addr_range)
    agent_pids = start_agent_instances(agent_extracted_dir, nr_of_agent_instances, args.addr_range)

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


def instance_count(instance_expression):
    """
    Parses the instance expressions into number of core and agent instances, i.e.

    The expression `2` translates to 2 core instances and 2 agent instances.
    The expression `2:3` translates to 2 core instances and 3 agent instances.

    :param instance_expression:
    :return: a tuple containing number of core instances and number of agent instances.
    """
    pass


def validate_jvm_support():
    """
    Validates for the presence of supported JVM (i.e. Oracle JVM 8), else raise an exception to fail the sandbox run.
    """
    pass


def validate_address_aliases(nr_of_alias, interface, addr_range):
    """
    Validates for the presence of address alias given a specified interface and address range, i.e.
    - Let's say 3 address aliases is required.
    - The interface specified is lo0.
    - The address range is 192.168.128.0/24

    These addresses requires setup using ifconfig as such:

    sudo ifconfig lo0 alias 192.168.128.1 255.255.255.0
    sudo ifconfig lo0 alias 192.168.128.2 255.255.255.0
    sudo ifconfig lo0 alias 192.168.128.3 255.255.255.0

    This command will parse the ifconfig output of the lo0 to ensure the alias for 192.168.128.1, 192.168.128.2, and
    192.168.128.3 is present.

    If these alias is not present, printout an error message and raise an exception to fail the sandbox run.

    As part of the error message printout, provide the commands so the end user is able to copy-paste and execute these
    commands.

    :param nr_of_alias: number of address aliases required
    :param interface: the network interface which will be used to create the address alias to be used by core and agent
                      as the bind address.
    :param addr_range: the range of address which is available to core and agent to bind to.
                       The address is specified in the CIDR format, i.e. 192.168.128.0/24
    """
    pass


def obtain_sandbox_image(cache_dir, image_dir, image_version):
    """
    Obtains the sandbox image.

    The sandbox image is the .tar.gz binary of ConductR core and agent which is available as a download from Bintray.

    First the local cache is interrogated for the presence of the .tar.gz binary.

    If the binary is not yet available within the local cache, then it will be downloaded from Bintray. If the binary
    is present within the local cache, they will be used instead.

    The core binary will be expanded into the `${image_dir}/core`. The directory `${image_dir}/core` will be emptied
    before the binary is expanded.

    Similarly, the agent binary will be expanded into the `${image_dir}/agent`. The directory `${image_dir}/agent` will
    be emptied before the binary is expanded.

    :param cache_dir: the directory where ConductR core and agent binaries will be cached.
    :param image_dir: the base directory containing the expanded ConductR core and agent binaries.
    :param image_version: the version of the sandbox to be downloaded.
    :return: the pair containing path to the expanded core directory and path to the expanded agent directory
    """
    def resolve_core_binary_from_cache():
        """
        Checks for the presence of `${cache_dir}/core/${image_version}.tar.gz`.

        :return: If present, return the path to the binary file, else return None.
        """
        pass

    def resolve_agent_binary_from_cache():
        """
        Checks for the presence of `${cache_dir}/agent/${image_version}.tar.gz`.

        :return: If present, return the path to the binary file, else return None.
        """
        pass

    def download_core_from_bintray(bintray_auth):
        """
        Downloads core from bintray given `${image_version}`.

        The images are expected to be cached in `${cache_dir}/core`.

        If the binary is not yet available within the local cache, then it will be downloaded from Bintray.

        The aftefacts will be available under the following Bintray repo:

        https://bintray.com/lightbend/commercial-releases/ConductR-Universal

        As part of the download:
        - A progress bar will be displayed.
        - The download will be saved into `${cache_dir}/core/${image_version}.tar.gz.tmp`. Once download is complete,
          this file will be moved to `${cache_dir}/core/${image_version}.tar.gz`.

        :param bintray_auth: a tuple containing Bintray auth information which can be passed into the request library.
                             This information is loaded from bintray credentials file, which can be None if the
                             credentials is not specified
        :return: path to the downloaded file
        """
        pass

    def download_agent_from_bintray(bintray_auth):
        """
        Downloads agent from bintray given `${image_version}`.

        The images are expected to be cached in `${cache_dir}/agent`.

        If the binary is not yet available within the local cache, then it will be downloaded from Bintray.

        The aftefacts will be available under the following Bintray repo:

        https://bintray.com/lightbend/commercial-releases/ConductR-Agent-Universal

        As part of the download:
        - A progress bar will be displayed.
        - The download will be saved into `${cache_dir}/agent/${image_version}.tar.gz.tmp`. Once download is complete,
          this file will be moved to `${cache_dir}/agent/${image_version}.tar.gz`.

        :param bintray_auth: a tuple containing Bintray auth information which can be passed into the request library.
                             This information is loaded from bintray credentials file, which can be None if the
                             credentials is not specified
        :return: path to the downloaded file
        """
        pass

    def extract_core(core_binary):
        """
        The core binary will be expanded into the `${image_dir}/core`. The directory `${image_dir}/core` will be emptied
        before the binary is expanded.

        :param core_binary: the path to the core binary to be expanded.
        :return: path to the directory containing expanded core binary.
        """
        pass

    def extract_agent(agent_binary):
        """
        The agent binary will be expanded into the `${image_dir}/agent`. The directory `${image_dir}/agent` will be emptied
        before the binary is expanded.

        :param agent_binary: the path to the agent binary to be expanded.
        :return: path to the directory containing expanded agent binary.
        """
        pass

    core_binary = resolve_core_binary_from_cache()
    agent_binary = resolve_agent_binary_from_cache()

    if (not core_binary) and (not agent_binary):
        bintray_username, bintray_password = bintray_resolver.load_bintray_credentials()
        bintray_auth = (BINTRAY_DOWNLOAD_REALM, bintray_username, bintray_password) if bintray_username else None
        if not core_binary:
            core_binary = download_core_from_bintray(bintray_auth)

        if not agent_binary:
            agent_binary = download_agent_from_bintray(bintray_auth)

    core_extracted_dir = extract_core(core_binary)
    agent_extracted_dir = extract_agent(agent_binary)

    return (core_extracted_dir, agent_extracted_dir)


def start_core_instances(core_extracted_dir, nr_of_instances, addr_range):
    """
    Starts the ConductR core process.

    Each instance is allocated an address to be bound based on the address range. For example:
    - Given 3 required core instances
    - Given the address range input of 192.168.128.0/24
    - The instances will be allocated these addresses: 192.168.128.1, 192.168.128.2, 192.168.128.3

    TODO: investigate if each ConductR core process requires its own log files, or all the logs can be sent into the
    same file.

    :param core_extracted_dir: the directory containing the files expanded from core's binary .tar.gz
    :param nr_of_instances: number of core instances required
    :param addr_range: the range of address required, i.e. 192.168.128.0/24
    :return: the pids of the core instances.
    """
    pass


def start_agent_instances(agent_extracted_dir, nr_of_instances, addr_range):
    """
    Starts the ConductR agent process.

    Each instance is allocated an address to be bound based on the address range. For example:
    - Given 3 required agent instances
    - Given the address range input of 192.168.128.0/24
    - The instances will be allocated these addresses: 192.168.128.1, 192.168.128.2, 192.168.128.3

    TODO: investigate if each ConductR agent process requires its own log files, or all the logs can be sent into the
    same file.

    :param agent_extracted_dir: the directory containing the files expanded from agent's binary .tar.gz
    :param nr_of_instances: number of agent instances required
    :param addr_range: the range of address required, i.e. 192.168.128.0/24
    :return: the pids of the agent instances.
    """
    pass
