import os
import sys


# build url from conductor base url and given path
def url(path):
    host = os.getenv('HOSTNAME', '127.0.0.1')
    port = 9005
    base_url = 'http://{}:{}'.format(host, port)
    return '{}/{}'.format(base_url, path)


# print to stderr
def print_error(message, *objs):
    print("ERROR:", message.format(*objs), file=sys.stderr)
