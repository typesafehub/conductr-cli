#!/usr/bin/env python3


import argcomplete
import argparse
from functools import partial
import hashlib
import os
import shutil
import tarfile
import tempfile


def shatar(args):

    # Remove trailing forward and backward slashes from the source path.
    # This is needed for basename and tarfile.add functions.
    source = args.source.rstrip("\\/")

    temp = tempfile.NamedTemporaryFile(mode='w+b', delete=False)
    with tarfile.open(fileobj=temp, mode="w:gz") as tgz:
        tgz.add(source, arcname=os.path.basename(source))

    temp_name = temp.name
    temp.close()

    shatar_name = os.path.basename(source)
    shatar_digest = digest_file(temp_name)
    shatar_filename = "%s-%s.tgz" % (shatar_name, shatar_digest)

    shutil.move(temp_name, os.path.join(args.output_dir, shatar_filename))


def digest_file(filename):
    with open(filename, mode='rb') as f:
        d = hashlib.sha256()
        for buf in iter(partial(f.read, 128), b''):
            d.update(buf)
    return d.hexdigest()


def build_parser():
    parser = argparse.ArgumentParser(description="Package a directory that has a structure of a bundle or bundle's configuration file.")
    parser.add_argument('--output-dir',
                        default='.',
                        help="The optional output directory, defaults to '.'")
    parser.add_argument('source',
                        help="Path to a directory that has a structure of a bundle or a bundle's configuration file.")
    parser.set_defaults(func=shatar)

    return parser


def run():
    parser = build_parser()
    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    run()
