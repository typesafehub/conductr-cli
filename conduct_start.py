import conduct
import requests


# `conduct start` command
def start(args):
    url = conduct.url('bundles/{}?scale={}'.format(args.bundle, args.scale))
    response = requests.put(url)
    if response.status_code == 200:
        print(response.text)
    else:
        conduct.print_error('{} {}', response.status_code, response.reason)
