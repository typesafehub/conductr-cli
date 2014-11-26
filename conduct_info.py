import conduct_url
import requests


# `conduct info` command
def info(args):
    url = conduct_url.url('bundles', args)
    response = requests.get(url)
    response.raise_for_status()
    print(response.text)
