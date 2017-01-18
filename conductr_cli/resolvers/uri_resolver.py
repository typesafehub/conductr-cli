from urllib.request import urlretrieve
from urllib.parse import ParseResult, urlparse, urlunparse
from urllib.error import URLError
from pathlib import Path
from conductr_cli import screen_utils
import os
import glob
import logging
import shutil
import urllib


def resolve_bundle(cache_dir, uri, auth=None):
    return resolve_file(cache_dir, uri, auth)


def resolve_file(cache_dir, uri, auth=None):
    log = logging.getLogger(__name__)

    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir, mode=0o700)

    try:
        file_name, file_url = get_url(uri)

        cached_file = cache_path(cache_dir, uri)
        tmp_download_path = '{}.tmp'.format(cached_file)

        if os.path.exists(tmp_download_path):
            os.remove(tmp_download_path)

        download_bundle(log, file_url, tmp_download_path, auth)

        os.chmod(tmp_download_path, 0o600)
        shutil.move(tmp_download_path, cached_file)
        return True, file_name, cached_file
    except URLError:
        return False, None, None


def load_bundle_from_cache(cache_dir, uri, offline_mode=False):
    """
    Tries to load a bundle from the cache directory.
    If offline mode is enabled and the given uri equals a bundle name without slashes, e.g. 'visualizer'
    then it tries to resolve the last modified bundle from the cache directory by the given uri.
    Otherwise, when the supplied uri is a local filesystem, the file is not loaded from cache so that the
    local file can be loaded directly.
    :param cache_dir: the cache directory
    :param uri: the bundle uri. Can be either a bundle name, e.g. 'visualizer, an http or file uri
    :param offline_mode: the offline mode flag
    :return: a tuple of (is_cached, bundle_name, bundle_uri)
    """
    # When the supplied uri is a local filesystem, don't load from cache so file can be used as is
    parsed = urlparse(uri, scheme='file')
    if offline_mode and is_bundle_name(uri):
        cached_bundles = glob.glob('{}/{}*'.format(cache_dir, uri))
        if cached_bundles:
            log = logging.getLogger(__name__)
            last_modified_cached_bundle_uri = max(cached_bundles, key=os.path.getctime)
            bundle_name = os.path.basename(last_modified_cached_bundle_uri)
            log.info('Retrieving from cache {}'.format(last_modified_cached_bundle_uri))
            return True, bundle_name, last_modified_cached_bundle_uri
        else:
            return False, None, None
    elif parsed.scheme == 'file':
        return False, None, None
    else:
        log = logging.getLogger(__name__)

        cached_file = cache_path(cache_dir, uri)
        if os.path.exists(cached_file):
            bundle_name = os.path.basename(cached_file)
            log.info('Retrieving from cache {}'.format(cached_file))
            return True, bundle_name, cached_file
        else:
            return False, None, None


def resolve_bundle_configuration(cache_dir, uri, auth=None):
    return resolve_bundle(cache_dir, uri, auth)


def load_bundle_configuration_from_cache(cache_dir, uri, offline_mode=False):
    return load_bundle_from_cache(cache_dir, uri, offline_mode)


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
    log.info('Retrieving {}'.format(bundle_url))

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
        urlretrieve(bundle_url, tmp_download_path, reporthook=show_progress(log))
    else:
        # File based download, no need to show progress bar
        urlretrieve(bundle_url, tmp_download_path)


def show_progress(log):
    def continue_logging(count, block_size, total_size):
        downloaded_size = count * block_size
        is_download_complete = downloaded_size >= total_size
        progress_bar_text = screen_utils.progress_bar(downloaded_size, total_size)
        log.progress(progress_bar_text, flush=is_download_complete)

    return continue_logging


def is_bundle_name(uri):
    if uri.count('/') == 0:
        return True
    else:
        False
