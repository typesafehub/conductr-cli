from conductr_cli import license, screen_utils
from conductr_cli.conduct_info_common import DISPLAY_PADDING, display_bundle_id
from conductr_cli.license import UNLICENSED_DISPLAY_TEXT
import logging


def display_bundles(args, bundles):
    if args.quiet:
        display_bundles_quiet(args, bundles)
    else:
        is_license_success, conductr_license = license.get_license(args)
        display_bundles_default(args, is_license_success, conductr_license, bundles)

    return True


def display_bundles_default(args, is_license_success, conductr_license, bundles):
    log = logging.getLogger(__name__)

    if is_license_success:
        license_formatted = license.format_license(conductr_license)
        license_to_display = license_formatted if conductr_license['isLicensed'] \
            else '{}\n{}'.format(UNLICENSED_DISPLAY_TEXT, license_formatted)

        log.screen('{}\n'.format(license_to_display))

    has_tags_key = all('tags' in bundle['attributes'] for bundle in bundles)

    data = [
        {
            'id': display_bundle_id(args, bundle),
            'name': bundle['attributes']['bundleName'],
            'tag': display_tag_or_compatibility_version(bundle, has_tags_key),
            'roles': ', '.join(sorted(bundle['attributes']['roles'])),
            'replications': len(bundle['bundleInstallations']),
            'starting': sum([not execution['isStarted'] for execution in bundle['bundleExecutions']]),
            'executions': sum([execution['isStarted'] for execution in bundle['bundleExecutions']])
        } for bundle in bundles
    ]
    data.insert(0, {
        'id': 'ID',
        'name': 'NAME',
        'tag': 'TAG' if has_tags_key else 'VER',
        'roles': 'ROLES',
        'replications': '#REP',
        'starting': '#STR',
        'executions': '#RUN'
    })

    column_widths = dict(screen_utils.calc_column_widths(data), **{'padding': ' ' * DISPLAY_PADDING})
    has_error = False
    for row in data:
        has_error |= '!' in row['id']
        log.screen('''\
{id: <{id_width}}{padding}\
{name: <{name_width}}{padding}\
{tag: >{tag_width}}{padding}\
{replications: >{replications_width}}{padding}\
{starting: >{starting_width}}{padding}\
{executions: >{executions_width}}{padding}\
{roles: <{roles_width}}'''.format(**dict(row, **column_widths)).rstrip())

    if has_error:
        log.screen('There are errors: use `conduct events` or `conduct logs` for further information')


def display_tag_or_compatibility_version(bundle, has_tags_key):
    if has_tags_key:
        return bundle['attributes']['tags'][0] if bundle['attributes']['tags'] else ""
    else:
        return 'v{}'.format(bundle['attributes']['compatibilityVersion'])


def display_bundles_quiet(args, bundles):
    log = logging.getLogger(__name__)

    for bundle in bundles:
        log.screen(display_bundle_id(args, bundle))
