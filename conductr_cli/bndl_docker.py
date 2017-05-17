from conductr_cli.bndl_utils import DigestReaderWriter, file_write_bytes
import gzip
import hashlib
import json
import os
import shutil
import tempfile


def docker_parse_image_name(name):
    """
    Parses a docker image name into a tuple containing the name and tag. Examples:

    "conductr:latest"           -> "conductr", "latest"
    "lightbend/conductr:latest" -> "conductr", "latest"

    :param name:
    :return:
    """
    image_tag = name.split(':')

    if len(image_tag) != 2:
        raise ValueError('Invalid tag format')

    return os.path.basename(image_tag[0]), image_tag[1]


def docker_image_name_matches(wanted_name, wanted_tag, image_name):
    return \
        (wanted_tag is None or image_name.endswith(':{}'.format(wanted_tag))) and \
        (wanted_name is None or os.path.basename(image_name).startswith('{}:'.format(wanted_name)))


def docker_parse_cmd(line):
    """
    Docker's `CMD` entries have several different funky formats. This parses those. Examples:

    CMD ["/bin/sh" "-c"]
    CMD ["/bin/sh", "-c"]
    CMD "/bin/sh" "-c"
    CMD /bin/sh -c
    CMD /bin/sh "-c"

    :param line: CMD line from docker image
    :return: parsed array of arguments
    """

    args_line = line[3:].strip() if line.startswith('CMD') else ''
    args_brackets = args_line.startswith('[') and args_line.endswith(']')
    args_portion = args_line[1:-1] if args_brackets else args_line

    args = []
    arg = ''
    escaped = False
    quoted = False

    for c in args_portion:
        if quoted and escaped:
            arg += c
            escaped = False
        elif quoted and not escaped:
            if c == '\\':
                escaped = True
            elif c == '"':
                args.append(arg)
                quoted = False
                arg = ''
            else:
                arg += c
        elif not quoted and escaped:
            arg += c
            escaped = False
        else:
            # not quoted and not escaped:

            if c.isspace():
                if arg != '':
                    args.append(arg)
                    arg = ''
            elif c == '"':
                if arg != '':
                    args.append(arg)
                    arg = ''

                quoted = True
            elif c == ',' and args_brackets:
                pass
            elif c == '\\':
                escaped = True
            else:
                arg += c

    if arg != '':
        args.append(arg)

    return args


def docker_config_to_oci_image(manifest, config, sizes, layers_to_digests):
    oci_config = {
        'created': config['created'],
        'architecture': config['architecture'],
        'os': config['os'],
        'config': {
            k: v for k, v in {
                'Env': config['config']['Env'] if 'Env' in config['config'] else None,
                'Cmd': config['config']['Cmd'] if 'Cmd' in config['config'] else None,
                'Entrypoint': config['config']['Entrypoint'] if 'Entrypoint' in config['config'] else None,
                'ExposedPorts': config['config']['ExposedPorts'] if 'ExposedPorts' in config['config'] else None,
                'Volumes': config['config']['Volumes'] if 'Volumes' in config['config'] and
                                                          config['config']['Volumes'] else None,

                'WorkingDir': config['config']['WorkingDir'] if 'WorkingDir' in config['config'] and
                                                                config['config']['WorkingDir'] else None,
                'User': config['config']['User'] if 'User' in config['config'] and
                                                    config['config']['User'] else None,
                'Labels': config['config']['Labels'] if 'Labels' in config['config'] and
                                                        config['config']['Labels'] else None
            }.items()

            if v is not None
        },
        'rootfs': config['rootfs'],
        'history': config['history']
    }

    oci_config_data = json.dumps(oci_config, sort_keys=True).encode('UTF-8')

    digest = hashlib.sha256()
    digest.update(oci_config_data)

    oci_config_digest = digest.hexdigest()

    oci_manifest = {
        'schemaVersion': 2,
        'config': {
            'mediaType': 'application/vnd.oci.image.config.v1+json',
            'size': len(oci_config_data),
            'digest': 'sha256:{}'.format(oci_config_digest)
        },
        'layers': [
            {
                'mediaType': 'application/vnd.oci.image.layer.v1.tar+gzip',
                'size': sizes[layers_to_digests[layer]],
                'digest': 'sha256:{}'.format(layers_to_digests[layer])
            } for layer in manifest['Layers']
        ],
        'annotations': config['config']['Labels'] if 'Labels' in config['config'] and
                                                     config['config']['Labels'] else None
    }

    oci_manifest_data = json.dumps(oci_manifest, sort_keys=True).encode('UTF-8')

    digest = hashlib.sha256()
    digest.update(oci_manifest_data)

    oci_manifest_digest = digest.hexdigest()

    refs = {
        'mediaType': 'application/vnd.oci.image.manifest.v1+json',
        'digest': 'sha256:{}'.format(oci_manifest_digest),
        'size': len(oci_manifest_data)
    }

    refs_data = json.dumps(refs, sort_keys=True).encode('UTF-8')

    digest = hashlib.sha256()
    digest.update(refs_data)

    refs_digest = digest.hexdigest()

    return {
        'config': oci_config_data,
        'config_digest': oci_config_digest,
        'manifest': oci_manifest_data,
        'manifest_digest': oci_manifest_digest,
        'refs': refs_data,
        'refs_digest': refs_digest
    }


