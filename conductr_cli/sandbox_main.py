import argcomplete
import argparse
import logging
from conductr_cli.sandbox_common import CONDUCTR_DEV_IMAGE
from conductr_cli.sandbox_features import feature_names
from conductr_cli.docker import DockerVmType
from conductr_cli import sandbox_run, sandbox_stop, sandbox_init, sandbox_common, logging_setup, docker, \
    docker_machine, terminal
from subprocess import CalledProcessError


def build_parser():
    # Main argument parser
    parser = argparse.ArgumentParser('sandbox')
    subparsers = parser.add_subparsers(title='commands',
                                       help='Use one of the following sub commands')

    # Sub-parser for `run` sub-command
    run_parser = subparsers.add_parser('run',
                                       help='Run ConductR sandbox cluster',
                                       usage='%(prog)s IMAGE_VERSION [ARGS]',
                                       formatter_class=argparse.RawTextHelpFormatter)
    add_default_arguments(run_parser)
    run_parser.add_argument('image_version',
                            nargs='?',
                            help='Version of the ConductR docker image to use.\n'
                                 'To obtain the current version and additional information, please visit the \n'
                                 'http://www.typesafe.com/product/conductr/developer page on Typesafe.com.')
    run_parser.add_argument('-r', '--conductr-role',
                            dest='conductr_roles',
                            action='append',
                            nargs='*',
                            default=[],
                            help='Set additional roles allowed per ConductR node.\n'
                                 'Multiple roles per node are separated by a whitespace.\n'
                                 'Example: sandbox run IMAGE_VERSION -r role1 role2 -r role3\n'
                                 'In this example the roles role1 and role2 are assigned to the first node and\n'
                                 'role3 is assigned to the second node.\n'
                                 'Afterwards the specified roles are subsequently applied to the remaining nodes.\n'
                                 'Defaults to [].',
                            metavar='')
    run_parser.add_argument('-e', '--env',
                            dest='envs',
                            action='append',
                            default=[],
                            help='Set additional environment variables for each ConductR container. Defaults to [].',
                            metavar='')
    run_parser.add_argument('-i', '--image',
                            default=CONDUCTR_DEV_IMAGE,
                            help='Docker image to use.\n'
                                 'Defaults to `{}`.'.format(CONDUCTR_DEV_IMAGE),
                            metavar='')
    log_levels = ['debug', 'info', 'warning']
    run_parser.add_argument('-l', '--log-level',
                            default='info',
                            help='Log level of ConductR.\n'
                                 'Defaults to `info`.\n'
                                 'You can observe ConductRs logging via the `docker logs` command. \n'
                                 'For example `docker logs -f cond-0` will follow the logs of the first '
                                 'ConductR container.\n'
                                 'Available log levels: ' + ', '.join(log_levels),
                            choices=log_levels,
                            metavar='')
    run_parser.add_argument('-n', '--nr-of-containers',
                            type=int,
                            default=1,
                            help='Number of ConductR nodes. Defaults to 1.',
                            metavar='')
    run_parser.add_argument('-p', '--port',
                            dest='ports',
                            action='append',
                            type=int,
                            default=[],
                            help='Set additional ports to be made public by each of the ConductR containers.',
                            metavar='')
    run_parser.add_argument('--bundle-http-port',
                            dest='bundle_http_port',
                            type=int,
                            default=sandbox_common.bundle_http_port(),
                            help='Set default frontend port for proxying HTTP based request ACLs.',
                            metavar='')
    run_parser.add_argument('-f', '--feature',
                            dest='features',
                            action='append',
                            nargs='*',
                            default=[],
                            help='Features to be enabled.\n'
                                 'Available features: ' + ', '.join(feature_names),
                            metavar='')
    run_parser.add_argument('--no-wait',
                            help='Disables waiting for ConductR to be started in the sandbox',
                            default=False,
                            dest='no_wait',
                            action='store_true')
    run_parser.set_defaults(func=sandbox_run.run)

    # Sub-parser for `debug` sub-command
    debug_parser = subparsers.add_parser('debug',
                                         help='Not supported. Use \'sbt-conductr-sandbox\' instead.')
    add_resolve_ip(debug_parser, False)
    debug_parser.set_defaults(func='debug')

    # Sub-parser for `stop` sub-command
    stop_parser = subparsers.add_parser('stop',
                                        help='Stop ConductR sandbox cluster')
    add_default_arguments(stop_parser)
    stop_parser.set_defaults(func=sandbox_stop.stop)

    # Sub-parser for `init` sub-command
    init_parser = subparsers.add_parser('init',
                                        help='Initializes ConductR sandbox environment')
    add_resolve_ip(init_parser, False)
    init_parser.set_defaults(func=sandbox_init.init)
    return parser


