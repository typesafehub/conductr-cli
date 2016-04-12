# build url from ConductR base url and given path
def url(path, args):
    base_url = 'http://{}:{}{}'.format(args.ip, args.port, api_version_path(args.api_version))
    return '{}/{}'.format(base_url, path)


def api_version_path(api_version):
    if api_version == '1':
        return ''
    else:
        return '/v{}'.format(api_version)


def request_headers(args):
    headers = {}
    if args.ip:
        headers.update({'Host': args.ip})

    return headers if headers else None
