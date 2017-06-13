from conductr_cli.exceptions import BundleResolutionError, ContinuousDeliveryError
from conductr_cli.resolvers import \
    bintray_resolver, docker_offline_resolver, docker_resolver, stdin_resolver, uri_resolver, offline_resolver, \
    resolvers_util, s3_resolver
import importlib
import logging


# Try to resolve from local file system before we attempting resolution using bintray
DEFAULT_RESOLVERS = [stdin_resolver, uri_resolver, bintray_resolver, docker_resolver, s3_resolver]
OFFLINE_RESOLVERS = [stdin_resolver, offline_resolver, docker_offline_resolver]


def resolve_bundle(custom_settings, cache_dir, uri, offline_mode=False):
    log = logging.getLogger(__name__)

    cache_resolution_errors = []
    bundle_resolution_errors = []

    all_resolvers = resolver_chain(custom_settings, offline_mode)
    supported_resolvers = filter_for_supported_resolvers(all_resolvers, uri)
    if supported_resolvers:
        log.info('Resolving bundle using [{}]'.format(get_resolver_names(supported_resolvers)))

        for resolver in supported_resolvers:
            is_cached, bundle_file_name, cached_bundle, error = resolver.load_bundle_from_cache(cache_dir, uri)

            if error:
                cache_resolution_errors.append((resolver, error))

            if is_cached:
                return bundle_file_name, cached_bundle

        for resolver in supported_resolvers:
            is_resolved, bundle_file_name, bundle_file, error = resolver.resolve_bundle(cache_dir, uri)

            if error:
                bundle_resolution_errors.append((resolver, error))

            if is_resolved:
                return bundle_file_name, bundle_file

    raise BundleResolutionError('Unable to resolve bundle using {}'.format(uri),
                                cache_resolution_errors,
                                bundle_resolution_errors)


def resolve_bundle_configuration(custom_settings, cache_dir, uri, offline_mode=False):
    log = logging.getLogger(__name__)

    cache_resolution_errors = []
    bundle_resolution_errors = []

    all_resolvers = resolver_chain(custom_settings, offline_mode)
    supported_resolvers = filter_for_supported_resolvers(all_resolvers, uri)
    if supported_resolvers:
        log.info('Resolving bundle configuration using [{}]'.format(get_resolver_names(supported_resolvers)))

        for resolver in supported_resolvers:
            is_cached, bundle_configuration_file_name, cached_bundle, error = \
                resolver.load_bundle_configuration_from_cache(cache_dir, uri)

            if error:
                cache_resolution_errors.append((resolver, error))

            if is_cached:
                return bundle_configuration_file_name, cached_bundle

        for resolver in supported_resolvers:
            is_resolved, bundle_configuration_file_name, bundle_configuration_file, error = \
                resolver.resolve_bundle_configuration(cache_dir, uri)

            if error:
                bundle_resolution_errors.append((resolver, error))

            if is_resolved:
                return bundle_configuration_file_name, bundle_configuration_file

    raise BundleResolutionError('Unable to resolve bundle using {}'.format(uri),
                                cache_resolution_errors,
                                bundle_resolution_errors)


def resolve_bundle_version(custom_settings, uri, offline_mode=False):
    log = logging.getLogger(__name__)

    bundle_resolution_errors = []

    all_resolvers = resolver_chain(custom_settings, offline_mode)
    supported_resolvers = filter_for_supported_resolvers(all_resolvers, uri)
    if supported_resolvers:
        log.info('Resolving bundle version using [{}]'.format(get_resolver_names(supported_resolvers)))

        for resolver in supported_resolvers:
            resolved_version, error = resolver.resolve_bundle_version(uri)

            if error:
                bundle_resolution_errors.append((resolver, error))

            if resolved_version:
                return resolved_version

    raise BundleResolutionError('Unable to resolve bundle using {}'.format(uri),
                                cache_resolution_errors=[],
                                bundle_resolution_errors=bundle_resolution_errors)


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


def filter_for_supported_resolvers(resolvers, uri):
    """
    Filter a list of resolver which can resolve a given URI.

    For example, if URI is a S3 URL, the resolver chain will only contain S3 resolver as it's the only resolver
    capable of resolving a S3 URL.

    Filtering the supported resolver beforehand will allow a more efficient resolution process, i.e. there's no need
    to resolve from Bintray if S3 URL is provided as input.

    Each resolver is expected to provide `supported_schemes()` method which returns list of schemes supported by the
    resolver.

    A list of possible schemes is deduced from the `uri`. This list is then compared with the list supported by each
    resolver. If one of the possible schemes deduced from the `uri` is in the list supported by a particular resolver,
    this resolver is added in the supported resolver chain.

    However, since it's possible to specify custom resolver outside of the CLI codebase, for backward compatibility
    purposes, the resolver without `supported_schemes()` method will be added into the supported resolver chain so it
    has a chance to resolve the input URI.

    :param resolvers: the resolver chain
    :param uri: the uri to be resolved
    :return: list of resolvers which can be used to resolve the uri
    """
    log = logging.getLogger(__name__)

    uri_schemes = resolvers_util.detect_schemes(uri)

    supported_resolvers = []
    for resolver in resolvers:
        try:
            resolver_schemes = resolver.supported_schemes()
            if [scheme for scheme in uri_schemes if scheme in resolver_schemes]:
                supported_resolvers.append(resolver)
        except AttributeError as e:
            error_message = '{}'.format(e)
            if error_message.endswith('has no attribute \'supported_schemes\''):
                # If Resolver doesn't provide `supported_schemes` method, add the resolver to the list of supported
                # resolvers.
                # This is to support backward compatibility with custom resolver.
                log.warning('The resolver {} does not provide `supported_schemes()` method.'.format(resolver.__name__))
                supported_resolvers.append(resolver)
            else:
                # Other attribute error, continue and raise this
                raise e

    return supported_resolvers


def get_resolver_names(resolvers):
    def get_resolver_name(resolver):
        resolver_name = resolver.__name__
        return resolver_name.split('.')[-1] if '.' in resolver_name else resolver_name

    resolver_names = [get_resolver_name(resolver) for resolver in resolvers]
    return ', '.join(resolver_names)
