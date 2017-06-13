from conductr_cli.resolvers import docker_resolver


def supported_schemes():
    return docker_resolver.supported_schemes()


def resolve_bundle(cache_dir, uri, auth=None):
    return docker_resolver.do_resolve_bundle(cache_dir, uri, auth, offline_mode=True)


def resolve_file(cache_dir, uri, auth=None):
    return False, None, None, None


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
