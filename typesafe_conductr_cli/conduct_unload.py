from typesafe_conductr_cli import conduct_logging, conduct_url
import requests


# `conduct unload` command
def unload(args):
    path = 'bundles/{}'.format(args.bundle)
    url = conduct_url.url(path, args)
    response = requests.delete(url)
    if response.status_code == 200:
        if (args.verbose):
            conduct_logging.pretty_json(response.text)

        print("Bundle unload request sent.")
        print("Print ConductR info with: cli/conduct info")
    else:
        conduct_logging.error('{} {}', response.status_code, response.reason)
