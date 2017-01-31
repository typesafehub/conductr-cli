from conductr_cli.exceptions import BundleResolutionError, ContinuousDeliveryError
from conductr_cli.resolvers import bintray_resolver, uri_resolver, offline_resolver
import importlib
import logging


# Try to resolve from local file system before we attempting resolution using bintray
DEFAULT_RESOLVERS = [uri_resolver, bintray_resolver]
OFFLINE_RESOLVERS = [offline_resolver]


def resolve_bundle(custom_settings, cache_dir, uri, offline_mode=False):
    all_resolvers = resolver_chain(custom_settings, offline_mode)

    for resolver in all_resolvers:
        is_cached, bundle_file_name, cached_bundle = resolver.load_bundle_from_cache(cache_dir, uri)
        if is_cached:
            return bundle_file_name, cached_bundle

    for resolver in all_resolvers:
        is_resolved, bundle_file_name, bundle_file = resolver.resolve_bundle(cache_dir, uri)
        if is_resolved:
            return bundle_file_name, bundle_file

    raise BundleResolutionError('Unable to resolve bundle using {}'.format(uri))


def resolve_bundle_configuration(custom_settings, cache_dir, uri, offline_mode=False):
    all_resolvers = resolver_chain(custom_settings, offline_mode)

    for resolver in all_resolvers:
        is_cached, bundle_configuration_file_name, cached_bundle = \
            resolver.load_bundle_configuration_from_cache(cache_dir, uri)
        if is_cached:
            return bundle_configuration_file_name, cached_bundle

    for resolver in all_resolvers:
        is_resolved, bundle_configuration_file_name, bundle_configuration_file = \
            resolver.resolve_bundle_configuration(cache_dir, uri)
        if is_resolved:
            return bundle_configuration_file_name, bundle_configuration_file

    raise BundleResolutionError('Unable to resolve bundle using {}'.format(uri))


def resolve_bundle_version(custom_settings, uri, offline_mode=False):
    all_resolvers = resolver_chain(custom_settings, offline_mode)

    for resolver in all_resolvers:
        resolved_version = resolver.resolve_bundle_version(uri)
        if resolved_version:
            return resolved_version

    raise BundleResolutionError('Unable to resolve bundle using {}'.format(uri))


def continuous_delivery_uri(custom_settings, resolved_version, offline_mode=False):
    all_resolvers = resolver_chain(custom_settings, offline_mode)

    for resolver in all_resolvers:
        uri = resolver.continuous_delivery_uri(resolved_version)
        if uri:
            return uri

    raise ContinuousDeliveryError('Unable to form Continuous Delivery uri using {}'.format(resolved_version))


def resolver_chain(custom_settings, offline_mode):
    log = logging.getLogger(__name__)
    if custom_settings is not None and 'resolvers' in custom_settings:
        resolver_names = custom_settings.get_list('resolvers')
        if resolver_names:
            log.info('Using custom bundle resolver chain {}'.format(resolver_names))
            custom_resolver_chain = [importlib.import_module(resolver_name) for resolver_name in resolver_names]
            return custom_resolver_chain
    else:
        return OFFLINE_RESOLVERS if offline_mode else DEFAULT_RESOLVERS
