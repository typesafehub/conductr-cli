from pyhocon import HOCONConverter, ConfigFactory, ConfigTree
from conductr_cli.bndl_utils import create_check_hocon
from conductr_cli.constants import BNDL_DEFAULT_CHECK_RETRY_COUNT, BNDL_DEFAULT_CHECK_RETRY_DELAY
import json
import os
import re
import shutil
import tempfile


def oci_image_bundle_conf(args, component_name, oci_manifest, oci_config):
    annotations_tree = ConfigTree()

    if 'annotations' in oci_manifest and oci_manifest['annotations'] is not None:
        for key in sorted(oci_manifest['annotations']):
            annotations_tree.put(key, oci_manifest['annotations'][key])

    annotations_tree.put('com.lightbend.conductr.oci-image-tags.{}'.format(component_name), args.image_tag)

    endpoints_tree = ConfigTree()

    oci_tree = ConfigTree()
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
            check_arguments.append(
                '${}_HOST?retry-delay={}&retry-count={}'.format(
                    re.sub('\\W', '_', name.upper()),
                    BNDL_DEFAULT_CHECK_RETRY_DELAY,
                    BNDL_DEFAULT_CHECK_RETRY_COUNT
                )
            )

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

    if args.use_default_volumes and 'config' in oci_config and 'Volumes' in oci_config['config']:
        volumes = ConfigTree()
        for vol_path in sorted(oci_config['config']['Volumes'].keys()):
            key = 'volume{}'.format(re.sub(r'\W+', '-', vol_path))
            volumes.put(key, vol_path)
        oci_tree.put('volumes', volumes)

    conf = ConfigFactory.parse_string('')
    conf.put('annotations', annotations_tree)
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
