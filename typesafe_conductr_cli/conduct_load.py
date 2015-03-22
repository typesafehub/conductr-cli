from pyhocon import ConfigFactory, ConfigTree
from pyhocon.exceptions import ConfigMissingException
from typesafe_conductr_cli import bundle_utils, conduct_url, conduct_logging
from functools import partial
import json
import os
import re
import requests


@conduct_logging.handle_connection_error
@conduct_logging.handle_http_error
@conduct_logging.handle_invalid_config
@conduct_logging.handle_no_file
def load(args):
    """`conduct load` command"""

    if not os.path.isfile(args.bundle):
        raise FileNotFoundError(args.bundle)

    if args.configuration is not None and not os.path.isfile(args.configuration):
        raise FileNotFoundError(args.configuration)

    bundle_conf = ConfigFactory.parse_string(bundle_utils.conf(args.bundle))
    overlay_bundle_conf = None if args.configuration is None else \
         ConfigFactory.parse_string(bundle_utils.conf(args.configuration))

    withBundleConfs = partial(applyToConfs, bundle_conf, overlay_bundle_conf)

    url = conduct_url.url('bundles', args)
    files = [
        ('nrOfCpus', withBundleConfs(ConfigTree.get_string, 'nrOfCpus')),
        ('memory', withBundleConfs(ConfigTree.get_string, 'memory')),
        ('diskSpace', withBundleConfs(ConfigTree.get_string, 'diskSpace')),
        ('roles', ' '.join(withBundleConfs(ConfigTree.get_list, 'roles'))),
        ('bundleName', withBundleConfs(ConfigTree.get_string, 'name')),
        ('system', withBundleConfs(ConfigTree.get_string, 'system')),
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

def applyToConfs(base_conf, overlay_conf, method, key):
    if overlay_conf is None:
        return method(base_conf, key)
    else:
        try:
            return method(overlay_conf, key)
        except ConfigMissingException:
            return method(base_conf, key)