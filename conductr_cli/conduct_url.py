# build url from ConductR base url and given path
def url(path, args):
    base_url = '{}://{}:{}{}{}'.format(args.scheme, conductr_host(args), args.port, args.base_path,
                                       api_version_path(args.api_version))
    return '{}{}'.format(base_url, path)


def conductr_host(args):
    return vars(args).get('host') or vars(args).get('ip')


def service_locator_url(service_name, args):
    if service_name:
        base_url = '{}://{}:{}{}'.format(args.scheme, conductr_host(args), 9008, args.base_path)
        return '{}services/{}'.format(base_url, service_name)
    else:
        return ''


def api_version_path(api_version):
    if api_version == '1':
        return ''
    else:
        return 'v{}/'.format(api_version)
