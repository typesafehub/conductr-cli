from pyhocon import ConfigFactory, ConfigTree
from pyhocon.exceptions import ConfigMissingException
from conductr_cli import bundle_utils, conduct_url, conduct_logging
from functools import partial
import json
import os
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

    with_bundle_configurations = partial(apply_to_configurations, bundle_conf, overlay_bundle_conf)

    url = conduct_url.url('bundles', args)
    files = [
        ('nrOfCpus', with_bundle_configurations(ConfigTree.get_string, 'nrOfCpus')),
        ('memory', with_bundle_configurations(ConfigTree.get_string, 'memory')),
        ('diskSpace', with_bundle_configurations(ConfigTree.get_string, 'diskSpace')),
        ('roles', ' '.join(with_bundle_configurations(ConfigTree.get_list, 'roles'))),
        ('bundleName', with_bundle_configurations(ConfigTree.get_string, 'name')),
        ('system', with_bundle_configurations(ConfigTree.get_string, 'system')),
        ('bundle', open(args.bundle, 'rb'))
    ]
    if args.configuration is not None:
        files.append(('configuration', open(args.configuration, 'rb')))

    response = requests.post(url, files=files)
    conduct_logging.raise_for_status_inc_3xx(response)

    if args.verbose:
        conduct_logging.pretty_json(response.text)

    response_json = json.loads(response.text)
    bundle_id = response_json['bundleId'] if args.long_ids else bundle_utils.short_id(response_json['bundleId'])

    print('Bundle loaded.')
    print('Start bundle with: conduct run{} {}'.format(args.cli_parameters, bundle_id))
    print('Unload bundle with: conduct unload{} {}'.format(args.cli_parameters, bundle_id))
    print('Print ConductR info with: conduct info{}'.format(args.cli_parameters))


def apply_to_configurations(base_conf, overlay_conf, method, key):
    if overlay_conf is None:
        return method(base_conf, key)
    else:
        try:
            return method(overlay_conf, key)
        except ConfigMissingException:
            return method(base_conf, key)
