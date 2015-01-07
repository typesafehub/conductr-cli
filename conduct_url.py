# build url from ConductR base url and given path
def url(path, args):
    base_url = 'http://{}:{}'.format(args.host, args.port)
    return '{}/{}'.format(base_url, path)
