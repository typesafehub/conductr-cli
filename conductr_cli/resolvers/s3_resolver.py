from conductr_cli import screen_utils
from conductr_cli.exceptions import S3InvalidArtefactError, S3MalformedUrlError
from conductr_cli.resolvers.schemes import SCHEME_S3
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound
from urllib.parse import urlparse
import boto3
import logging
import os
import shutil
import time


DATA_READ_CHUNK_SIZE = 128


def supported_schemes():
    return [SCHEME_S3]


def resolve_bundle(cache_dir, uri):
    return resolve_s3_object(cache_dir, uri)


def load_bundle_from_cache(cache_dir, uri):
    return resolve_s3_object_from_cache(cache_dir, uri)


def resolve_bundle_configuration(cache_dir, uri):
    return resolve_s3_object(cache_dir, uri)


def load_bundle_configuration_from_cache(cache_dir, uri):
    return resolve_s3_object_from_cache(cache_dir, uri)


def resolve_bundle_version(uri):
    return None


def continuous_delivery_uri(resolved_version):
    return None


def resolve_s3_object(cache_dir, uri):
    if not is_s3_url(uri):
        return False, None, None, None

    try:
        bucket_name, s3_key_name = s3_bucket_and_key_from_uri(uri)
        if bucket_name and s3_key_name:
            return download_from_s3(cache_dir, bucket_name, s3_key_name)
        else:
            error = S3MalformedUrlError('Unable to derive S3 bucket and key from {}'.format(uri))
            return False, None, None, error
    except NoCredentialsError as e:
        return False, None, None, e


def resolve_s3_object_from_cache(cache_dir, uri):
    log = logging.getLogger(__name__)

    if not is_s3_url(uri):
        return False, None, None, None

    bucket_name, s3_key_name = s3_bucket_and_key_from_uri(uri)
    if s3_key_name:
        artefact_name = os.path.basename(s3_key_name)
        cached_artefact = os.path.join(cache_dir, artefact_name)
        if os.path.exists(cached_artefact):
            log.info('Retrieving from cache {}'.format(cached_artefact))
            return True, artefact_name, cached_artefact, None

    return False, None, None, None


def s3_bucket_and_key_from_uri(uri):
    if is_s3_url(uri):
        parsed = urlparse(uri)
        bucket_name = parsed.netloc
        uri_parts = [path for path in parsed.path.split('/') if path]
        if len(uri_parts) > 0:
            s3_key = '/'.join(uri_parts)
            return bucket_name, s3_key

    return None, None


def is_s3_url(uri):
    return urlparse(uri).scheme == SCHEME_S3


def download_from_s3(cache_dir, bucket_name, s3_key_name):
    log = logging.getLogger(__name__)
    client = create_s3_client()
    try:
        artefact = client.get_object(Bucket=bucket_name, Key=s3_key_name)

        validate_artefact(artefact)

        artefact_file_name = os.path.basename(s3_key_name)
        cached_file = os.path.join(cache_dir, artefact_file_name)
        cached_file_tmp = '{}.tmp'.format(cached_file)

        artefact_size = artefact['ContentLength']
        artefact_data = artefact['Body']

        log.info('Retrieving {}://{}{}'.format(SCHEME_S3, bucket_name, s3_key_name))
        save_artefact_data_to_file(artefact_size, artefact_data, cached_file_tmp)
        shutil.move(cached_file_tmp, cached_file)

        return True, artefact_file_name, cached_file, None
    except (ClientError, S3InvalidArtefactError) as e:
        return False, None, None, e


def validate_artefact(artefact):
    if 'ContentLength' not in artefact:
        raise S3InvalidArtefactError('Unable to find \'ContentLength\' in the S3 artefact metadata')
    elif artefact['ContentLength'] <= 0:
        raise S3InvalidArtefactError('Artefact ContentLength must not be zero')
    elif 'ContentType' not in artefact:
        raise S3InvalidArtefactError('Unable to find \'ContentType\' in the S3 artefact metadata')
    elif artefact['ContentType'] != 'application/zip':
        raise S3InvalidArtefactError('Invalid content type \'{}\''.format(artefact['ContentType']))
    elif 'Body' not in artefact:
        raise S3InvalidArtefactError('Unable to find artefact data')


def save_artefact_data_to_file(artefact_size, artefact_data, file_path):
    try:
        log = logging.getLogger(__name__)

        parent_dir = os.path.abspath(os.path.join(file_path, os.pardir))
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir, mode=0o700)

        if os.path.exists(file_path):
            os.remove(file_path)

        with open(file_path, mode='bw') as f:
            downloaded_size = 0
            prev_time = time.time()

            while downloaded_size < artefact_size:
                chunk = artefact_data.read(DATA_READ_CHUNK_SIZE)
                chunk_length = len(chunk)
                downloaded_size += chunk_length
                if chunk_length > 0:
                    f.write(chunk)

                now_time = time.time()
                upload_complete = downloaded_size >= artefact_size
                if upload_complete or now_time - prev_time >= 0.1:
                    percent = 1.0 if upload_complete else downloaded_size * 1.0 / artefact_size
                    progress_bar_text = screen_utils.progress_bar(percent)
                    log.progress(progress_bar_text, flush=upload_complete)
                    prev_time = now_time

        return file_path
    finally:
        artefact_data.close()


def create_s3_client():
    log = logging.getLogger(__name__)
    try:
        session = boto3.Session(profile_name='conductr')
        log.info('Using S3 \'conductr\' profile')
        return session.client('s3')
    except ProfileNotFound:
        session = boto3.Session()
        log.info('Using S3 \'default\' profile')
        return session.client('s3')
