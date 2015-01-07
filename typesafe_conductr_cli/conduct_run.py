from typesafe_conductr_cli import conduct_logging, conduct_url
import json
import requests


# `conduct run` command
def run(args):
    path = 'bundles/{}?scale={}'.format(args.bundle, args.scale)
    url = conduct_url.url(path, args)
    response = requests.put(url)
    if response.status_code == 200:
        if (args.verbose):
            conduct_logging.pretty_json(response.text)

        response_json = json.loads(response.text)
        bundleId = response_json['bundleId']

        print("Bundle run request sent.")
        print("Stop bundle with: conduct stop{} {}".format(args.cli_parameters, bundleId))
        print("Print ConductR info with: conduct info{}".format(args.cli_parameters))
    else:
        conduct_logging.error('{} {}', response.status_code, response.reason)
