from pyhocon import ConfigFactory
from typesafe_conductr_cli import bundle_utils, conduct_url, conduct_logging
import json
import os
import re
import requests


@conduct_logging.handle_connection_error
@conduct_logging.handle_http_error
@conduct_logging.handle_invalid_config
def load(args):
    """`conduct load` command"""

    if args.bundle_name is None:
        args.bundle_name = path_to_bundle_name(args.bundle)

    if args.system is None:
        args.system = path_to_bundle_name(args.bundle)

    bundle_conf = ConfigFactory.parse_string(bundle_utils.conf(args.bundle))

    url = conduct_url.url('bundles', args)
    files = [
        ('nrOfCpus', bundle_conf.get_string('nrOfCpus')),
        ('memory', bundle_conf.get_string('memory')),
        ('diskSpace', bundle_conf.get_string('diskSpace')),
        ('roles', ' '.join(bundle_conf.get_list('roles'))),
        ('bundleName', args.bundle_name),
        ('system', args.system),
        ('bundle', open(args.bundle, 'rb'))
    ]
    if args.configuration is not None:
        files.append(('configuration', open(args.configuration, 'rb')))

    response = requests.post(url, files=files)
    conduct_logging.raise_for_status_inc_3xx(response)

    if (args.verbose):
        conduct_logging.pretty_json(response.text)

    response_json = json.loads(response.text)
    bundleId = response_json['bundleId'] if args.long_ids else bundle_utils.short_id(response_json['bundleId'])

    print('Bundle loaded.')
    print('Start bundle with: conduct run{} {}'.format(args.cli_parameters, bundleId))
    print('Unload bundle with: conduct unload{} {}'.format(args.cli_parameters, bundleId))
    print('Print ConductR info with: conduct info{}'.format(args.cli_parameters))


def path_to_bundle_name(filename):
    match = re.match(r'(.*?)(-[a-fA-F0-9]{0,64})?\.zip', os.path.basename(filename))
    return match.group(1)
