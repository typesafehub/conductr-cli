from conductr_cli.constants import CONDUCTR_DCOS_SERVICE, DEFAULT_DCOS_SERVICE
from conductr_cli import conduct_request, conduct_url
from dcos import constants
import logging
import json
import os
import shutil
import sys


def default_service_name():
    return DEFAULT_DCOS_SERVICE


def service_name(args):
    # If Marathon is running more than one ConductR, and the user hasn't specified
    # a DCOS service, pick the first one that is returned

    default = default_service_name()

    if CONDUCTR_DCOS_SERVICE == default:
        marathon_groups = conduct_request.get(
            dcos_mode=True,
            host=conduct_url.conductr_host(args),
            url=conduct_url.raw_url('/service/marathon/v2/groups', args)
        )

        if marathon_groups.status_code == 200:
            groups = json.loads(marathon_groups.text)
            if 'apps' in groups:
                conductr_services = [
                    a['labels']['DCOS_SERVICE_NAME'] for a in groups['apps']

                    if 'labels' in a and
                       'DCOS_SERVICE_NAME' in a['labels'] and
                       a['labels']['DCOS_SERVICE_NAME'].startswith(CONDUCTR_DCOS_SERVICE)
                ]

                if len(conductr_services) > 0:
                    return conductr_services[0]

    return default


def setup(args):
    """`conduct setup-dcos` command"""
    log = logging.getLogger(__name__)

    if sys.executable.endswith(os.path.sep + 'conduct'):
        src = sys.executable
    else:
        src = shutil.which('conduct')

        if src is None:
            log.error('Unable to determine location of \'conduct\'; is it on the PATH?')
            return False

    dst = os.path.join(os.path.expanduser('~'),
                       constants.DCOS_DIR,
                       constants.DCOS_SUBCOMMAND_SUBDIR,
                       'conductr',
                       constants.DCOS_SUBCOMMAND_ENV_SUBDIR,
                       'bin',
                       constants.DCOS_COMMAND_PREFIX + 'conduct')

    package = os.path.join(os.path.expanduser('~'),
                           constants.DCOS_DIR,
                           constants.DCOS_SUBCOMMAND_SUBDIR,
                           'conductr',
                           'package.json')

    os.makedirs(os.path.dirname(package), exist_ok=True)

    with open(package, 'w') as file:
        file.write(json.dumps({
            'name': 'conductr',
            'description': 'To uninstall, use `dcos marathon app remove <service-name>`',
            'framework': True,
            'website': 'https://conductr.lightbend.com/docs'
        }))

    if os.path.exists(dst) or os.path.islink(dst):
        os.remove(dst)

    os.makedirs(os.path.dirname(dst), exist_ok=True)
    os.symlink(src, dst)
    log.screen('The DC/OS CLI is now configured.\n'
               'Prefix \'conduct\' with \'dcos\' when you want to contact ConductR on DC/OS e.g. \'dcos conduct info\'')
    return True
