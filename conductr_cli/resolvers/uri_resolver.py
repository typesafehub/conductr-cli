from urllib.request import urlretrieve
from urllib.parse import ParseResult, urlparse, urlunparse
from urllib.error import URLError
from pathlib import Path
from conductr_cli import screen_utils
import os
import logging
import shutil
import urllib


def resolve_bundle(cache_dir, uri, auth=None):
    log = logging.getLogger(__name__)

    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir, mode=0o700)

    try:
        bundle_name, bundle_url = get_url(uri)

        cached_file = cache_path(cache_dir, uri)
        tmp_download_path = '{}.tmp'.format(cached_file)

        if os.path.exists(tmp_download_path):
            os.remove(tmp_download_path)

        download_bundle(log, bundle_url, tmp_download_path, auth)

        os.chmod(tmp_download_path, 0o600)
        shutil.move(tmp_download_path, cached_file)
        return True, bundle_name, cached_file
    except URLError:
        return False, None, None


def load_from_cache(cache_dir, uri):
    # When the supplied uri is a local filesystem, don't load from cache so file can be used as is
    parsed = urlparse(uri, scheme='file')
    if parsed.scheme == 'file':
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
