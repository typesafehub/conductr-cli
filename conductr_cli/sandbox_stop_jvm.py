def stop(args):
    """
    Stops the existing ConductR core and agent processes.
    This is done by interrogating the output of the ps, looking for java process which is running of the sandbox image.
    directory.

    :param args: args parsed from the input arguments
    """

    core_pids = find_conductr_core_pids(args.image_dir)
    core_killed_pids, core_hung_pids = kill_processes(core_pids)

    agent_pids = find_conductr_agent_pids(args.image_dir)
    agent_killed_pids, agent_hung_pids = kill_processes(agent_pids)

    if core_hung_pids or agent_hung_pids:
        if core_hung_pids:
            log_hung_core_processes(core_hung_pids)

        if agent_hung_pids:
            log_hung_agent_processes(agent_hung_pids)

        raise_hung_processes_error(core_hung_pids, agent_hung_pids)
    else:
        log_terminated_successfully(core_killed_pids, agent_killed_pids)


def find_conductr_core_pids(run_dir):
    """
    Finds the PIDs of the ConductR core from the output of the ps process, looking for java process which is running
    of the sandbox image.
    :param run_dir: directory of where ConductR core is running from.
    :return: the list of the ConductR core pids.
    """
    pass


def find_conductr_agent_pids(run_dir):
    """
    Finds the PIDs of the ConductR agent from the output of the ps process, looking for java process which is running
    of the sandbox image.
    :param run_dir: directory of where ConductR agent is running from.
    :return: the list of the ConductR agent pids.
    """
    pass


def kill_processes(pids):
    """
    Kills the processes given the pids by sending SIGTERM.
    :param pids: List of pids to be killed.
    :return: a tuple containing list of pids which can be killed successfully and a list of pids which has hung and
             can't be killed using SIGTERM.
    """
    pass


def log_hung_core_processes(core_hung_pids):
    """
    Displays an error message to indicate the core process pids which can't be terminated by SIGTERM.
    :param core_hung_pids: list of pids of the hung core process
    """
    pass


def log_hung_agent_processes(agent_hung_pids):
    """
    Displays an error message to indicate the agent process pids which can't be terminated by SIGTERM.
    :param core_hung_pids: list of pids of the hung agent process
    """
    pass


def log_terminated_successfully(core_killed_pids, agent_killed_pids):
    """
    Displays a log message to indicate that all sandbox processes has been terminated successfully.
    :param core_killed_pids: list of core pids which was terminated successfully.
    :param agent_killed_pids: list of agent pids which was terminated successfully.
    :return:
    """
    pass


def raise_hung_processes_error(core_hung_pids, agent_hung_pids):
    """
    Raises an error given pids of the hung core and agent processes.
    :param core_hung_pids: list of pids of the hung core process.
    :param agent_hung_pids: list of pids of the hung agent process.
    :return:
    """
    pass
