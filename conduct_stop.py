import conduct_logging
import conduct_url
import json
import requests


# `conduct stop` command
def stop(args):
    path = 'bundles/{}?scale=0'.format(args.bundle)
    url = conduct_url.url(path, args)
    response = requests.put(url)
    if response.status_code == 200:
        if (args.verbose):
            conduct_logging.pretty_json(response.text)

        response_json = json.loads(response.text)
        bundleId = response_json['bundleId']

        print("Bundle stop request sent.")
        print("Unload bundle with: cli/conduct unload {}".format(bundleId))
        print("Print conductor info with: cli/conduct info")
    else:
        conduct_logging.error('{} {}', response.status_code, response.reason)
