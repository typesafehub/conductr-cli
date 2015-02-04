#!/usr/bin/env python3


import argcomplete
import argparse
from functools import partial
import hashlib
import os
import shutil
import tempfile
import zipfile


def run():
    parser = build_parser()
    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    args.func(args)


def build_parser():
    parser = argparse.ArgumentParser(
        description='Package a bundle directory or bundle configuration file'
    )
    parser.add_argument('--output-dir',
                        default='.',
                        help="The optional output directory, defaults to '.'")
    parser.add_argument('source',
                        help='Path to a bundle directory or bundle configuration file')
    parser.set_defaults(func=shazar)
    return parser


def shazar(args):
    source_base_name = os.path.basename(args.source.rstrip('\\/'))
    temp_file = tempfile.NamedTemporaryFile(suffix='.zip', delete=False).name

    with zipfile.ZipFile(temp_file, 'w') as zip_file:
        if os.path.isdir(args.source):
            for (dir_path, dir_names, file_names) in os.walk(args.source):
                for file_name in file_names:
                    path = os.path.join(dir_path, file_name)
                    name = os.path.join(source_base_name, os.path.relpath(path, start=args.source))
                    zip_file.write(path, name)
        else:
            zip_file.write(args.source, source_base_name)

    dest = shutil.move(
        temp_file,
        os.path.join(args.output_dir, '{}-{}.zip'.format(source_base_name, create_digest(temp_file)))
    )
    print('Created digested ZIP archive at {}'.format(dest))


def create_digest(file_name):
    with open(file_name, mode='rb') as f:
        d = hashlib.sha256()
        for buf in iter(partial(f.read, 128), b''):
            d.update(buf)
    return d.hexdigest()


if __name__ == '__main__':
    run()
