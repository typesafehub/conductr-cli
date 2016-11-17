from dcos import constants
import logging
import os
import shutil


def setup(args):
    """`conduct setup-dcos` command"""
    log = logging.getLogger(__name__)
    src = shutil.which("conduct")
    dst = os.path.join(os.path.expanduser('~'),
                       constants.DCOS_DIR,
                       constants.DCOS_SUBCOMMAND_SUBDIR,
                       'conductr',
                       constants.DCOS_SUBCOMMAND_ENV_SUBDIR,
                       'bin',
                       constants.DCOS_COMMAND_PREFIX + 'conduct')
    if os.path.exists(dst):
        os.remove(dst)
    else:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
    os.symlink(src, dst)
    log.screen('The DC/OS CLI is now configured.\n'
               'Prefix \'conduct\' with \'dcos\' when you want to contact ConductR on DC/OS e.g. \'dcos conduct info\'')
    return True
