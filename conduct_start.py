import conduct_util
import requests


# `conduct start` command
def start(args):
    url = conduct_util.url('bundles/{}?scale={}'.format(args.bundle, args.scale))
    response = requests.put(url)
    if response.status_code == 200:
        print(response.text)
    else:
        conduct_util.print_error('{} {}', response.status_code, response.reason)
