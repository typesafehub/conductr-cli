from conductr_cli import bundle_utils, conduct_url, validation, screen_utils
import json
import logging
import re
import requests
from conductr_cli.http import DEFAULT_HTTP_TIMEOUT


SUPPORTED_PROTOCOL_FAMILIES = ['http', 'tcp']
ALL_HTTP_METHOD = '*'
HTTP_ACL_PATH = 'path'
HTTP_ACL_PATH_BEG = 'path_beg'
HTTP_ACL_PATH_REGEX = 'path_regex'


@validation.handle_connection_error
@validation.handle_http_error
def acls(args):
    """`conduct acls` command"""

    log = logging.getLogger(__name__)
    url = conduct_url.url('bundles', args)
    # At the time when this comment is being written, we need to pass the Host header when making HTTP request due to
    # a bug with requests python library not working properly when IPv6 address is supplied:
    # https://github.com/kennethreitz/requests/issues/3002
    # The workaround for this problem is to explicitly set the Host header when making HTTP request.
    # This fix is benign and backward compatible as the library would do this when making HTTP request anyway.
    response = requests.get(url, timeout=DEFAULT_HTTP_TIMEOUT, headers=conduct_url.request_headers(args))
    validation.raise_for_status_inc_3xx(response)

    if log.is_verbose_enabled():
        log.verbose(validation.pretty_json(response.text))

    def get_system_version(bundle):
        if 'systemVersion' in bundle['attributes']:
            return bundle['attributes']['systemVersion']
        else:
            return bundle['attributes']['system'].split('-')[-1]

    def is_started(bundle_executions):
        for execution in bundle_executions:
            if execution['isStarted']:
                return 'Running'
        return 'Starting'

    all_acls = [
        {
            'acl': acl,
            'system': bundle['attributes']['system'],
            'system_version': get_system_version(bundle),
            'endpoint_name': endpoint_name,
            'bundle_id': bundle['bundleId'] if args.long_ids else bundle_utils.short_id(bundle['bundleId']),
            'bundle_name': bundle['attributes']['bundleName'],
            'status': is_started(bundle['bundleExecutions'])
        }
        for bundle in json.loads(response.text) if bundle['bundleExecutions']
        for endpoint_name, endpoint in bundle['bundleConfig']['endpoints'].items() if 'acls' in endpoint
        for acl in endpoint['acls']
    ]

    if args.protocol_family == 'http':
        http_acls = [acl for acl in all_acls if 'http' in acl['acl']]
        display_http_acls(log, http_acls)

    elif args.protocol_family == 'tcp':
        tcp_acls = [acl for acl in all_acls if 'tcp' in acl['acl']]
        display_tcp_acls(log, tcp_acls)

    return True


def display_tcp_acls(log, tcp_acls):
    def tcp_port_value(line):
        return int(line['tcp_port'])

    data = [
        {
            'tcp_port': 'TCP/PORT',
            'system': 'SYSTEM',
            'system_version': 'SYSTEM VERSION',
            'endpoint_name': 'ENDPOINT NAME',
            'bundle_id': 'BUNDLE ID',
            'bundle_name': 'BUNDLE NAME',
            'status': 'STATUS'
        }
    ] + sorted([
        {
            'tcp_port': tcp_port,
            'system': tcp_acl['system'],
            'system_version': tcp_acl['system_version'],
            'endpoint_name': tcp_acl['endpoint_name'],
            'bundle_id': tcp_acl['bundle_id'],
            'bundle_name': tcp_acl['bundle_name'],
            'status': tcp_acl['status']
        }
        for tcp_acl in tcp_acls
        for tcp_port in tcp_acl['acl']['tcp']['requests']
    ], key=tcp_port_value)

    padding = 2
    column_widths = dict(screen_utils.calc_column_widths(data), **{'padding': ' ' * padding})
    for row in data:
        log.screen(
            '{tcp_port: <{tcp_port_width}}{padding}'
            '{system: <{system_width}}{padding}'
            '{system_version: <{system_version_width}}{padding}'
            '{endpoint_name: <{endpoint_name_width}}{padding}'
            '{bundle_id: <{bundle_id_width}}{padding}'
            '{bundle_name: <{bundle_name_width}}{padding}'
            '{status: <{status_width}}'.format(**dict(row, **column_widths)).rstrip())


