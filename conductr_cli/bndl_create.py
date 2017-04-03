from conductr_cli.bndl_oci import oci_image_bundle_conf, oci_image_extract_manifest_config, oci_image_unpack
from conductr_cli.bndl_docker import docker_unpack
from conductr_cli.bndl_utils import detect_format_dir, detect_format_stream
from conductr_cli.constants import BNDL_PEEK_SIZE, IO_CHUNK_SIZE
from conductr_cli.shazar_main import dir_to_zip, write_with_digest
from io import BufferedReader, BytesIO
import logging
import os
import shutil
import sys
import tarfile
import tempfile
import zipfile


def bndl_create(args):
    log = logging.getLogger(__name__)

    if args.source is not None and not (os.path.isfile(args.source) or os.path.isdir(args.source)):
        log.error('bndl: Unable to read {}. Must be the path to a valid file or directory'.format(args.source))

        return 2

    buff_in = BufferedReader(sys.stdin.buffer, IO_CHUNK_SIZE)

    if args.format is None:
        if args.source is None:
            args.format = detect_format_stream(buff_in.peek(BNDL_PEEK_SIZE))
        elif os.path.isdir(args.source):
            args.format = detect_format_dir(args.source)
        elif os.path.isfile(args.source):
            with open(args.source, 'rb') as source_in:
                args.format = detect_format_stream(source_in.read(BNDL_PEEK_SIZE))

    output = sys.stdout.buffer if args.output is None else open(args.output, 'wb')

    temp_dir = tempfile.mkdtemp()

    component_name = 'oci-image'

    oci_image_dir = os.path.join(temp_dir, component_name)

    os.mkdir(oci_image_dir)

    try:
        if args.format is None:
            log.error('bndl: Unable to detect format. Provide a -f or --format argument')

            return 2
        elif args.format == 'docker':
            if args.source is None:
                with tarfile.open(fileobj=buff_in, mode='r|') as tar_in:
                    name = docker_unpack(oci_image_dir, tar_in, is_dir=False, maybe_name=args.name, maybe_tag=args.tag)
            elif os.path.isfile(args.source):
                with tarfile.open(args.source, mode='r') as tar_in:
                    name = docker_unpack(oci_image_dir, tar_in, is_dir=False, maybe_name=args.name, maybe_tag=args.tag)
            else:
                name = docker_unpack(oci_image_dir, args.source, is_dir=True, maybe_name=args.name, maybe_tag=args.tag)

            if name is None:
                log.error('bndl: Not a Docker image')
                return 3
            elif args.name is None:
                args.name = name
        elif args.format == 'oci-image':
            if args.name is None:
                log.error('bndl: OCI Image support requires that you provide a --name argument')
                return 2
            elif args.source is None:
                with tarfile.open(fileobj=buff_in, mode='r|') as tar_in:
                    valid_image = oci_image_unpack(oci_image_dir, tar_in, is_dir=False)
            elif os.path.isfile(args.source):
                with tarfile.open(args.source, mode='r') as tar_in:
                    valid_image = oci_image_unpack(oci_image_dir, tar_in, is_dir=False)
            else:
                valid_image = oci_image_unpack(oci_image_dir, args.source, is_dir=True)

            if not valid_image:
                log.error('bndl: Not an OCI Image')
                return 2

        has_oci_layout = os.path.isfile(os.path.join(oci_image_dir, 'oci-layout'))

        refs_dir = os.path.join(oci_image_dir, 'refs')

        if args.tag is None and os.path.isdir(refs_dir):
            for ref in os.listdir(refs_dir):
                args.tag = ref
                break

        ref_exists = args.tag is not None and os.path.isfile(os.path.join(refs_dir, args.tag))

        if not ref_exists:
            log.error('bndl: Invalid OCI Image. Cannot find requested tag "{}" in OCI Image'.format(args.tag))

            return 2

        if not has_oci_layout:
            log.error('bndl: Invalid OCI Image. Missing oci-layout')

            return 2

        oci_manifest, oci_config = oci_image_extract_manifest_config(oci_image_dir, args.tag)
        bundle_conf = oci_image_bundle_conf(args, component_name, oci_manifest, oci_config)
        bundle_conf_name = os.path.join(args.name, 'bundle.conf')
        bundle_conf_data = bundle_conf.encode('UTF-8')

        # bundle.conf must be written first, so we explicitly do that for zip and tar

        if args.use_shazar:
            with tempfile.NamedTemporaryFile() as zip_file_data:
                with zipfile.ZipFile(zip_file_data, 'w') as zip_file:
                    zip_file.writestr(bundle_conf_name, bundle_conf_data)
                    dir_to_zip(temp_dir, zip_file, args.name)

                zip_file_data.flush()
                zip_file_data.seek(0)

                write_with_digest(zip_file_data, output)
        else:
            with tarfile.open(fileobj=output, mode='w|') as tar:
                info = tarfile.TarInfo(name=bundle_conf_name)
                info.size = len(bundle_conf_data)
                tar.addfile(tarinfo=info, fileobj=BytesIO(bundle_conf_data))

                for (dir_path, dir_names, file_names) in os.walk(temp_dir):
                    for file_name in file_names:
                        path = os.path.join(dir_path, file_name)
                        name = os.path.join(args.name, os.path.relpath(path, start=temp_dir))
                        tar.add(path, arcname=name)

        output.flush()

        return 0
    finally:
        shutil.rmtree(temp_dir)
