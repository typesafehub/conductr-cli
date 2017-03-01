import argcomplete
import argparse
from functools import partial
from conductr_cli import logging_setup
import hashlib
import logging
import os
import shutil
import sys
import tempfile
import zipfile


READ_SIZE_BYTES = 32768


def run(argv=None):
    parser = build_parser()
    argcomplete.autocomplete(parser)
    args = parser.parse_args(argv)
    logging_setup.configure_logging(args)
    args.func(args)


def build_parser():
    parser = argparse.ArgumentParser(
        description='Package a bundle directory or bundle configuration file'
    )
    parser.add_argument('--output-dir',
                        default='.',
                        help="The optional output directory, defaults to '.'")
    parser.add_argument('source',
                        help='Path to a bundle directory or bundle configuration file. If absent, stream from stdin.',
                        nargs='?')
    parser.set_defaults(func=shazar)
    return parser


def shazar(args):
    log = logging.getLogger(__name__)

    # shazar has a standard zip-based format for directories that encodes
    # the digest of a file in its file name.

    # When reading from stdin, however,  it embeds this digest at the end
    # of stdout.

    # In this case, shazar pipes the input to stdout and when finished
    # also writes the digest. This means the output stream will always
    # be 32 bytes longer than the input stream. To verify the digest of a stream,
    # consuming programs that expect a streaming shazar format can
    # calculate a running digest as they consume the stream
    # simply decode the digest from the last 32 bytes of the stream
    # and then check the rest of the stream.

    if args.source is None:
        done = False
        d = hashlib.sha256()

        while not done:
            buf = sys.stdin.buffer.read(READ_SIZE_BYTES)

            if buf == b'':
                sys.stdout.buffer.write(d.digest())
                done = True
            else:
                sys.stdout.buffer.write(buf)
                d.update(buf)
    else:
        source_base_name = os.path.basename(args.source.rstrip('\\/'))
        # Create an empty tempfile
        temp_file = tempfile.NamedTemporaryFile(suffix='.zip', delete=False)
        temp_file.close()
        temp_file_name = temp_file.name

        with zipfile.ZipFile(temp_file_name, 'w') as zip_file:
            if os.path.isdir(args.source):
                for (dir_path, dir_names, file_names) in os.walk(args.source):
                    for file_name in file_names:
                        path = os.path.join(dir_path, file_name)
                        name = os.path.join(source_base_name, os.path.relpath(path, start=args.source))
                        zip_file.write(path, name)
            else:
                zip_file.write(args.source, source_base_name)

        dest = os.path.join(args.output_dir, '{}-{}.zip'.format(source_base_name, create_digest(temp_file_name)))
        shutil.move(temp_file_name, dest)
        log.info('Created digested ZIP archive at {}'.format(dest))


def create_digest(file_name):
    with open(file_name, mode='rb') as f:
        d = hashlib.sha256()
        for buf in iter(partial(f.read, READ_SIZE_BYTES), b''):
            d.update(buf)
    return d.hexdigest()
