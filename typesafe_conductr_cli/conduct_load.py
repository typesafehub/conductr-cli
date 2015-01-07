from typesafe_conductr_cli import conduct_logging, conduct_url
import json
import requests


# `conduct load` command
def load(args):
    url = conduct_url.url('bundles', args)
    files = [
        ('nrOfCpus', str(args.nr_of_cpus)),
        ('memory', str(args.memory)),
        ('diskSpace', str(args.disk_space)),
        ('roles', ' '.join(args.roles)),
        ('bundle', open(args.bundle, 'rb'))
    ]
    if args.configuration is not None:
        files.append(('configuration', open(args.configuration, 'rb')))
    response = requests.post(url, files=files)
    if response.status_code == 200:
        if (args.verbose):
            conduct_logging.pretty_json(response.text)

        response_json = json.loads(response.text)
        bundleId = response_json['bundleId']

        print("Bundle loaded.")
        print("Start bundle with: cli/conduct run {}".format(bundleId))
        print("Unload bundle with: cli/conduct unload {}".format(bundleId))
        print("Print ConductR info with: cli/conduct info")
    else:
        conduct_logging.error('{} {}', response.status_code, response.reason)
