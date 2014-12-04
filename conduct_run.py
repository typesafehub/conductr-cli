import conduct_logging
import conduct_url
import requests


# `conduct run` command
def run(args):
    path = 'bundles/{}?scale={}'.format(args.bundle, args.scale)
    url = conduct_url.url(path, args)
    response = requests.put(url)
    if response.status_code == 200:
        print(response.text)
    else:
        conduct_logging.error('{} {}', response.status_code, response.reason)
