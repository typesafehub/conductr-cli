from conductr_cli.exceptions import BundleResolutionError
from conductr_cli.resolvers import bintray_resolver, uri_resolver


def all_resolvers():
    # Try to resolve from local file system before we attempting resolution using bintray
    return [uri_resolver, bintray_resolver]


def resolve_bundle(cache_dir, uri):
    for resolver in all_resolvers():
        is_cached, bundle_name, cached_bundle = resolver.load_from_cache(cache_dir, uri)
        if is_cached:
            return bundle_name, cached_bundle

    for resolver in all_resolvers():
        is_resolved, bundle_name, bundle_file = resolver.resolve_bundle(cache_dir, uri)
        if is_resolved:
            return bundle_name, bundle_file

    raise BundleResolutionError('Unable to resolve bundle using {}'.format(uri))
