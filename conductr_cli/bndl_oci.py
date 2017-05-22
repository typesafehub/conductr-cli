from pyhocon import HOCONConverter, ConfigFactory, ConfigTree
from conductr_cli.bndl_utils import load_bundle_args_into_conf, create_check_hocon
import hashlib
import json
import os
import re
import shutil
import tempfile


def oci_config_to_image(oci_config, layers, annotations):
    oci_config_text = json.dumps(oci_config, sort_keys=True)
    oci_config_data = oci_config_text.encode('UTF-8')

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
        'layers': layers,
        'annotations': annotations
    }

    oci_manifest_text = json.dumps(oci_manifest, sort_keys=True)
    oci_manifest_data = oci_manifest_text.encode('UTF-8')

    digest = hashlib.sha256()
    digest.update(oci_manifest_data)

    oci_manifest_digest = digest.hexdigest()

    refs = {
        'mediaType': 'application/vnd.oci.image.manifest.v1+json',
        'digest': 'sha256:{}'.format(oci_manifest_digest),
        'size': len(oci_manifest_data)
    }

    refs_text = json.dumps(refs, sort_keys=True)
    refs_data = refs_text.encode('UTF-8')

    digest = hashlib.sha256()
    digest.update(refs_data)

    refs_digest = digest.hexdigest()

    return {
        'config_obj': oci_config,
        'config_text': oci_config_text,
        'config': oci_config_data,
        'config_digest': oci_config_digest,
        'manifest_obj': oci_manifest,
        'manifest_text': oci_manifest_text,
        'manifest': oci_manifest_data,
        'manifest_digest': oci_manifest_digest,
        'refs_obj': refs,
        'refs_text': refs_text,
        'refs': refs_data,
        'refs_digest': refs_digest
    }


def oci_image_bundle_conf(args, component_name, oci_manifest, oci_config):
    conf = ConfigFactory.parse_string('')
    load_bundle_args_into_conf(conf, args, with_defaults=True, validate_components=False)

    annotations_tree = conf.get('annotations')

    if 'annotations' in oci_manifest and oci_manifest['annotations'] is not None:
        for key in sorted(oci_manifest['annotations']):
            annotations_tree.put(key, oci_manifest['annotations'][key])

    annotations_tree.put('com.lightbend.conductr.oci-image-tags.{}'.format(component_name), args.image_tag)

    endpoints_tree = ConfigTree()

    oci_tree = ConfigTree()
    oci_tree.put('description', args.component_description)
    oci_tree.put('file-system-type', 'oci-image')
    oci_tree.put('start-command', [])
    oci_tree.put('endpoints', endpoints_tree)

    components_tree = ConfigTree()
    components_tree.put(component_name, oci_tree)

    if args.use_default_endpoints and 'config' in oci_config and 'ExposedPorts' in oci_config['config']:
        check_arguments = ['--any-address']

        for exposed_port in sorted(oci_config['config']['ExposedPorts']):
            type_parts = exposed_port.split('/', 1)

            port = int(type_parts[0])
            protocol = type_parts[1] if len(type_parts) > 1 else 'tcp'
            name = '{}-{}-{}'.format(component_name, protocol, port)
            check_arguments.append('${}_HOST'.format(re.sub('\\W', '_', name.upper())))

            entry_tree = ConfigTree()
            entry_tree.put('bind-protocol', protocol)
            entry_tree.put('bind-port', port)
            entry_tree.put('service-name', name)

            endpoints_tree.put(name, entry_tree)

        if args.use_default_check and check_arguments:
            oci_check_tree = create_check_hocon(check_arguments)

            components_tree = ConfigTree()
            components_tree.put(component_name, oci_tree)
            components_tree.put('bundle-status', oci_check_tree)

    conf.put('components', components_tree)

    return HOCONConverter.to_hocon(conf)


def oci_image_extract_manifest_config(dir, tag):
    refs_path = os.path.join(dir, 'refs', tag)

    if os.path.isfile(refs_path):
        with open(refs_path, 'r') as refs_file:
            refs_json = json.load(refs_file)

        if 'digest' in refs_json:
            manifest_parts = refs_json['digest'].split(':', 1)
            manifest_path = os.path.join(dir, 'blobs', manifest_parts[0], manifest_parts[1])

            if os.path.isfile(manifest_path):
                with open(manifest_path, 'r') as manifest_file:
                    manifest_json = json.load(manifest_file)

                if 'config' in manifest_json and 'digest' in manifest_json['config']:
                    config_parts = manifest_json['config']['digest'].split(':', 1)

                    config_path = os.path.join(dir, 'blobs', config_parts[0], config_parts[1])

                    if os.path.isfile(config_path):
                        with open(config_path, 'r') as config_file:
                            return manifest_json, json.load(config_file)

    return {}, {}


def oci_image_unpack(destination, data, is_dir):
    temp_dir = tempfile.mkdtemp()

    try:
        if is_dir:
            shutil.copytree(data, os.path.join(temp_dir, 'image'))
        else:
            data.extractall(temp_dir)

        for base, dirs, files in os.walk(temp_dir):
            if 'oci-layout' in files or 'refs' in dirs:
                os.renames(base, destination)
                return True

        return False
    finally:
        if os.path.isdir(temp_dir):
            shutil.rmtree(temp_dir)
