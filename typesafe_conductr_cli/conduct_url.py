# build url from ConductR base url and given path
def url(path, args):
    base_url = 'http://{}:{}'.format(args.ip, args.port)
    return '{}/{}'.format(base_url, path)
