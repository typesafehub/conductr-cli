from typesafe_conductr_cli import conduct_url, conduct_logging
import json
import requests


@conduct_logging.handle_connection_error
@conduct_logging.handle_http_error
def load(args):
    """`conduct load` command"""

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
    response.raise_for_status()

    if (args.verbose):
        conduct_logging.pretty_json(response.text)

    response_json = json.loads(response.text)
    bundleId = response_json['bundleId']

    print("Bundle loaded.")
    print("Start bundle with: conduct run{} {}".format(args.cli_parameters, bundleId))
    print("Unload bundle with: conduct unload{} {}".format(args.cli_parameters, bundleId))
    print("Print ConductR info with: conduct info{}".format(args.cli_parameters))