def add_default_arguments(sub_parser):
    sub_parser.add_argument('--local-connection',
                            default=True,
                            help=argparse.SUPPRESS)
    add_resolve_ip(sub_parser, True)


def add_resolve_ip(sub_parser, default_value):
    sub_parser.add_argument('--resolve-ip',
                            default=default_value,
                            dest='resolve_ip',
                            action='store_true',
                            help=argparse.SUPPRESS)


def validate_docker_vm(vm_type, is_init_command):
    log = logging.getLogger(__name__)
    if vm_type is DockerVmType.DOCKER_ENGINE:
        try:
            terminal.docker_info()
            return True
        except (AttributeError, CalledProcessError):
            log.error('Docker native is installed but not running.')
            log.error('Please start Docker with one of the Docker flavors based on your OS:')
            log.error('  Linux:   Docker service')
            log.error('  MacOS:   Docker for Mac')
            log.error('  Windows: Docker for Windows')
            log.error('A successful Docker startup can be verified with: docker info')
            return False
    elif vm_type is DockerVmType.DOCKER_MACHINE and is_init_command:
        # The docker-machine validation is also performed in the sandbox init command. Therefore we skip the validation.
        return True
    elif vm_type is DockerVmType.DOCKER_MACHINE:
        docker_machine_vm_name = docker_machine.vm_name()

        try:
            output = terminal.docker_machine_status(docker_machine_vm_name)
            if output != 'Running':
                log.error('Docker machine VM {} is not started'.format(docker_machine_vm_name))
                log.error('Please use the following command to start the Docker machine VM: sandbox init')
                return False
        except CalledProcessError:
            log.error('Docker machine VM {} does not exist'.format(docker_machine_vm_name))
            log.error('Please use the following command to create the Docker machine VM: sandbox init')
            return False

        try:
            terminal.docker_info()
            return True
        except (AttributeError, CalledProcessError):
            print('out of docker info')
            log.info('It looks like the Docker machine environment variables are not set correctly.')
            log.info('Let me try to reset the Docker machine environment variables..')
            docker_machine_vm_name = docker_machine.vm_name()
            [docker_machine.set_env(env[0], env[1]) for env in docker_machine.envs(docker_machine_vm_name)]
            try:
                terminal.docker_info()
                log.warning('To set the environment variables for each terminal session '
                            'follow the instructions of the command:')
                log.warning('  docker-machine env {}'.format(docker_machine_vm_name))
                return True
            except (AttributeError, CalledProcessError):
                log.error('Docker still cannot connect to the Docker machine VM.')
                log.error('Please set the docker environment variables.')
                log.error('Afterwards verify that docker is up and running with: docker info')
                return False

    elif vm_type is DockerVmType.NONE:
        log.error('Neither Docker native is installed nor the Docker machine environment variables are set.')
        log.error('We recommend to use one of following the Docker distributions depending on your OS:')
        log.error('  Linux:                                         Docker Engine')
        log.error('  MacOS:                                         Docker for Mac')
        log.error('  Windows 10+ Professional or Enterprise 64-bit: Docker for Windows')
        log.error('  Other Windows:                                 Docker machine via Docker Toolbox')
        log.error('For more information checkout: https://www.docker.com/products/overview')
        return False


def run():
    # Parse arguments
    parser = build_parser()
    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    # Print help or execute subparser function
    if not vars(args).get('func'):
        parser.print_help()
    # Exit with sandbox debug error message
    elif vars(args).get('func') == 'debug':
        parser.exit('Debugging a ConductR cluster is not supported by the \'conductr-cli\'.\n'
                    'Use the sbt plugin \'sbt-conductr\' instead.')
    # Validate image_version
    elif vars(args).get('func').__name__ == 'run' and not args.image_version:
        parser.exit('The version of the ConductR Docker image must be set.\n'
                    'Please visit https://www.lightbend.com/product/conductr/developer '
                    'to obtain the current version information.')
    # Call sandbox function
    else:
        logging_setup.configure_logging(args)
        # Check that all feature arguments are valid
        if vars(args).get('func').__name__ == 'run':
            invalid_features = [f for f, *a in args.features if f not in feature_names]
            if invalid_features:
                parser.exit('Invalid features: %s (choose from %s)' %
                            (', '.join("'%s'" % f for f in invalid_features),
                             ', '.join("'%s'" % f for f in feature_names)))
        # Docker VM validation
        args.vm_type = docker.vm_type()
        is_init_command = True if vars(args).get('func').__name__ == 'init' else False
        docker_vm_validation_successful = validate_docker_vm(args.vm_type, is_init_command)
        if not args.vm_type or not docker_vm_validation_successful:
            exit(1)
        else:
            args.func(args)
