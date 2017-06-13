from conductr_cli.resolvers.schemes import SCHEME_BUNDLE, SCHEME_FILE
import os
import glob
import logging


def supported_schemes():
    return [SCHEME_BUNDLE, SCHEME_FILE]


def resolve_bundle(cache_dir, uri, auth=None):
    return resolve_file(cache_dir, uri, auth)


def resolve_file(cache_dir, uri, auth=None):
    log = logging.getLogger(__name__)

    if os.path.exists(uri):
        abs_path = os.path.abspath(uri)
        log.info('Retrieving {}'.format(abs_path))
        return True, os.path.basename(abs_path), abs_path, None
    else:
        return False, None, None, None


def load_bundle_from_cache(cache_dir, uri):
    """
    Tries to load a bundle from the cache directory.
    If offline mode is enabled and the given uri equals a bundle name without slashes, e.g. 'visualizer'
    then it tries to resolve the last modified bundle from the cache directory by the given uri.
    Otherwise, when the supplied uri is a local filesystem, the file is not loaded from cache so that the
    local file can be loaded directly.
    :param cache_dir: the cache directory
    :param uri: the bundle uri. Can be either a bundle name, e.g. 'visualizer, an http or file uri
    :return: a tuple of (is_cached, bundle_name, bundle_uri)
    """
    # When the supplied uri is a local filesystem, don't load from cache so file can be used as is
    if is_bundle_name(uri):
        cached_bundles = glob.glob('{}/{}*'.format(cache_dir, uri))
        if cached_bundles:
            log = logging.getLogger(__name__)
            latest_bundle_file = max(cached_bundles, key=os.path.getctime)
            bundle_name = os.path.basename(latest_bundle_file)
            log.info('Retrieving from cache {}'.format(latest_bundle_file))
            return True, bundle_name, latest_bundle_file, None

    return False, None, None, None


def resolve_bundle_configuration(cache_dir, uri, auth=None):
    return resolve_bundle(cache_dir, uri, auth)


def load_bundle_configuration_from_cache(cache_dir, uri):
    return load_bundle_from_cache(cache_dir, uri)


def resolve_bundle_version(uri):
    return None, None


def continuous_delivery_uri(resolved_version):
    return None


def is_bundle_name(uri):
    return uri.count('/') == 0 and uri.count('.') == 0
