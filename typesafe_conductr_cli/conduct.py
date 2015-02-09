#!/usr/bin/env python3


import argcomplete
import argparse
from typesafe_conductr_cli import conduct_info, conduct_load, conduct_run, conduct_services, conduct_stop, conduct_unload, conduct_version
import os


default_ip = os.getenv('CONDUCTR_IP', '127.0.0.1')
default_port = os.getenv('CONDUCTR_PORT', '9005')


def add_ip_and_port(sub_parser):
    sub_parser.add_argument('-i', '--ip',
                            help='The optional ConductR IP, defaults to $CONDUCTR_IP or "127.0.0.1"',
                            default=default_ip)
    sub_parser.add_argument('-p', '--port',
                            type=int,
                            help='The optional ConductR port, defaults to $CONDUCTR_PORT or "9005"',
                            default=default_port)


def add_verbose(sub_parser):
    sub_parser.add_argument('-v', '--verbose',
                            help='Print JSON response to the command',
                            default=False,
                            dest='verbose',
                            action='store_true')


def add_default_arguments(sub_parser):
    add_ip_and_port(sub_parser)
    add_verbose(sub_parser)


def build_parser():
    # Main argument parser
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title='subcommands',
                                       description='valid subcommands',
                                       help='help for subcommands')

    # Sub-parser for `version` sub-command
    version_parser = subparsers.add_parser('version',
                                           help='print version')
    version_parser.set_defaults(func=conduct_version.version)

    # Sub-parser for `info` sub-command
    info_parser = subparsers.add_parser('info',
                                        help='print bundle information')
    add_default_arguments(info_parser)
    info_parser.set_defaults(func=conduct_info.info)

    # Sub-parser for `services` sub-command
    services_parser = subparsers.add_parser('services',
                                            help='print service information')
    add_default_arguments(services_parser)
    services_parser.set_defaults(func=conduct_services.services)

    # Sub-parser for `load` sub-command
    load_parser = subparsers.add_parser('load',
                                        help='load a bundle')
    load_parser.add_argument('bundle',
                             help='The path to the bundle')
    load_parser.add_argument('configuration',
                             nargs='?',
                             default=None,
                             help='The optional configuration for the bundle')
    load_parser.add_argument('--nr-of-cpus',
                             type=int,
                             required=True,
                             help='The number of cpus required to run the bundle')
    load_parser.add_argument('--memory',
                             type=int,
                             required=True,
                             help='The amount of memory in bytes required to run the bundle')
    load_parser.add_argument('--disk-space',
                             type=int,
                             required=True,
                             help='The amount of disk space in bytes required to ip an expanded bundle and configuration')
    load_parser.add_argument('--roles',
                             nargs='*',
                             default=[],
                             help='The optional roles of cluster nodes that this bundle can be deployed to, defaults to all roles')
    load_parser.add_argument('--name',
                             default=None,
                             dest='bundle_name',
                             help='The optional name of the bundle. Defaults to the first part of the filename until the digest.')
    load_parser.add_argument('--system',
                             default=None,
                             dest='system',
                             help='The optional system for the bundle. Defaults to the first part of the filename until the digest.')
    add_default_arguments(load_parser)
    load_parser.set_defaults(func=conduct_load.load)

    # Sub-parser for `run` sub-command
    run_parser = subparsers.add_parser('run',
                                       help='run a bundle')
    run_parser.add_argument('--scale',
                            type=int,
                            default=1,
                            help='The optional number of executions, defaults to 1')
    run_parser.add_argument('bundle',
                            help='The ID of the bundle')
    add_default_arguments(run_parser)
    run_parser.set_defaults(func=conduct_run.run)

    # Sub-parser for `stop` sub-command
    stop_parser = subparsers.add_parser('stop',
                                        help='stop a bundle')
    stop_parser.add_argument('bundle',
                             help='The ID of the bundle')
    add_default_arguments(stop_parser)
    stop_parser.set_defaults(func=conduct_stop.stop)

    # Sub-parser for `unload` sub-command
    unload_parser = subparsers.add_parser('unload',
                                          help='unload a bundle')
    unload_parser.add_argument('bundle',
                               help='The ID of the bundle')
    add_default_arguments(unload_parser)
    unload_parser.set_defaults(func=conduct_unload.unload)

    return parser


def get_cli_parameters(args):
    parameters = ['']
    if args.ip != default_ip:
        parameters.append('--ip {}'.format(args.ip))
    if args.port != int(default_port):
        parameters.append('--port {}'.format(args.port))
    return ' '.join(parameters)


def run():
    # Parse arguments
    parser = build_parser()
    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    if vars(args).get('func') is None:
        parser.print_help()
    else:
        args.cli_parameters = get_cli_parameters(args)
        args.func(args)


if __name__ == '__main__':
    run()
