from conductr_cli import screen_utils, conduct_acls, conduct_service_names
from conductr_cli.conduct_info_common import DISPLAY_PADDING, display_bundle_id
from urllib.parse import urlparse
import json
import logging


def display_bundle(args, bundles, bundle_id_or_name):
    log = logging.getLogger(__name__)

    bundles = filter_bundles_by_id_or_name(bundles, bundle_id_or_name)
    if bundles and len(bundles) == 1:
        bundle = bundles[0]

        if log.is_verbose_enabled():
            log.verbose(json.dumps(bundle, sort_keys=True, indent=2, separators=(',', ': ')))

        display_bundle_properties(args, bundle)

        return True
    elif bundles and len(bundles) > 1:
        found_bundle_ids = [
            display_bundle_id(args, bundle)
            for bundle in bundles
        ]
        log.error('Specified Bundle ID/name: {} resulted in multiple Bundle IDs: {}'.format(bundle_id_or_name,
                                                                                            found_bundle_ids))
        return False
    else:
        log.error('Unable to find bundle {}'.format(bundle_id_or_name))
        return False


def display_bundle_properties(args, bundle):
    display_bundle_attributes(args, bundle)
    display_bundle_scale(bundle)
    display_bundle_installations(bundle)
    display_bundle_executions(bundle)
    display_bundle_config(args, bundle)


def display_bundle_attributes(args, bundle):
    display_key_value_table_with_title('BUNDLE ATTRIBUTES', [
        ('Bundle Id', display_bundle_id(args, bundle)),
        ('Bundle Name', bundle['attributes']['bundleName']),
        ('Compatibility Version', bundle['attributes']['compatibilityVersion']
            if 'compatibilityVersion' in bundle['attributes'] else None),
        ('System', bundle['attributes']['system']),
        ('System Version', bundle['attributes']['systemVersion'] if 'systemVersion' in bundle['attributes'] else None),
        ('Nr of CPUs', bundle['attributes']['nrOfCpus']),
        ('Memory', bundle['attributes']['memory']),
        ('Disk Space', bundle['attributes']['diskSpace']),
        ('Roles', ', '.join(sorted(bundle['attributes']['roles']))),
        ('Bundle Digest', bundle['bundleDigest']),
        ('Configuration Digest', bundle['configurationDigest'] if 'configurationDigest' in bundle else None),
        ('Error', 'Yes' if bundle['hasError'] else 'No'),
    ])


def display_bundle_config(args, bundle):
    all_acls, http_acls, tcp_acls = conduct_acls.get_acls_from_bundles(args, [bundle])
    display_http_acls(http_acls)
    display_tcp_acls(tcp_acls)

    data, duplicate_endpoints = conduct_service_names.get_service_names_from_bundles(args, [bundle])
    display_service_names(data, duplicate_endpoints)


def display_http_acls(http_acls):
    log = logging.getLogger(__name__)
    if http_acls:
        display_title_table('HTTP ACLS')
        conduct_acls.display_http_acls(log, http_acls,
                                       display_bundle_id=False,
                                       display_bundle_name=False,
                                       display_status=True)
        log.screen('')


def display_tcp_acls(tcp_acls):
    log = logging.getLogger(__name__)

    if tcp_acls:
        display_title_table('TCP ACLS')
        conduct_acls.display_tcp_acls(log, tcp_acls,
                                      display_bundle_id=False,
                                      display_bundle_name=False,
                                      display_status=True)
        log.screen('')


def display_service_names(service_names, duplicate_endpoints):
    log = logging.getLogger(__name__)

    if service_names:
        display_title_table('SERVICE NAMES')
        conduct_service_names.display_service_names(log, service_names, duplicate_endpoints,
                                                    display_bundle_id=False,
                                                    display_bundle_name=False,
                                                    display_status=True)
        log.screen('')


def display_bundle_installations(bundle):
    def host_from_akka_address(akka_address):
        return akka_address.split('@')[1].split(':')[0]

    def get_path(file_uri):
        parse = urlparse(file_uri)
        if parse.scheme == '' or parse.scheme == 'file':
            return parse.path
        else:
            return file_uri

    if 'bundleInstallations' in bundle:
        installations = bundle['bundleInstallations']
        if installations:
            display_title_table('BUNDLE INSTALLATIONS')

            for installation in installations:
                display_key_value_table([
                    ('Host', host_from_akka_address(installation['uniqueAddress']['address'])),
                    ('Bundle', get_path(installation['bundleFile'])),
                    ('Bundle configuration', get_path(installation['configurationFile'])
                        if 'configurationFile' in installation else None),
                ])


