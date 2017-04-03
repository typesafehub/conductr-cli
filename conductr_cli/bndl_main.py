from conductr_cli import logging_setup
from conductr_cli.bndl_create import bndl_create
from conductr_cli.bndl_utils import mappings
import argcomplete
import argparse
import logging
import sys


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
                        choices=['docker', 'oci-image'],
                        required=False,
                        help='The input format. When absent, auto-detection is attempted')

    parser.add_argument('-t', '--tag',
                        required=False,
                        help='The name of the tag to create a ConductR bundle from. '
                             'For use with docker and oci-image formats. When absent,'
                             'the first tag present is used.')

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
                        help='If enabled, a bundle will not contain endpoints for ExposedPorts. '
                             'For use with docker and oci-image formats.',
                        default=True,
                        dest='use_default_endpoints',
                        action='store_false')

    parser.add_argument('--with-check',
                        help='If enabled, a "check" component will be added to the bundle"',
                        default=False,
                        action='store_true')

    parser.add_argument('--component-description',
                        help='Description to use for the generated ConductR component',
                        default='')

    parser.add_argument('--annotation',
                        action='append',
                        default=[],
                        dest='annotations',
                        help='Annotations to add to bundle.conf\n'
                             'Example: bndl --annotation my.first=value1 --annotation my.second=value2\n'
                             'Defaults to []')

    zero_or_more_mappings = {'--roles'}
    type_mappings = {'--memory': int, '--disk-space': int, '--nr-of-cpus': float}

    for argument, bundle_key in mappings.items():
        help_text = 'Sets the "{}" bundle.conf value'.format(bundle_key)

        parser.add_argument(argument,
                            nargs='*' if argument in zero_or_more_mappings else '?',
                            type=type_mappings[argument] if argument in type_mappings else None,
                            required=False,
                            help=help_text,
                            dest=bundle_key)

    parser.set_defaults(func=bndl)

    return parser


def bndl(args):
    return bndl_create(args)
