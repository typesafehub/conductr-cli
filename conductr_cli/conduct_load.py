from pyhocon import ConfigFactory, ConfigTree
from pyhocon.exceptions import ConfigMissingException
from conductr_cli import bundle_utils, conduct_url, conduct_logging
from functools import partial
from urllib.parse import ParseResult, urlparse, urlunparse
from urllib.request import urlretrieve
from pathlib import Path

import json
import requests


@conduct_logging.handle_connection_error
@conduct_logging.handle_http_error
@conduct_logging.handle_invalid_config
@conduct_logging.handle_no_file
@conduct_logging.handle_bad_zip
def load(args):
    """`conduct load` command"""

    print('Retrieving bundle...')
    bundle_name, bundle_url = get_url(args.bundle)
    bundle_file, bundle_headers = urlretrieve(bundle_url)

    configuration_file, configuration_headers, configuration_name = (None, None, None)
    if args.configuration is not None:
        print('Retrieving configuration...')
        configuration_name, configuration_url = get_url(args.configuration)
        configuration_file, configuration_headers = urlretrieve(configuration_url)

    bundle_conf = ConfigFactory.parse_string(bundle_utils.conf(bundle_file))
    overlay_bundle_conf = None if configuration_file is None else \
        ConfigFactory.parse_string(bundle_utils.conf(configuration_file))

    with_bundle_configurations = partial(apply_to_configurations, bundle_conf, overlay_bundle_conf)

    url = conduct_url.url('bundles', args)
    files = [
        ('nrOfCpus', with_bundle_configurations(ConfigTree.get_string, 'nrOfCpus')),
        ('memory', with_bundle_configurations(ConfigTree.get_string, 'memory')),
        ('diskSpace', with_bundle_configurations(ConfigTree.get_string, 'diskSpace')),
        ('roles', ' '.join(with_bundle_configurations(ConfigTree.get_list, 'roles'))),
        ('bundleName', with_bundle_configurations(ConfigTree.get_string, 'name')),
        ('system', with_bundle_configurations(ConfigTree.get_string, 'system')),
        ('bundle', (bundle_name, open(bundle_file, 'rb')))
    ]
    if configuration_file is not None:
        files.append(('configuration', (configuration_name, open(configuration_file, 'rb'))))

    print('Loading bundle to ConductR...')
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


def get_url(uri):
    parsed = urlparse(uri, scheme='file')
    op = Path(uri)
    np = str(op.cwd() / op if parsed.scheme == 'file' and op.root == '' else parsed.path)
    url = urlunparse(ParseResult(parsed.scheme, parsed.netloc, np, parsed.params, parsed.query, parsed.fragment))
    return (url.split('/')[-1], url)
