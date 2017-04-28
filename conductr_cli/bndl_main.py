from conductr_cli import logging_setup
from conductr_cli.endpoint import Endpoint, AmbigousBindProtocolError
from conductr_cli.bndl_create import bndl_create
import argcomplete
import argparse
import logging
import sys


def invoke(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    set_endpoints(args)
    return args.func(args)


def run(argv=None):
    log = logging.getLogger(__name__)
    parser = build_parser()
    argcomplete.autocomplete(parser)
    args = parser.parse_args(argv)
    set_endpoints(args)

    if args.source == '-':
        args.source = None

    if args.output == '-':
        args.output = None

    if sys.stdout.isatty() and sys.stdin.isatty() and args.source is None:
        parser.print_help()
    elif sys.stdout.isatty() and args.output is None:
        log.error('bndl: Refusing to write to terminal. Provide -o or redirect elsewhere')
        sys.exit(2)
    else:
        logging_setup.configure_logging(args)

        sys.exit(args.func(args))


class EndpointAction(argparse.Action):
    def __call__(self, parser, namespace, value, option_strings):
        log = logging.getLogger(__name__)
        if option_strings == '--endpoint':
            namespace.endpoint_dicts.append({'name': value})
        elif not namespace.endpoint_dicts:
            log.error('bndl: argument {} needs to be specified after the argument --endpoint'
                      .format(option_strings))
            sys.exit(2)
        elif option_strings == '--acl':
            last_endpoint = namespace.endpoint_dicts[-1]
            if 'acls' in last_endpoint:
                last_endpoint['acls'].append(value)
            else:
                last_endpoint['acls'] = [value]
        else:
            dict_key = option_strings[2:]
            namespace.endpoint_dicts[-1][dict_key] = value


def set_endpoints(args):
    log = logging.getLogger(__name__)
    if args.endpoint_dicts:
        args.endpoints = []
        for endpoint_dict in args.endpoint_dicts:
            try:
                endpoint = Endpoint(endpoint_dict)
            except ValueError:
                log.error('bndl: argument --component is required when specifying argument --endpoint {}'
                          .format(endpoint_dict['name']))
                sys.exit(2)
            except AmbigousBindProtocolError:
                log.error('bndl: argument --bind-protocol is required '
                          'when acls with different protocol families are specified\n'
                          'endpoint: {}\n'
                          'acls: {}'
                          .format(endpoint_dict['name'], ', '.join(endpoint_dict['acls'])))
                sys.exit(2)
            args.endpoints.append(endpoint)


def build_parser():
    parser = argparse.ArgumentParser(prog='bndl',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     description='Create or modify a bundle')

    parser.add_argument('-f', '--format',
                        choices=['docker', 'oci-image', 'bundle'],
                        required=False,
                        help='The input format\n'
                             'When absent, auto-detection is attempted')

    parser.add_argument('--image-tag',
                        required=False,
                        help='The name of the tag to create a ConductR bundle from\n'
                             'For use with docker and oci-image formats\n'
                             'When absent, the first tag present is used')

    parser.add_argument('--image-name',
                        required=False,
                        help='The name of the image to create a ConductR bundle from\n'
                             'For use with docker and oci-image formats\n'
                             'When absent, the first image present is used')

    parser.add_argument('-o', '--output',
                        nargs='?',
                        help='The target output file\n'
                             'When absent, stdout is used')

    parser.add_argument('source',
                        help='Optional path to a directory or tar file\n'
                             'When absent, stdin is used',
                        nargs='?')

    parser.add_argument('--no-shazar',
                        help='If enabled, a bundle will not be run through shazar',
                        default=True,
                        dest='use_shazar',
                        action='store_false')

    parser.add_argument('--no-default-endpoints',
                        help='If provided, a bundle will not contain endpoints for ExposedPorts\n'
                             'For use with docker and oci-image formats',
                        default=True,
                        dest='use_default_endpoints',
                        action='store_false')

    endpoint_args = parser.add_argument_group('endpoints')
    endpoint_args.add_argument('-e', '--endpoint',
                               help='Endpoints to add to bundle.conf\n'
                                    'If specified, existing endpoints are removed\n'
                                    'Example: bndl --endpoint web --component web --bind-protocol http '
                                    '--service-name web --acl http:/subpath',
                               metavar='ENDPOINT [OPTS]',
                               dest='endpoint_dicts',
                               default=[],
                               action=EndpointAction)
    endpoint_args.add_argument('--component',
                               help='Component to which an endpoint should be added\n'
                                    'Used in conjunction with the --endpoint option\n'
                                    'Required when specifying the --endpoint option',
                               metavar='COMPONENT',
                               dest='endpoint_dicts',
                               action=EndpointAction)
    endpoint_args.add_argument('--bind-protocol',
                               help='Bind protocol of an endpoint\n'
                                    'Used in conjunction with the --endpoint option\n'
                                    'When absent, tcp is used',
                               metavar='BIND_PROTOCOL',
                               dest='endpoint_dicts',
                               choices=['tcp', 'http'],
                               action=EndpointAction)
    endpoint_args.add_argument('--bind-port',
                               help='Bind port of an endpoint\n'
                                    'Used in conjunction with the --endpoint option\n'
                                    'When absent, 0 is used, meaning a bind port is selected by ConductR',
                               metavar='BIND_PORT',
                               type=int,
                               dest='endpoint_dicts',
                               action=EndpointAction)
    endpoint_args.add_argument('--service-name',
                               help='Service name of an endpoint\n'
                                    'Used in conjunction with the --endpoint option\n'
                                    'When absent, the endpoint is not locatable via the service name',
                               metavar='SERVICE_NAME',
                               dest='endpoint_dicts',
                               action=EndpointAction)
    endpoint_args.add_argument('--acl',
                               help='Request ACL of an endpoint\n'
                                    'Used in conjunction with the --endpoint option\n'
                                    'When absent, the endpoint will not be accessible via the Proxy',
                               metavar='ACL',
                               dest='endpoint_dicts',
                               action=EndpointAction)

    parser.add_argument('--with-check',
                        help='If enabled, a "check" component will be added to the bundle',
                        default=False,
                        action='store_true')

    parser.add_argument('--component-description',
                        help='Description to use for the generated ConductR component\n'
                             'For use with docker and oci-image formats',
                        default='')

    parser.add_argument('--annotation',
                        action='append',
                        default=[],
                        dest='annotations',
                        help='Annotations to add to bundle.conf\n'
                             'Example: bndl --annotation my.first=value1 --annotation my.second=value2\n'
                             'Defaults to []')

    parser.add_argument('--compatibility-version',
                        nargs='?',
                        required=False,
                        help='Sets the "compatibilityVersion" bundle.conf value',
                        dest='compatibility_version')

    parser.add_argument('--disk-space',
                        nargs='?',
                        required=False,
                        help='Sets the "diskSpace" bundle.conf value',
                        dest='disk_space',
                        type=int)

    parser.add_argument('--memory',
                        nargs='?',
                        required=False,
                        help='Sets the "memory" bundle.conf value',
                        dest='memory',
                        type=int)

    parser.add_argument('--name',
                        nargs='?',
                        required=False,
                        help='Sets the "name" bundle.conf value',
                        dest='name')

    parser.add_argument('--nr-of-cpus',
                        nargs='?',
                        required=False,
                        help='Sets the "nrOfCpus" bundle.conf value',
                        dest='nr_of_cpus',
                        type=float)

    parser.add_argument('--roles',
                        nargs='*',
                        required=False,
                        help='Sets the "roles" bundle.conf value',
                        dest='roles')

    parser.add_argument('--system',
                        nargs='?',
                        required=False,
                        help='Sets the "system" bundle.conf value',
                        dest='system')

    parser.add_argument('--system-version',
                        nargs='?',
                        required=False,
                        help='Sets the "systemVersion" bundle.conf value',
                        dest='system_version')

    parser.add_argument('--tag',
                        action='append',
                        default=[],
                        dest='tags',
                        help='Tags to add to bundle.conf\n'
                             'Example: bndl --tag 16.04 --tag xenial\n'
                             'Defaults to []')

    parser.add_argument('--version',
                        nargs='?',
                        required=False,
                        help='Sets the "version" bundle.conf value',
                        dest='version')

    parser.set_defaults(func=bndl)

    return parser


def bndl(args):
    return bndl_create(args)
