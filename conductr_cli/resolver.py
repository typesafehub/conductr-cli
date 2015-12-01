from conductr_cli.exceptions import BundleResolutionError
from conductr_cli.resolvers import bintray_resolver, uri_resolver
import importlib
import logging


# Try to resolve from local file system before we attempting resolution using bintray
DEFAULT_RESOLVERS = [uri_resolver, bintray_resolver]


def resolve_bundle(custom_settings, cache_dir, uri):
    all_resolvers = resolver_chain(custom_settings)

    for resolver in all_resolvers:
        is_cached, bundle_name, cached_bundle = resolver.load_from_cache(cache_dir, uri)
        if is_cached:
            return bundle_name, cached_bundle

    for resolver in all_resolvers:
        is_resolved, bundle_name, bundle_file = resolver.resolve_bundle(cache_dir, uri)
        if is_resolved:
            return bundle_name, bundle_file

    raise BundleResolutionError('Unable to resolve bundle using {}'.format(uri))


def resolver_chain(custom_settings):
    log = logging.getLogger(__name__)
    if custom_settings is not None and 'resolvers' in custom_settings:
        resolver_names = custom_settings.get_list('resolvers')
        if resolver_names:
            log.info('Using custom bundle resolver chain {}'.format(resolver_names))
            custom_resolver_chain = [importlib.import_module(resolver_name) for resolver_name in resolver_names]
            return custom_resolver_chain

    return DEFAULT_RESOLVERS