def display_http_acls(log, http_acls):
    http_request_mappings = [
        {
            'http_method': http_request_mapping['method'] if 'method' in http_request_mapping else ALL_HTTP_METHOD,
            'http_rewrite': http_request_mapping['rewrite'] if 'rewrite' in http_request_mapping else '',
            'http_acl': get_http_acl(http_request_mapping),
            'http_acl_type': get_http_acl_type(http_request_mapping),
            'system': http_acl['system'],
            'system_version': http_acl['system_version'],
            'endpoint_name': http_acl['endpoint_name'],
            'bundle_id': http_acl['bundle_id'],
            'bundle_name': http_acl['bundle_name'],
            'status': http_acl['status']
        }
        for http_acl in http_acls
        for http_request_mapping in http_acl['acl']['http']['requests']
    ]

    def capture_group_count_reverse(line):
        return len(re.findall('([^\\(\\)]+)', line['http_acl'])) * -1

    http_path_regex_sorted = sorted([
        request_mapping
        for request_mapping in http_request_mappings if request_mapping['http_acl_type'] == HTTP_ACL_PATH_REGEX
    ], key=capture_group_count_reverse)

    def path_depth_reverse(line):
        return len(line['http_acl'].split('/')) * -1

    http_path_beg_sorted = sorted([
        request_mapping
        for request_mapping in http_request_mappings if request_mapping['http_acl_type'] == HTTP_ACL_PATH_BEG
    ], key=path_depth_reverse)

    http_path_sorted = sorted([
        request_mapping
        for request_mapping in http_request_mappings if request_mapping['http_acl_type'] == HTTP_ACL_PATH
    ], key=path_depth_reverse)

    data = [{
        'http_method': 'METHOD',
        'http_acl': 'PATH',
        'http_rewrite': 'REWRITE',
        'system': 'SYSTEM',
        'system_version': 'SYSTEM VERSION',
        'endpoint_name': 'ENDPOINT NAME',
        'bundle_id': 'BUNDLE ID',
        'bundle_name': 'BUNDLE NAME',
        'status': 'STATUS'
    }] + http_path_regex_sorted + http_path_beg_sorted + http_path_sorted

    padding = 2
    column_widths = dict(screen_utils.calc_column_widths(data), **{'padding': ' ' * padding})
    for row in data:
        log.screen(
            '{http_method: <{http_method_width}}{padding}'
            '{http_acl: <{http_acl_width}}{padding}'
            '{http_rewrite: <{http_rewrite_width}}{padding}'
            '{system: <{system_width}}{padding}'
            '{system_version: <{system_version_width}}{padding}'
            '{endpoint_name: <{endpoint_name_width}}{padding}'
            '{bundle_id: <{bundle_id_width}}{padding}'
            '{bundle_name: <{bundle_name_width}}{padding}'
            '{status: <{status_width}}'.format(**dict(row, **column_widths)).rstrip())


def get_http_acl(http_request_mapping):
    if 'path' in http_request_mapping:
        return http_request_mapping['path']
    elif 'pathBeg' in http_request_mapping:
        return '^{}'.format(http_request_mapping['pathBeg'])
    elif 'pathRegex' in http_request_mapping:
        return http_request_mapping['pathRegex']


def get_http_acl_type(http_request_mapping):
    if 'path' in http_request_mapping:
        return HTTP_ACL_PATH
    elif 'pathBeg' in http_request_mapping:
        return HTTP_ACL_PATH_BEG
    elif 'pathRegex' in http_request_mapping:
        return HTTP_ACL_PATH_REGEX
