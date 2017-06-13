import time
from collections import OrderedDict
from conductr_cli import screen_utils
from conductr_cli.constants import IO_CHUNK_SIZE
from conductr_cli.exceptions import DockerImageMalformedError
from conductr_cli.resolvers.schemes import SCHEME_BUNDLE
from functools import partial
from requests.auth import HTTPBasicAuth
from urllib.parse import urlencode
import gzip
import hashlib
import logging
import os
import json
import re
import requests
import shutil
import tempfile
import www_authenticate


DOCKER_CREDENTIAL_FILE_PATH = '{}/.lightbend/docker.credentials'.format(os.path.expanduser('~'))
DOCKER_PROPERTIES_RE = re.compile('^(\S+)\s*=\s*([\S]+)$')


def supported_schemes():
    return [SCHEME_BUNDLE]


def get_with_token(ns, url, headers=None, raw=False, try_new_token=True):
    if not hasattr(get_with_token, 'latest_token'):
        get_with_token.latest_token = None

    try:
        new_headers = headers.copy() if headers is not None else {}

        if get_with_token.latest_token is not None:
            new_headers['Authorization'] = 'Bearer {}'.format(get_with_token.latest_token)

        response = requests.get(url, stream=raw, headers=new_headers)
        response.raise_for_status()

        if raw:
            response.raw.decode_content = True

        return response
    except requests.exceptions.HTTPError as error:
        if error.response.status_code == 401 and 'Www-Authenticate' in error.response.headers and try_new_token:
            credentials = load_docker_credentials(ns)
            auth_info = www_authenticate.parse(error.response.headers['Www-Authenticate'])

            token_params = {
                'service': auth_info['bearer']['service'],
                'scope': auth_info['bearer']['scope'],
                'client_id': 'Lightbend ConductR'
            }

            if credentials is not None:
                token_params['account'] = credentials[0]
                auth = HTTPBasicAuth(credentials[0], credentials[1])
            else:
                auth = None

            token_url = '{}?{}'.format(auth_info['bearer']['realm'], urlencode(token_params))

            token_response = requests.get(token_url, auth=auth)
            token_response.raise_for_status()
            token_content = json.loads(token_response.text)

            get_with_token.latest_token = token_content['token']

            return get_with_token(ns, url, headers, raw, try_new_token=False)
        else:
            raise error


def fetch_blobs(cache_dir, url, ns, image, blobs, offline_mode):
    log = logging.getLogger(__name__)
    files = {}
    needs_retrieving = []
    downloaded_size = 0
    total_size = 0

    for blob in blobs:
        blob['cache_file'] = os.path.join(cache_dir, 'docker-blob-{}'.format(re.sub('\\W', '_', blob['digest'])))
        blob['cache_file_temp'] = '{}.tmp'.format(blob['cache_file'])

        if not os.path.isfile(blob['cache_file']):
            needs_retrieving.append(strip_digest(blob['digest']))
            total_size += blob['size']

    if len(needs_retrieving) > 0:
        log.info('Retrieving Docker layers:')
        for layer in needs_retrieving:
            log.info('    {}'.format(layer))

    for blob in blobs:
        cache_file = os.path.join(cache_dir, 'docker-blob-{}'.format(re.sub('\\W', '_', blob['digest'])))
        cache_file_temp = '{}.tmp'.format(cache_file)

        if not os.path.isfile(cache_file):
            if offline_mode:
                return None

            prev_time = 0.0

            full_url = 'https://{}/v2/{}/{}/blobs/{}'.format(url, ns, image, blob['digest'])
            response = get_with_token(url, full_url, raw=True)
            with open(cache_file_temp, 'wb') as cache_fileobj:
                for chunk in iter(partial(response.raw.read, IO_CHUNK_SIZE), b''):
                    cache_fileobj.write(chunk)

                    if log.is_progress_enabled():
                        downloaded_size += len(chunk)
                        percent = (downloaded_size * 1.0) / total_size
                        download_complete = percent >= 1.0
                        now_time = time.time()
                        if download_complete or now_time - prev_time >= 0.1:
                            progress_bar_text = screen_utils.progress_bar(percent)
                            log.progress(progress_bar_text, flush=download_complete)
                            prev_time = now_time

            os.rename(cache_file_temp, cache_file)

        files[blob['digest']] = cache_file

    return files


def fetch_manifest(cache_dir, url, ns, image, manifest, offline_mode):
    full_url = 'https://{}/v2/{}/{}/manifests/{}'.format(url, ns, image, manifest)
    full_url_digest = hashlib.sha256(full_url.encode('UTF-8')).hexdigest()
    cache_file = os.path.join(cache_dir, 'docker-manifest-{}'.format(full_url_digest))

    if offline_mode:
        if os.path.isfile(cache_file):
            with open(cache_file, 'r') as cache_fileobj:
                return json.load(cache_fileobj)
        else:
            return None
    else:
        response = get_with_token(url,
                                  full_url,
                                  headers={'Accept': 'application/vnd.docker.distribution.manifest.v2+json'})
        response.raise_for_status()

        with open(cache_file, 'w', encoding="utf-8") as cache_fileobj:
            cache_fileobj.write(response.text)

        return json.loads(response.text)


def strip_digest(value):
    try:
        return value[value.index(':') + 1:]
    except ValueError:
        return value