def docker_unpack(destination, data, is_dir, maybe_name, maybe_tag):
    temp_dir = tempfile.mkdtemp()

    try:
        os.makedirs(os.path.join(destination, 'blobs/sha256'))
        os.makedirs(os.path.join(destination, 'refs'))

        file_write_bytes(os.path.join(destination, 'oci-layout'), '{"imageLayoutVersion": "1.0.0"}'.encode('UTF-8'))

        layers_to_digests = {}
        symlinks = {}
        digests = {}
        sizes = {}

        def handle_entry(name, fileobj, isdir, isfile, issym, top):
            parent_dir = os.path.dirname(name)
            immediate_parent_dir = os.path.basename(parent_dir)

            if parent_dir != top:
                os.makedirs(os.path.join(temp_dir, 'layers', parent_dir), exist_ok=True)

            file_name = os.path.basename(name)

            if isdir:
                os.makedirs(os.path.join(temp_dir, 'layers', file_name))
            elif isfile and parent_dir == top:
                with open(os.path.join(temp_dir, file_name), 'wb') as dest:
                    shutil.copyfileobj(fileobj, dest)
            elif issym and file_name == 'layer.tar':
                if fileobj.startswith('../'):
                    symlinks[os.path.join(immediate_parent_dir, file_name)] = fileobj[3:]
                else:
                    symlinks[os.path.join(immediate_parent_dir, file_name)] = fileobj
            elif isfile and file_name == 'layer.tar':
                dest_path = os.path.join(temp_dir, 'layers', parent_dir, 'data')

                with open(dest_path, 'wb') as dest_file:
                    dest_file_digest = DigestReaderWriter(dest_file)

                    # TODO investigate if below is still the case
                    # bundles are packaged into zips, so we don't want to compress, but OCI tooling
                    # as of 2017-03-14 is broken for plain tar files; they must be gzip

                    with gzip.GzipFile(fileobj=dest_file_digest, mode='wb', compresslevel=0, mtime=0) as dest:
                        shutil.copyfileobj(fileobj, dest)

                    dest_file_hexdigest = dest_file_digest.digest_out.hexdigest()
                    dest_file_size = dest_file_digest.size_out
                    digests[dest_file_hexdigest] = dest_path
                    sizes[dest_file_hexdigest] = dest_file_size
                    layers_to_digests[os.path.join(immediate_parent_dir, file_name)] = dest_file_hexdigest

                os.renames(dest_path, '{}/blobs/sha256/{}'.format(destination, dest_file_hexdigest))
            else:
                with open(os.path.join(temp_dir, 'layers', parent_dir, file_name), 'wb') as dest:
                    shutil.copyfileobj(fileobj, dest)

        if is_dir:
            for base, dirs, files in os.walk(data):
                for file in files:
                    name = os.path.join(base, file)

                    with open(name, 'rb') as fileobj:
                        handle_entry(name, fileobj, isdir=False, isfile=True, issym=False, top=data)
        else:
            for entry in data:
                if entry.isfile():
                    handle_entry(entry.name, data.extractfile(entry), isdir=False, isfile=True, issym=False, top='')
                elif entry.issym():
                    handle_entry(entry.name, entry.linkname, isdir=False, isfile=False, issym=True, top='')

        for key in symlinks:
            layers_to_digests[key] = layers_to_digests[symlinks[key]]

        contents_dir = None

        for base, dirs, files in os.walk(temp_dir):
            if 'manifest.json' in files:
                contents_dir = base
                break

        if contents_dir is None:
            return None
        else:
            with open(os.path.join(contents_dir, 'manifest.json'), 'r') as manifest_file:
                manifests = json.load(manifest_file)
                manifest = None

                for m in manifests:
                    if m['RepoTags'] and \
                            any(t for t in m['RepoTags'] if docker_image_name_matches(maybe_name, maybe_tag, t)):
                        manifest = m
                        break

                if manifest is None:
                    return None
                else:
                    image_name, image_tag = docker_parse_image_name(manifest['RepoTags'][0])

                    with open(os.path.join(contents_dir, manifest['Config'])) as config_file:
                        config = json.load(config_file)

                        oci_spec = docker_config_to_oci_image(manifest, config, sizes, layers_to_digests)

                        file_write_bytes(
                            '{}/blobs/sha256/{}'.format(destination, oci_spec['config_digest']),
                            oci_spec['config']
                        )

                        file_write_bytes(
                            '{}/blobs/sha256/{}'.format(destination, oci_spec['manifest_digest']),
                            oci_spec['manifest']
                        )

                        file_write_bytes(
                            '{}/refs/{}'.format(destination, image_tag),
                            oci_spec['refs']
                        )

                    return image_name
    finally:
        shutil.rmtree(temp_dir)