def display_bundle_executions(bundle):
    log = logging.getLogger(__name__)

    if 'bundleExecutions' in bundle and bundle['bundleExecutions']:
        rows = sorted([
            {
                'endpoint': endpoint_name,
                'host': bundle_execution['host'],
                'is_started': 'Yes' if bundle_execution['isStarted'] else 'No',
                'bind_port': endpoint_details['bindPort'],
                'host_port': endpoint_details['hostPort']
            }
            for bundle_execution in bundle['bundleExecutions']
            for endpoint_name, endpoint_details in bundle_execution['endpoints'].items()
        ], key=lambda v: v['endpoint'])

        if rows:
            display_title_table('BUNDLE EXECUTIONS')

            rows.insert(0, {
                'endpoint': 'ENDPOINT',
                'host': 'HOST',
                'is_started': 'STARTED',
                'bind_port': 'BIND_PORT',
                'host_port': 'HOST_PORT',
            })
            column_widths = dict(screen_utils.calc_column_widths(rows), **{'padding': ' ' * DISPLAY_PADDING})
            for row in rows:
                log.screen('{endpoint: <{endpoint_width}}{padding}'
                           '{host: <{host_width}}{padding}'
                           '{is_started: >{is_started_width}}{padding}'
                           '{bind_port: >{bind_port_width}}{padding}'
                           '{host_port: >{host_port_width}}'.format(**dict(row, **column_widths)).rstrip())

            log.screen('')


def display_bundle_scale(bundle):
    if 'bundleScale' in bundle:
        if isinstance(bundle['bundleScale'], int):
            display_key_value_table_with_title('BUNDLE SCALE', [
                ('Scale', bundle['bundleScale']),
            ])
        else:
            display_key_value_table_with_title('BUNDLE SCALE', [
                ('Nr of Reschedules', bundle['bundleScale']['nrOfReschedules']
                    if 'nrOfReschedules' in bundle['bundleScale'] else None),
                ('Scale', bundle['bundleScale']['scale']),
            ])


def display_key_value_table_with_title(title, entries):
    display_title_table(title)
    display_key_value_table(entries)


def display_key_value_table(entries):
    log = logging.getLogger(__name__)
    rows = [{'key': key, 'value': value} for key, value in entries if value is not None]

    column_widths = dict(screen_utils.calc_column_widths(rows), **{'padding': ' ' * DISPLAY_PADDING})
    for row in rows:
        log.screen('''\
{key: <{key_width}}{padding}\
{value: <{value_width}}'''.format(**dict(row, **column_widths)).rstrip())

    log.screen('')


def display_title_table(title):
    log = logging.getLogger(__name__)
    log.screen(title)
    title_separator = ''.join(['-' for x in title])
    log.screen(title_separator)


def filter_bundles_by_id_or_name(bundles, bundle_id_or_name):
    return [
        bundle
        for bundle in bundles
        if has_bundle_name(bundle, bundle_id_or_name) or has_bundle_id(bundle, bundle_id_or_name)
    ]


def has_bundle_name(bundle, bundle_name):
    actual_name = bundle['attributes']['bundleName']
    return actual_name == bundle_name or actual_name.startswith(bundle_name)


def has_bundle_id(bundle, bundle_id):
    actual_bundle_id = bundle['bundleId']
    if actual_bundle_id == bundle_id:
        return True
    else:
        if '-' in actual_bundle_id and '-' in bundle_id:
            actual_bundle_id_parts = actual_bundle_id.split('-')
            actual_bundle_digest = actual_bundle_id_parts[0]
            actual_config_digest = actual_bundle_id_parts[1]

            bundle_id_parts = bundle_id.split('-')
            bundle_digest = bundle_id_parts[0]
            config_digest = bundle_id_parts[1]

            bundle_digest_matches = actual_bundle_digest == bundle_digest or \
                actual_bundle_digest.startswith(bundle_digest)
            config_digest_matches = actual_config_digest == config_digest or \
                actual_config_digest.startswith(config_digest)

            return bundle_digest_matches and config_digest_matches
        else:
            return actual_bundle_id.startswith(bundle_id)
