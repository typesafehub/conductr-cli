import json
import os
import shutil
import tempfile

import io
import copy
import logging

import sys

from io import BytesIO

from conductr_cli import control_protocol, bundle_utils, validation, conduct_load, bundle_scale
from conductr_cli.bundle_core_info import BundleCoreInfo
from conductr_cli.exceptions import ConductRestoreError


@validation.handle_connection_error
@validation.handle_http_error
@validation.handle_wait_timeout_error
@validation.handle_conductr_restore_error
def restore(args):
    log = logging.getLogger(__name__)

    isatty = os.isatty(sys.stdin.fileno())
    if args.backup is '-' and isatty:
        raise ConductRestoreError('Specify a backup file. Cannot read from stdin(-)')

    destination_bundles = control_protocol.get_bundles(args)
    destination_bundles_info = BundleCoreInfo.from_bundles(destination_bundles)

    restore_directory = unpack_backup(args.backup)
    bundle_json_file = open(os.path.join(restore_directory, 'bundles.json'), 'r')
    bundles_json = bundle_json_file.read()
    bundle_json_file.close()

    bundles_info = sorted(BundleCoreInfo.from_bundles(json.loads(bundles_json)), key=lambda b: b.start_time)

    restore_errors = []
    for bundle_info in bundles_info:
        new_bundle_id = None
        log.info('Restoring bundle : {}.'.format(bundle_info.bundle_name))

        try:
            new_bundle_id = process_bundle(args, restore_directory, bundle_info)
            log.info('Loaded {} with bundleId : {}'.format(bundle_info.bundle_name, new_bundle_id))
        except:
            restore_errors.append('{} could not be loaded.'.format(bundle_info.bundle_name))

        try:
            if new_bundle_id is not None:
                affinity = compatible_bundle(destination_bundles_info, bundle_info.bundle_name,
                                             bundle_info.compatibility_Version)
                if affinity == new_bundle_id:
                    affinity = None

                scale_bundle(args, new_bundle_id, bundle_info.scale, affinity)
                log.info('Scaled {} to : {}.'.format(new_bundle_id, bundle_info.scale))
        except:
            restore_errors.append('{} could not be scaled.'.format(bundle_info.bundle_name))

    for error in restore_errors:
        log.error(error)

    return len(restore_errors) == 0


def unpack_backup(backup):
    restore_directory = tempfile.mkdtemp()
    isatty = os.isatty(sys.stdin.fileno())
    has_stdin = not isatty

    if backup is '-' and has_stdin:
        buffer = sys.stdin.buffer.read()
        shutil.unpack_archive(BytesIO(buffer), restore_directory, format='zip')
    else:
        shutil.unpack_archive(backup, restore_directory, format='zip')
    return restore_directory


def process_bundle(args, restore_directory, bundle_info: BundleCoreInfo):
    log = logging.getLogger(__name__)

    files = []

    bundle = '{}.zip'.format(bundle_info.bundle_name_with_digest)
    bundle_path = os.path.join(restore_directory, bundle)

    bundle_conf = bundle_utils.conf(bundle_path)
    files.append(('bundleConf', ('bundle.conf', io.StringIO(bundle_conf))))

    bundle_archive = open(bundle_path, 'rb')

    if len(bundle_info.configuration_digest) != 0:
        configuration = '{}.zip'.format(bundle_info.bundle_name_with_configuration_digest)
        bundle_configuration_path = os.path.join(restore_directory, configuration)

        bundle_conf_overlay = bundle_utils.conf(bundle_configuration_path)
        files.append(('bundleConfOverlay', ('bundle.conf', io.StringIO(bundle_conf_overlay))))

        files.append(('bundle', (bundle, bundle_archive)))

        configuration_archive = open(bundle_configuration_path, 'rb')
        files.append(('configuration', (configuration, configuration_archive)))
    else:
        files.append(('bundle', (bundle, bundle_archive)))

    multipart = conduct_load.create_multipart(log, files)
    response = control_protocol.load_bundle(args, multipart)

    return response['bundleId']


def scale_bundle(args, bundle_id, scale, affinity):
    modified_args = copy.deepcopy(args)
    modified_args.wait_timeout = 60
    modified_args.bundle = bundle_id
    modified_args.lines = 10
    modified_args.utc = False
    modified_args.follow = False
    modified_args.affinity = affinity
    modified_args.scale = scale

    response_json = control_protocol.run_bundle(modified_args)

    bundle_scale.wait_for_scale(response_json['bundleId'], scale, wait_for_is_active=True, args=modified_args)


def compatible_bundle(bundle_infos, bundle_name, compatibility_version):
    for bundle_info in bundle_infos:
        if bundle_info.bundle_name == bundle_name and bundle_info.compatibility_Version == compatibility_version:
            return bundle_info.bundle_id
    return None