def parse_uri(uri):
    parts = uri.split('/', 2)
    num_parts = len(parts)

    provided_url = parts[0] if num_parts > 2 else None
    url = provided_url if provided_url is not None else 'registry.hub.docker.com'

    provided_ns = parts[1] if num_parts > 2 else parts[0] if num_parts > 1 else None
    ns = provided_ns if provided_ns is not None else 'library'

    image_parts = (parts[2] if num_parts > 2 else parts[1] if num_parts > 1 else parts[0]).split(':', 1)
    image = image_parts[0]

    provided_tag = image_parts[1] if len(image_parts) > 1 else None
    tag = provided_tag if provided_tag is not None else 'latest'

    return (provided_url, url), (provided_ns, ns), (image, image), (provided_tag, tag)


def resolve_bundle(cache_dir, uri, auth=None):
    return do_resolve_bundle(cache_dir, uri, auth, offline_mode=False)


def do_resolve_bundle(cache_dir, uri, auth, offline_mode):
    (provided_url, url), (provided_ns, ns), (provided_image, image), (provided_tag, tag) = parse_uri(uri)

    temp_dir = tempfile.mkdtemp()

    try:
        manifest = fetch_manifest(cache_dir, url, ns, image, tag, offline_mode)

        if manifest is None:
            return False, None, None, DockerImageMalformedError('{} - unable to find manifest'.format(uri))
        elif 'config' not in manifest or 'layers' not in manifest:
            return False, None, None, DockerImageMalformedError('{} - 1.0 manifests are not supported'.format(uri))

        files = fetch_blobs(cache_dir, url, ns, image, [manifest['config']] + manifest['layers'], offline_mode)

        if files is None:
            return False, None, None, None

        shutil.copyfile(
            files[manifest['config']['digest']],
            os.path.join(temp_dir, strip_digest(manifest['config']['digest']) + '.json')
        )

        layers = []
        layer_digests = []

        for layer in manifest['layers']:
            layer_file = files[layer['digest']]
            digest = hashlib.sha256()
            base_layer_digest = strip_digest(layer['digest'])
            layer_digests.append(base_layer_digest)
            base_layer_name = os.path.join(base_layer_digest, 'layer.tar')
            file_name = os.path.join(temp_dir, base_layer_name)
            os.makedirs(os.path.dirname(file_name))

            with open(file_name, 'wb') as layer_out_file, open(layer_file, 'rb') as layer_in_file:
                if layer['mediaType'].endswith('.gzip'):
                    with gzip.GzipFile(fileobj=layer_in_file.raw, mode='rb') as gzip_file:
                        for chunk in iter(partial(gzip_file.read, IO_CHUNK_SIZE), b''):
                            layer_out_file.write(chunk)
                            digest.update(chunk)
                else:
                    for chunk in iter(partial(layer_in_file.read, IO_CHUNK_SIZE), b''):
                        layer_out_file.write(chunk)
                        digest.update(chunk)

            layers.append(base_layer_name)

        manifests_tag = []
        repositories = {}

        if provided_url is not None and provided_ns is not None and tag is not None:
            manifests_tag.append('{}/{}/{}:{}'.format(provided_url, provided_ns, image, tag))

            if len(layer_digests) > 0:
                repositories['{}/{}/{}'.format(provided_url, provided_ns, image)] = {tag: layer_digests[-1]}
        elif provided_ns is not None and tag is not None:
            manifests_tag.append('{}/{}:{}'.format(provided_ns, image, tag))

            if len(layer_digests) > 0:
                repositories['{}/{}'.format(provided_ns, image)] = {tag: layer_digests[-1]}
        elif tag is not None:
            manifests_tag.append('{}:{}'.format(image, tag))

            if len(layer_digests) > 0:
                repositories[image] = {tag: layer_digests[-1]}

        manifests = [OrderedDict([
            ('Config', '{}.json'.format(strip_digest(manifest['config']['digest']))),
            ('RepoTags', manifests_tag),
            ('Layers', layers)
        ])]

        with open(os.path.join(temp_dir, 'manifest.json'), 'w', encoding="utf-8") as manifest_fileobj:
            manifest_fileobj.write(json.dumps(manifests))

        with open(os.path.join(temp_dir, 'repositories'), 'w', encoding="utf-8") as repositories_fileobj:
            repositories_fileobj.write(json.dumps(repositories))

        return True, None, temp_dir, None
    except Exception as e:
        return False, None, None, e


def load_bundle_from_cache(cache_dir, uri):
    return False, None, None, None


def resolve_bundle_configuration(cache_dir, uri, auth=None):
    return False, None, None, None


def load_bundle_configuration_from_cache(cache_dir, uri):
    return False, None, None, None


def resolve_bundle_version(uri):
    return None, None


def continuous_delivery_uri(resolved_version):
    return None


def is_bundle_name(uri):
    return uri.count('/') == 0 and uri.count('.') == 0


def load_docker_credentials(server):
    log = logging.getLogger(__name__)

    override_path = '{}-{}'.format(DOCKER_CREDENTIAL_FILE_PATH, server)

    if os.path.exists(override_path):
        path = override_path
    elif os.path.exists(DOCKER_CREDENTIAL_FILE_PATH):
        path = DOCKER_CREDENTIAL_FILE_PATH
    else:
        path = None

    if path is None:
            return None
    else:
        with open(path, 'r') as cred_file:
            lines = [line.replace('\n', '') for line in cred_file.readlines()]
            data = dict()
            for line in lines:
                match = DOCKER_PROPERTIES_RE.match(line)
                if match is not None:
                    try:
                        key, value = match.group(1, 2)
                        key = 'user' if key == 'username' else key
                        data[key] = value
                    except IndexError:
                        pass

            if 'user' not in data or 'password' not in data:
                return None

            log.info('Docker credentials loaded from {}'.format(path))

            return data['user'], data['password']
