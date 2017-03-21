from conductr_cli import bundle_utils, conduct_request, conduct_url, validation, screen_utils
from conductr_cli.conduct_url import conductr_host
import json
import logging
import re
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
    response = conduct_request.get(args.dcos_mode, conductr_host(args), url, timeout=DEFAULT_HTTP_TIMEOUT)
    validation.raise_for_status_inc_3xx(response)

    if log.is_verbose_enabled():
        log.verbose(validation.pretty_json(response.text))

    bundles = json.loads(response.text)
    all_acls, http_acls, tcp_acls = get_acls_from_bundles(args, bundles)

    if args.protocol_family == 'http':
        display_http_acls(log, http_acls)

    elif args.protocol_family == 'tcp':
        display_tcp_acls(log, tcp_acls)

    return True


def display_tcp_acls(log, tcp_acls, display_bundle_id=True, display_bundle_name=True, display_status=True):
    def tcp_port_value(line):
        return int(line['tcp_port'])

    data = [
        {
            'tcp_port': 'TCP/PORT',
            'bundle_id': 'BUNDLE ID' if display_bundle_id else '',
            'bundle_name': 'BUNDLE NAME' if display_bundle_name else '',
            'status': 'STATUS' if display_status else ''
        }
    ] + sorted([
        {
            'tcp_port': tcp_port,
            'bundle_id': tcp_acl['bundle_id'] if display_bundle_id else '',
            'bundle_name': tcp_acl['bundle_name'] if display_bundle_name else '',
            'status': tcp_acl['status'] if display_status else ''
        }
        for tcp_acl in tcp_acls
        for tcp_port in tcp_acl['acl']['tcp']['requests']
    ], key=tcp_port_value)

    display_template = '{tcp_port: <{tcp_port_width}}{padding}'
    if display_bundle_id:
        display_template += '{bundle_id: <{bundle_id_width}}{padding}'

    if display_bundle_name:
        display_template += '{bundle_name: <{bundle_name_width}}{padding}'

    if display_status:
        display_template += '{status: <{status_width}}'

    padding = 2
    column_widths = dict(screen_utils.calc_column_widths(data), **{'padding': ' ' * padding})
    for row in data:
        log.screen(display_template.format(**dict(row, **column_widths)).rstrip())


def display_http_acls(log, http_acls, display_bundle_id=True, display_bundle_name=True, display_status=True):
    http_request_mappings = [
        {
            'http_method': http_request_mapping['method'] if 'method' in http_request_mapping else ALL_HTTP_METHOD,
            'http_rewrite': http_request_mapping['rewrite'] if 'rewrite' in http_request_mapping else '',
            'http_acl': get_http_acl(http_request_mapping),
            'http_acl_type': get_http_acl_type(http_request_mapping),
            'bundle_id': http_acl['bundle_id'] if display_bundle_id else '',
            'bundle_name': http_acl['bundle_name'] if display_bundle_name else '',
            'status': http_acl['status'] if display_status else ''
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
        'bundle_id': 'BUNDLE ID' if display_bundle_id else '',
        'bundle_name': 'BUNDLE NAME' if display_bundle_name else '',
        'status': 'STATUS' if display_status else ''
    }] + http_path_regex_sorted + http_path_beg_sorted + http_path_sorted

    padding = 2
    column_widths = dict(screen_utils.calc_column_widths(data), **{'padding': ' ' * padding})

    display_template = '{http_method: <{http_method_width}}{padding}' \
                       '{http_acl: <{http_acl_width}}{padding}' \
                       '{http_rewrite: <{http_rewrite_width}}{padding}'
    if display_bundle_id:
        display_template += '{bundle_id: <{bundle_id_width}}{padding}'
    if display_bundle_name:
        display_template += '{bundle_name: <{bundle_name_width}}{padding}'
    if display_status:
        display_template += '{status: <{status_width}}'

    for row in data:
        log.screen(display_template.format(**dict(row, **column_widths)).rstrip())


def get_acls_from_bundles(args, bundles):
    def is_started(bundle_executions):
        for execution in bundle_executions:
            if execution['isStarted']:
                return 'Running'
        return 'Starting'

    all_acls = [
        {
            'acl': acl,
            'bundle_id': bundle['bundleId'] if args.long_ids else bundle_utils.short_id(bundle['bundleId']),
            'bundle_name': bundle['attributes']['bundleName'],
            'status': is_started(bundle['bundleExecutions'])
        }
        for bundle in bundles if bundle['bundleExecutions']
        for endpoint_name, endpoint in bundle['bundleConfig']['endpoints'].items() if 'acls' in endpoint
        for acl in endpoint['acls']
    ]

    http_acls = [acl for acl in all_acls if 'http' in acl['acl']]
    tcp_acls = [acl for acl in all_acls if 'tcp' in acl['acl']]

    return all_acls, http_acls, tcp_acls


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
