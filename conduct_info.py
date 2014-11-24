import conduct_util
import requests


# `conduct info` command
def info(args):
    url = conduct_util.url('bundles')
    response = requests.get(url)
    response.raise_for_status()
    print(response.text)
