import argcomplete
import argparse
from functools import partial
from conductr_cli import logging_setup
from conductr_cli.constants import IO_CHUNK_SIZE, SHAZAR_TIMESTAMP_MIN
import hashlib
import logging
import os
import shutil
import sys
import tarfile
import tempfile
import time
import zipfile


def run(argv=None):
    parser = build_parser()
    argcomplete.autocomplete(parser)
    args = parser.parse_args(argv)
    logging_setup.configure_logging(args)

    log = logging.getLogger(__name__)

    if sys.stdout.isatty() and args.output is None and (args.source is None or args.tar):
        if sys.stdin.isatty() and not args.tar:
            parser.print_help()
        else:
            log.error('shazar: Refusing to write to terminal. Provide -o or redirect elsewhere')
            sys.exit(2)
    else:
        args.func(args)


def build_parser():
    parser = argparse.ArgumentParser(
        description='Package a bundle directory or bundle configuration file'
    )
    parser.add_argument('-o', '--output',
                        nargs='?',
                        help='The target output file')
    parser.add_argument('--output-dir',
                        default='.',
                        help="When provided with a directory name to package, "
                             "the directory to write the bundle to, defaults to '.'")
    parser.add_argument('--tar',
                        help='If provided, source is decoded as a tar file',
                        default=False,
                        dest='tar',
                        action='store_true')
    parser.add_argument('source',
                        help='Optional path to a bundle directory or bundle configuration file or tar file.',
                        nargs='?')
    parser.set_defaults(func=shazar)
    return parser


def shazar(args):
    log = logging.getLogger(__name__)

    source_is_tar = args.source is None or args.tar

    with tempfile.NamedTemporaryFile() as zip_file_data:
        source_base_name = None

        with zipfile.ZipFile(zip_file_data, 'w') as zip_file:
            if source_is_tar:
                try:
                    with tarfile.open(fileobj=sys.stdin.buffer, mode='r|') \
                            if args.source is None else tarfile.open(args.source, mode='r') as tar:
                        tar_to_zip(tar, zip_file)

                except tarfile.ReadError:
                    log.error('shazar: input must be in tar format')
                    sys.exit(2)
            else:
                source_base_name = os.path.basename(args.source.rstrip('\\/'))

                if os.path.isdir(args.source):
                    dir_to_zip(args.source, zip_file, source_base_name)
                else:
                    zip_file.write(args.source, source_base_name)

        zip_file_data.seek(0)

        # Per UNIX conventions, if given "-" as a filename that's a way of saying to use stdout. This solves the
        # use-case of outputting to stdout despite giving `shazar` a `source` argument.

        if args.output == '-' or (args.output is None and source_base_name is None):
            write_with_digest(zip_file_data, sys.stdout.buffer)
        elif args.output is not None:
            # write directly to the file here so writing to device nodes like e.g. /dev/null is supported
            with open(args.output, 'wb') as file:
                write_with_digest(zip_file_data, file)
        else:
            with tempfile.NamedTemporaryFile(delete=False) as file:
                hex_digest = write_with_digest(zip_file_data, file)

                dest = args.output if args.output is not None else os.path.join(
                    args.output_dir,
                    '{}-{}.zip'.format(source_base_name, hex_digest)
                )

            shutil.move(file.name, dest)

            if not source_is_tar:
                sys.stdout.write(dest + os.linesep)


def dir_to_zip(dir, zip_file, source_base_name, mtime=None):
    for (dir_path, dir_names, file_names) in os.walk(dir):
        for file_name in file_names:
            path = os.path.join(dir_path, file_name)
            name = os.path.join(source_base_name, os.path.relpath(path, start=dir))

            if mtime is not None:
                os.utime(path, (mtime, mtime))

            zip_file.write(path, name)


def tar_to_zip(tar, zip_file):
    log = logging.getLogger(__name__)

    for entry in tar:
        mtime_to_use = max(entry.mtime, SHAZAR_TIMESTAMP_MIN)

        if entry.isfile():
            with tempfile.NamedTemporaryFile() as entry_file:
                shutil.copyfileobj(tar.extractfile(entry), entry_file)
                entry_file.flush()
                os.utime(entry_file.name, (mtime_to_use, mtime_to_use))
                zip_file.write(entry_file.name, entry.name)
        elif entry.isdir():
            info = zipfile.ZipInfo(entry.name + '/', date_time=time.localtime(mtime_to_use))
            info.create_system = 0
            zip_file.writestr(info, '')
        else:
            log.error('shazar: your archive cannot contain device nodes or symlinks')
            sys.exit(1)


def write_with_digest(input, output):
    digest = hashlib.sha256()

    iterator = iter(partial(input.read, IO_CHUNK_SIZE), b'')

    for chunk in iterator:
        output.write(chunk)
        digest.update(chunk)

    hex_digest = digest.hexdigest()

    output.write(('\nsha-256/' + hex_digest).encode('UTF-8'))

    return hex_digest
