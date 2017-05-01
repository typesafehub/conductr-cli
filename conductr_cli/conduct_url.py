# build url from ConductR base url and given path
def url(path, args):
    if hasattr(args, 'dcos_mode') and args.dcos_mode:
        base_url = '{}://{}{}{}'.format(args.scheme, conductr_host(args), args.base_path,
                                        api_version_path(args.api_version))
    else:
        base_url = '{}://{}:{}{}{}'.format(args.scheme, conductr_host(args), args.port, args.base_path,
                                           api_version_path(args.api_version))
    return '{}{}'.format(base_url, path)


def conductr_host(args):
    return vars(args).get('host') or vars(args).get('ip')


def api_version_path(api_version):
    if api_version == '1':
        return ''
    else:
        return 'v{}/'.format(api_version)
