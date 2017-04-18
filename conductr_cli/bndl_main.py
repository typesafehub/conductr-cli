from conductr_cli import logging_setup
from conductr_cli.bndl_create import bndl_create
import argcomplete
import argparse
import logging
import sys


def invoke(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


def run(argv=None):
    log = logging.getLogger(__name__)
    parser = build_parser()
    argcomplete.autocomplete(parser)
    args = parser.parse_args(argv)

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


def build_parser():
    parser = argparse.ArgumentParser('bndl', formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-f', '--format',
                        choices=['docker', 'oci-image', 'bundle'],
                        required=False,
                        help='The input format. When absent, auto-detection is attempted')

    parser.add_argument('--image-tag',
                        required=False,
                        help='The name of the tag to create a ConductR bundle from. '
                             'For use with docker and oci-image formats. When absent, '
                             'the first tag present is used')

    parser.add_argument('--image-name',
                        required=False,
                        help='The name of the image to create a ConductR bundle from. '
                             'For use with docker and oci-image formats. When absent, '
                             'the first image present is used.')

    parser.add_argument('-o', '--output',
                        nargs='?',
                        help='The target output file. When absent, stdout is used')

    parser.add_argument('source',
                        help='Optional path to a directory or tar file'
                             'When absent, stdin is used',
                        nargs='?')

    parser.add_argument('--no-shazar',
                        help='If enabled, a bundle will not be run through shazar',
                        default=True,
                        dest='use_shazar',
                        action='store_false')

    parser.add_argument('--no-default-endpoints',
                        help='If provided, a bundle will not contain endpoints for ExposedPorts. '
                             'For use with docker and oci-image formats',
                        default=True,
                        dest='use_default_endpoints',
                        action='store_false')

    parser.add_argument('--with-check',
                        help='If enabled, a "check" component will be added to the bundle"',
                        default=False,
                        action='store_true')

    parser.add_argument('--component-description',
                        help='Description to use for the generated ConductR component. '
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
