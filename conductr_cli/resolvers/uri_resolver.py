from conductr_cli.resolvers.schemes import SCHEME_FILE, SCHEME_HTTP, SCHEME_HTTPS
from urllib.request import urlretrieve
from urllib.parse import ParseResult, urlparse, urlunparse
from urllib.error import URLError
from pathlib import Path

import time

from conductr_cli import screen_utils
from conductr_cli.resolvers.resolvers_util import is_local_file
import os
import logging
import shutil
import urllib


def supported_schemes():
    return [SCHEME_FILE, SCHEME_HTTP, SCHEME_HTTPS]


def resolve_bundle(cache_dir, uri, auth=None):
    return resolve_file(cache_dir, uri, auth)


def resolve_file(cache_dir, uri, auth=None, require_bundle_conf=True, raise_error=False):
    log = logging.getLogger(__name__)

    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir, mode=0o700)

    try:
        file_protocol = 'file://'
        file_name, file_url = get_url(uri)

        if file_url.startswith(file_protocol):
            file_path = file_url[len(file_protocol):]

            if is_local_file(file_path, require_bundle_conf=require_bundle_conf):
                return True, file_name, file_path, None

        cached_file = cache_path(cache_dir, uri)
        tmp_download_path = '{}.tmp'.format(cached_file)

        if os.path.exists(tmp_download_path):
            os.remove(tmp_download_path)

        download_bundle(log, file_url, tmp_download_path, auth)

        os.chmod(tmp_download_path, 0o600)
        shutil.move(tmp_download_path, cached_file)
        return True, file_name, cached_file, None
    except URLError as e:
        if raise_error:
            raise e
        else:
            return False, None, None, e


def load_bundle_from_cache(cache_dir, uri):
    # When the supplied uri is a local filesystem, don't load from cache so file can be used as is
    parsed = urlparse(uri, scheme='file')
    if parsed.scheme == 'file':
        return False, None, None, None
    else:
        log = logging.getLogger(__name__)

        cached_file = cache_path(cache_dir, uri)
        if os.path.exists(cached_file):
            bundle_name = os.path.basename(cached_file)
            log.info('Retrieving from cache {}'.format(cached_file))
            return True, bundle_name, cached_file, None
        else:
            return False, None, None, None


def resolve_bundle_configuration(cache_dir, uri, auth=None):
    return resolve_file(cache_dir, uri, auth, require_bundle_conf=False)


def load_bundle_configuration_from_cache(cache_dir, uri):
    return load_bundle_from_cache(cache_dir, uri)


def resolve_bundle_version(uri):
    return None


def continuous_delivery_uri(resolved_version):
    return None


def get_url(uri):
    parsed = urlparse(uri, scheme='file')
    op = Path(uri)
    if parsed.scheme == 'file' and op.root == '' and not parsed.path.startswith('/'):
        np = str(op.cwd() / op)
    else:
        np = parsed.path
    url = urlunparse(ParseResult(parsed.scheme, parsed.netloc, np, parsed.params, parsed.query, parsed.fragment))
    return os.path.basename(url), url


def cache_path(cache_dir, uri):
    parsed = urlparse(uri, scheme='file')
    basename = os.path.basename(parsed.path)
    return '{}/{}'.format(cache_dir, basename)


def download_bundle(log, bundle_url, tmp_download_path, auth):
    parsed = urlparse(bundle_url, scheme='file')
    is_http_download = parsed.scheme == 'http' or parsed.scheme == 'https'

    if is_http_download and auth:
        realm, username, password = auth
        authinfo = urllib.request.HTTPBasicAuthHandler()
        authinfo.add_password(realm=realm,
                              uri=bundle_url,
                              user=username,
                              passwd=password)
        opener = urllib.request.build_opener(authinfo)
        urllib.request.install_opener(opener)

    if log.is_progress_enabled() and is_http_download:
        urlretrieve(bundle_url, tmp_download_path, reporthook=show_progress(log, bundle_url))
    else:
        log.info('Retrieving {}'.format(bundle_url))
        # File based download, no need to show progress bar
        urlretrieve(bundle_url, tmp_download_path)


def show_progress(log, bundle_url):
    prev_time = 0.0
    download_message_shown = False

    def continue_logging(count, block_size, total_size):
        nonlocal prev_time, download_message_shown

        if not download_message_shown:
            log.info('Retrieving {}'.format(bundle_url))
            download_message_shown = True

        downloaded_size = count * block_size
        percent = (downloaded_size * 1.0) / total_size
        download_complete = percent >= 1.0
        now_time = time.time()
        if download_complete or now_time - prev_time >= 0.1:
            progress_bar_text = screen_utils.progress_bar(percent)
            log.progress(progress_bar_text, flush=download_complete)
            prev_time = now_time

    return continue_logging
