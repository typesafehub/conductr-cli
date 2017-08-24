import hashlib
import json
import logging
import os
import sys
import tempfile
import zipfile
from shutil import rmtree

import requests
from requests_toolbelt import MultipartDecoder

from conductr_cli import conduct_url, conduct_request, validation, control_protocol
from conductr_cli.bndl_utils import file_write_bytes, file_write_string
from conductr_cli.bundle_core_info import BundleCoreInfo
from conductr_cli.conduct_info_inspect import filter_bundles_by_id_or_name
from conductr_cli.conduct_url import conductr_host
from conductr_cli.exceptions import ConductBackupError
from conductr_cli.http import DEFAULT_HTTP_TIMEOUT
from conductr_cli.shazar_main import dir_to_zip, write_with_digest


@validation.handle_connection_error
@validation.handle_http_error
@validation.handle_wait_timeout_error
@validation.handle_conductr_backup_error
def backup(args):
    bundle_id_or_name = args.bundle
    backup_directory = tempfile.mkdtemp()

    try:
        initial_bundles_json = control_protocol.get_bundles(args)
        initial_bundle_core_info = BundleCoreInfo.from_bundles(initial_bundles_json)

        if not bundle_id_or_name:

            for info in initial_bundle_core_info:
                backup_bundle(args, backup_directory, info)

            final_bundles_json = control_protocol.get_bundles(args)
            final_bundle_core_info = BundleCoreInfo.from_bundles(final_bundles_json)

            process_removed_bundles(backup_directory, initial_bundle_core_info, final_bundle_core_info)
            process_added_bundles(args, backup_directory, initial_bundle_core_info, final_bundle_core_info)
            backup_bundle_json(backup_directory, json.dumps(final_bundles_json))

        else:
            bundle_info = BundleCoreInfo.filter_by_bundle_id(initial_bundle_core_info, bundle_id_or_name)

            if not bundle_info:
                raise ConductBackupError('Bundle {} was not found.'.format(bundle_id_or_name))

            filtered_bundle = filter_bundles_by_id_or_name(initial_bundles_json, bundle_id_or_name)
            backup_bundle_json(backup_directory, json.dumps(filtered_bundle))
            backup_bundle(args, backup_directory, bundle_info)

        backup_members(args, backup_directory)
        backup_agents(args, backup_directory)

        compress_backup(args.output_path, backup_directory)

    finally:
        remove_backup_directory(backup_directory)
    return True


def compress_backup(output_path, backup_directory):
    log = logging.getLogger(__name__)

    if sys.stdout.isatty() and output_path is None:
        log.error('conduct backup: Refusing to write to terminal. Provide -o or redirect elsewhere')
        sys.exit(2)

    output_file = open(output_path, 'wb') if output_path else sys.stdout.buffer
    with tempfile.NamedTemporaryFile() as zip_file_data:
        with zipfile.ZipFile(zip_file_data, 'w') as zip_file:
            dir_to_zip(backup_directory, zip_file, '.', None)
        zip_file_data.flush()
        zip_file_data.seek(0)

        write_with_digest(zip_file_data, output_file)
    output_file.flush()


def process_removed_bundles(backup_path, initial_bundle_core_info, final_bundle_core_info):
    bundles_removed = BundleCoreInfo.diff(initial_bundle_core_info, final_bundle_core_info)
    for bundle_info in bundles_removed:
        remove_bundle(backup_path, bundle_info)


def process_added_bundles(args, backup_path, initial_bundle_core_info, final_bundle_core_info):
    bundles_added = BundleCoreInfo.diff(final_bundle_core_info, initial_bundle_core_info)
    for bundle_info in bundles_added:
        backup_bundle(args, backup_path, bundle_info)


def backup_bundle(args, backup_path, bundle_core_info: BundleCoreInfo):
    log = logging.getLogger(__name__)
    log.debug('Processing bundle : {}'.format(bundle_core_info.bundle_id))

    bundle_files_response = bundle_files(args, bundle_core_info.bundle_id)
    bundle_validated = backup_bundle_file(backup_path, bundle_files_response[0], bundle_core_info)
    bundle_conf_validated = True

    # the config is also present
    if len(bundle_files_response) == 2:
        bundle_conf_validated = backup_bundle_conf(backup_path, bundle_files_response[1], bundle_core_info)

    validation_failed = bundle_validated is False or bundle_conf_validated is False
    if validation_failed:
        raise ConductBackupError('Digest validations failed for {}'.format(bundle_core_info.bundle_id))


def backup_members(args, backup_path):
    members_info = json.dumps(control_protocol.get_members(args))
    members_json_path = os.path.join(backup_path, 'members.json')
    file_write_string(members_json_path, members_info)


def backup_agents(args, backup_path):
    agents_info = json.dumps(control_protocol.get_agents(args))
    agents_info_path = os.path.join(backup_path, 'agents.json')
    file_write_string(agents_info_path, agents_info)


def remove_bundle(backup_path, bundle_info: BundleCoreInfo):
    try:
        bundle_file_path = '{}.zip'.format(os.path.join(backup_path, bundle_info.bundle_name_with_digest))
        bundle_conf_path = '{}.zip'.format(os.path.join(backup_path, bundle_info.configuration_digest))
        os.remove(bundle_file_path)
        os.remove(bundle_conf_path)
    except OSError as err:
        error_message = 'Error rolling back Bundle {} from backup.'.format(bundle_info.bundle_id)
        raise ConductBackupError(error_message, err)


def backup_bundle_json(backup_path, bundle_data):
    bundles_json_path = os.path.join(backup_path, 'bundles.json')
    file_write_string(bundles_json_path, bundle_data)


def backup_bundle_file(backup_path, bundle_file, bundle_info):
    bundle_file_path = '{}.zip'.format(os.path.join(backup_path, bundle_info.bundle_name_with_digest))
    file_write_bytes(bundle_file_path, bundle_file)
    return validate_artifact(bundle_file_path, bundle_info.bundle_digest)


def backup_bundle_conf(backup_path, bundle_conf, bundle_info):
    bundle_conf_path = '{}.zip'.format(os.path.join(backup_path, bundle_info.bundle_name_with_configuration_digest))
    file_write_bytes(bundle_conf_path, bundle_conf)
    bundle_conf_validated = validate_artifact(bundle_conf_path, bundle_info.configuration_digest)
    return bundle_conf_validated


def bundle_files(args, bundle_id):
    url = conduct_url.url('bundles/{}'.format(bundle_id), args)
    response = conduct_request.get(args.dcos_mode, conductr_host(args), url, auth=args.conductr_auth,
                                   verify=args.server_verification_file, timeout=DEFAULT_HTTP_TIMEOUT,
                                   headers={'Accept': 'multipart/form-data'})

    result = []
    # ensure that the bundle hasn't been unloaded
    if requests.codes.not_found != response.status_code:
        validation.raise_for_status_inc_3xx(response)
        multipart_data = MultipartDecoder.from_response(response)
        for part in multipart_data.parts:
            result.append(part.content)
    else:
        raise ConductBackupError('Bundle was not found.')

    return result


def remove_backup_directory(backup_path):
    rmtree(backup_path)


def validate_artifact(file_path, digest):
    log = logging.getLogger(__name__)

    validated = compare_digest(file_path, digest)

    if not validated:
        log.error('digest validation failed')
        return False
    return True


def compare_digest(input_file, digest):
    buffer_size = 65536
    sha256 = hashlib.sha256()
    with open(input_file, 'rb') as open_file:
        while True:
            data = open_file.read(buffer_size)
            if not data:
                break
            sha256.update(data)

    return sha256.hexdigest() == digest
