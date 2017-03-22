from pyhocon import HOCONConverter, ConfigFactory, ConfigTree
from conductr_cli.bndl_utils import load_bundle_args_into_conf
import os
import shutil
import tempfile


def oci_image_bundle_conf(args, component_name):
    conf = ConfigFactory.parse_string('')
    load_bundle_args_into_conf(conf, args)

    oci_tree = ConfigTree()
    oci_tree.put('description', args.component_description)
    oci_tree.put('file-system-type', 'oci-image')
    oci_tree.put('start-command', ['ociImageTag', args.tag])
    oci_tree.put('endpoints', {})

    components_tree = ConfigTree()
    components_tree.put(component_name, oci_tree)

    conf.put('components', components_tree)

    return HOCONConverter.to_hocon(conf)


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
