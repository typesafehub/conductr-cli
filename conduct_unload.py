import conduct_logging
import conduct_url
import requests


# `conduct unload` command
def unload(args):
    path = 'bundles/{}'.format(args.bundle)
    url = conduct_url.url(path, args)
    response = requests.delete(url)
    if response.status_code == 200:
        conduct_logging.pretty_json(response.text)
    else:
        conduct_logging.error('{} {}', response.status_code, response.reason)
