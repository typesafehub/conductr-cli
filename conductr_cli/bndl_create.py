from conductr_cli import bndl_oci, validation
from conductr_cli.bndl_oci import oci_bundle_bundle_conf, oci_bundle_unpack, oci_image_bundle_conf, oci_image_unpack
from conductr_cli.bndl_docker import docker_unpack
from conductr_cli.bndl_utils import \
    data_is_bundle_conf, \
    data_is_tar, \
    data_is_zip, \
    detect_format_dir, \
    detect_format_stream, \
    find_bundle_conf_dir, \
    first_mtime, \
    load_bundle_args_into_conf, \
    zip_extract_with_dates
from conductr_cli.constants import BNDL_PEEK_SIZE, IO_CHUNK_SIZE, SHAZAR_TIMESTAMP_MIN
from conductr_cli.shazar_main import dir_to_zip, write_with_digest
from io import BufferedReader, BytesIO
from pyhocon import ConfigException, ConfigFactory, HOCONConverter
import arrow
import logging
import os
import shutil
import sys
import tarfile
import tempfile
import time
import zipfile


@validation.handle_bndl_create_error
def bndl_create(args):
    log = logging.getLogger(__name__)

    if args.source and not (os.path.isfile(args.source) or os.path.isdir(args.source)):
        log.error('bndl: Unable to read {}. Must be the path to a valid file or directory'.format(args.source))

        return 2

    buff_in = BufferedReader(sys.stdin.buffer, IO_CHUNK_SIZE) if args.source is None else None

    if not args.format:
        if not args.source:
            args.format = detect_format_stream(buff_in.peek(BNDL_PEEK_SIZE))
        elif os.path.isdir(args.source):
            args.format = detect_format_dir(args.source)
        elif os.path.isfile(args.source):
            with open(args.source, 'rb') as source_in:
                args.format = detect_format_stream(source_in.read(BNDL_PEEK_SIZE))

    output = open(args.output, 'wb') if args.output else sys.stdout.buffer

    temp_dir = tempfile.mkdtemp()
    input_dir = temp_dir
    component_name = 'component'
    component_dir = os.path.join(temp_dir, component_name)
    mtime = None
    bundle_conf_data = b''

    try:
        process_oci_image = False

        if not args.format:
            log.error('bndl: Unable to detect format. Provide a -f or --format argument')

            return 2
        elif args.format == 'docker':
            component_name = 'oci-image'
            component_dir = os.path.join(temp_dir, component_name)
            os.mkdir(component_dir)

            if not args.source:
                with tarfile.open(fileobj=buff_in, mode='r|') as tar_in:
                    name = docker_unpack(component_dir, tar_in, is_dir=False, maybe_name=args.image_name, maybe_tag=args.image_tag)
            elif os.path.isfile(args.source):
                with tarfile.open(args.source, mode='r') as tar_in:
                    name = docker_unpack(component_dir, tar_in, is_dir=False, maybe_name=args.image_name, maybe_tag=args.image_tag)
            else:
                name = docker_unpack(component_dir, args.source, is_dir=True, maybe_name=args.image_name, maybe_tag=args.image_tag)

            if not name:
                log.error('bndl: Not a Docker image')
                return 3
            elif not args.name:
                args.name = name

            process_oci_image = True
        elif args.format == 'oci-image':
            component_name = 'oci-image'
            component_dir = os.path.join(temp_dir, component_name)
            os.mkdir(component_dir)

            if not args.source:
                with tarfile.open(fileobj=buff_in, mode='r|') as tar_in:
                    valid_image = oci_image_unpack(component_dir, tar_in, is_dir=False)
            elif os.path.isfile(args.source):
                with tarfile.open(args.source, mode='r') as tar_in:
                    valid_image = oci_image_unpack(component_dir, tar_in, is_dir=False)
            else:
                valid_image = oci_image_unpack(component_dir, args.source, is_dir=True)

            if not valid_image:
                log.error('bndl: Not an OCI Image')
                return 2

            process_oci_image = True
        elif args.format == 'bundle':
            peek = buff_in.peek(BNDL_PEEK_SIZE) if args.source is None else None
            peek_file = None

            if args.source and os.path.isfile(args.source):
                with open(args.source, 'rb') as file:
                    peek_file = file.read(BNDL_PEEK_SIZE)

            if not args.source and data_is_zip(peek):
                with tempfile.NamedTemporaryFile() as temp:
                    shutil.copyfileobj(buff_in, temp)
                    temp.seek(0)
                    zip_extract_with_dates(temp, temp_dir)
            elif not args.source and data_is_tar(peek):
                with tarfile.open(fileobj=buff_in, mode='r|') as tar:
                    tar.extractall(temp_dir)
            elif not args.source and data_is_bundle_conf(peek):
                with open(os.path.join(temp_dir, 'bundle.conf'), 'wb') as bundle_conf_fileobj:
                    shutil.copyfileobj(buff_in, bundle_conf_fileobj)
            elif os.path.isdir(args.source):
                os.rmdir(temp_dir)
                shutil.copytree(args.source, temp_dir)
            elif os.path.isfile(args.source) and zipfile.is_zipfile(args.source):
                zip_extract_with_dates(args.source, temp_dir)
            elif os.path.isfile(args.source) and tarfile.is_tarfile(args.source):
                with tarfile.open(args.source) as tar:
                    tar.extractall(temp_dir)
            elif os.path.isfile(args.source) and data_is_bundle_conf(peek_file):
                shutil.copyfile(args.source, os.path.join(temp_dir, 'bundle.conf'))
                mtime = os.path.getmtime(args.source)
            else:
                log.error('bndl: Not a ConductR Bundle')
                return 2

            input_dir = find_bundle_conf_dir(temp_dir)
            bundle_conf_path = os.path.join(input_dir, 'bundle.conf')

            if not input_dir or not os.path.exists(bundle_conf_path):
                log.error(
                    'bndl: Missing bundle.conf (for source {})'.format(
                        'stdin' if args.source is None else args.source
                    )
                )

                return 2

            with open(bundle_conf_path, 'rb') as bundle_conf_fileobj:
                bundle_conf_data = bundle_conf_fileobj.read()

            os.unlink(bundle_conf_path)

            if not args.name:
                try:
                    bundle_conf = ConfigFactory.parse_string(bundle_conf_data.decode('UTF-8'))

                    if 'name' in bundle_conf:
                        args.name = bundle_conf['name']
                except:
                    pass  # ignore exceptions - we'll catch the bad config below
        elif args.format == 'oci-bundle':
            component_name = 'oci-bundle'
            component_dir = os.path.join(temp_dir, component_name)
            os.mkdir(component_dir)

            if not args.source:
                with tarfile.open(fileobj=buff_in, mode='r|') as tar_in:
                    valid_bundle = oci_bundle_unpack(component_dir, tar_in, is_dir=False)
            elif os.path.isfile(args.source):
                with tarfile.open(args.source, mode='r') as tar_in:
                    valid_bundle = oci_bundle_unpack(component_dir, tar_in, is_dir=False)
            else:
                valid_bundle = oci_bundle_unpack(component_dir, args.source, is_dir=True)

            if not valid_bundle:
                log.error('bndl: Not an OCI Runtime Bundle')
                return 2

            if not args.name:
                log.error('bndl: OCI Runtime Bundles require a --name argument to be provided')
                return 2

            bundle_conf = oci_bundle_bundle_conf(args, component_name)
            bundle_conf_data = bundle_conf.encode('UTF-8')

        mtime = first_mtime(input_dir, SHAZAR_TIMESTAMP_MIN) if mtime is None else mtime

        if process_oci_image:
            has_oci_layout = os.path.isfile(os.path.join(component_dir, 'oci-layout'))

            refs_dir = os.path.join(component_dir, 'refs')

            if not args.image_tag and os.path.isdir(refs_dir):
                for ref in os.listdir(refs_dir):
                    args.image_tag = ref
                    break

            ref_exists = args.image_tag and os.path.isfile(os.path.join(refs_dir, args.image_tag))

            if not ref_exists:
                log.error('bndl: Invalid OCI Image. Cannot find requested tag "{}" in OCI Image'.format(args.image_tag))

                return 2

            if not has_oci_layout:
                log.error('bndl: Invalid OCI Image. Missing oci-layout')

                return 2

            oci_manifest, oci_config = bndl_oci.oci_image_extract_manifest_config(component_dir, args.image_tag)
            bundle_conf = oci_image_bundle_conf(args, component_name, oci_manifest, oci_config)
            bundle_conf_data = bundle_conf.encode('UTF-8')

            # bundle data timestamps can vary based on how it's acquired (docker save, our own resolver, etc) so we
            # deterministically set the mtime of the files to be based on the OCI config 'created' value if available

            if oci_config and 'created' in oci_config:
                mtime = arrow.get(oci_config['created']).timestamp

        try:
            bundle_conf = ConfigFactory.parse_string(bundle_conf_data.decode('UTF-8'))
        except ConfigException:
            log.error('bndl: Unable to parse bundle.conf')
            return 1

        load_bundle_args_into_conf(bundle_conf, args, with_defaults=False, validate_components=True)

        bundle_conf_data = HOCONConverter.to_hocon(bundle_conf).encode('UTF-8')
        archive_name = bundle_conf['name'] if 'name' in bundle_conf else 'bundle'
        bundle_conf_name = os.path.join(archive_name, 'bundle.conf')

        if args.use_shazar:
            with tempfile.NamedTemporaryFile() as zip_file_data:
                with zipfile.ZipFile(zip_file_data, 'w') as zip_file:
                    bundle_conf_zinfo = zipfile.ZipInfo(filename=bundle_conf_name, date_time=time.localtime(mtime)[:6])
                    bundle_conf_zinfo.external_attr = 0o644 << 16
                    zip_file.writestr(bundle_conf_zinfo, bundle_conf_data)
                    dir_to_zip(input_dir, zip_file, args.name, mtime)

                zip_file_data.flush()
                zip_file_data.seek(0)

                write_with_digest(zip_file_data, output)
        else:
            with tarfile.open(fileobj=output, mode='w|') as tar:
                info = tarfile.TarInfo(name=bundle_conf_name)
                info.size = len(bundle_conf_data)
                info.mtime = mtime
                tar.addfile(tarinfo=info, fileobj=BytesIO(bundle_conf_data))

                for (dir_path, dir_names, file_names) in os.walk(input_dir):
                    for file_name in file_names:
                        path = os.path.join(dir_path, file_name)
                        name = os.path.join(args.name, os.path.relpath(path, start=input_dir))
                        if not os.path.islink(path):
                            os.utime(path, (mtime, mtime))
                        tar.add(path, arcname=name)

        output.flush()

        return 0
    finally:
        shutil.rmtree(temp_dir)
