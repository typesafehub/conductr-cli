import conduct_logging
import conduct_url
import requests


# `conduct info` command
def info(args):
    url = conduct_url.url('bundles', args)
    response = requests.get(url)
    response.raise_for_status()
    conduct_logging.pretty_json(response.text)
