import conduct
import requests


# `conduct info` command
def info(args):
    url = conduct.url('bundles')
    response = requests.get(url)
    response.raise_for_status()
    print(response.text)
