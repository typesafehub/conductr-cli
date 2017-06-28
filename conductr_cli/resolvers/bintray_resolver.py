from conductr_cli.exceptions import MalformedBundleUriError, BintrayResolutionError, \
    BintrayCredentialsNotFoundError, MalformedBintrayCredentialsError
from conductr_cli.resolvers import uri_resolver
from conductr_cli.resolvers.resolvers_util import is_local_file
from conductr_cli.resolvers.schemes import SCHEME_BUNDLE
from conductr_cli import bundle_shorthand
from requests.exceptions import HTTPError, ConnectionError
import json
import logging
import os
import re
import requests

BINTRAY_API_BASE_URL = 'https://api.bintray.com'
BINTRAY_DOWNLOAD_BASE_URL = 'https://dl.bintray.com'
BINTRAY_DOWNLOAD_REALM = 'Bintray'
BINTRAY_CREDENTIAL_FILE_PATH = '{}/.lightbend/commercial.credentials'.format(os.path.expanduser('~'))
BINTRAY_PROPERTIES_RE = re.compile('^\s*(\S+)\s*=\s*((\S|\S+\s+\S+)+)\s*$')
BINTRAY_LIGHTBEND_ORG = 'lightbend'
BINTRAY_CONDUCTR_COMMERCIAL_REPO = 'commercial-releases'
BINTRAY_CONDUCTR_GENERIC_REPO = 'generic'
BINTRAY_CONDUCTR_CORE_PACKAGE_NAME = 'ConductR-Universal'
BINTRAY_CONDUCTR_AGENT_PACKAGE_NAME = 'ConductR-Agent-Universal'


def supported_schemes():
    return [SCHEME_BUNDLE]


def resolve_bundle(cache_dir, uri):
    log = logging.getLogger(__name__)

    try:
        urn, org, repo, package_name, tag, digest = bundle_shorthand.parse_bundle(uri)
        log.info(log_message('Resolving bundle', org, repo, package_name, tag, digest))

        bintray_auth = load_bintray_credentials(raise_error=False)
        resolved_version = bintray_resolve_version(bintray_auth, org, repo, package_name, tag, digest)
        return bintray_download_artefact(cache_dir, resolved_version, bintray_auth)
    except MalformedBundleUriError as e:
        return False, None, None, e
    except HTTPError as e:
        return False, None, None, e
    except ConnectionError as e:
        return False, None, None, e


def load_bundle_from_cache(cache_dir, uri):
    # When the supplied uri points to a local file, don't load from cache so file can be used as is.
    if is_local_file(uri, require_bundle_conf=True):
        return False, None, None, None
    else:
        log = logging.getLogger(__name__)
        try:
            urn, org, repo, package_name, tag, digest = bundle_shorthand.parse_bundle(uri)
            log.info(log_message('Loading bundle from cache', org, repo, package_name, tag, digest))
            bintray_auth = load_bintray_credentials(raise_error=False)
            resolved_version = bintray_resolve_version(bintray_auth, org, repo, package_name, tag, digest)
            if resolved_version:
                return uri_resolver.load_bundle_from_cache(cache_dir, resolved_version['download_url'])
            else:
                return False, None, None, None
        except MalformedBundleUriError as e:
            return False, None, None, e
        except HTTPError as e:
            return False, None, None, e
        except ConnectionError as e:
            return False, None, None, e


def resolve_bundle_configuration(cache_dir, uri):
    log = logging.getLogger(__name__)

    try:
        urn, org, repo, package_name, tag, digest = bundle_shorthand.parse_bundle_configuration(uri)
        log.info(log_message('Resolving bundle configuration', org, repo, package_name, tag, digest))
        bintray_auth = load_bintray_credentials(raise_error=False)
        resolved_version = bintray_resolve_version(bintray_auth, org, repo, package_name, tag, digest)
        return bintray_download_artefact(cache_dir, resolved_version, bintray_auth)
    except MalformedBundleUriError as e:
        return False, None, None, e
    except HTTPError as e:
        return False, None, None, e
    except ConnectionError as e:
        return False, None, None, e


def load_bundle_configuration_from_cache(cache_dir, uri):
    # When the supplied uri points to a local file, don't load from cache so file can be used as is.
    if is_local_file(uri, require_bundle_conf=False):
        return False, None, None, None
    else:
        log = logging.getLogger(__name__)
        try:
            urn, org, repo, package_name, tag, digest = bundle_shorthand.parse_bundle_configuration(uri)
            log.info(log_message('Loading bundle configuration from cache', org, repo, package_name, tag, digest))
            bintray_auth = load_bintray_credentials(raise_error=False)
            resolved_version = bintray_resolve_version(bintray_auth,
                                                       org, repo, package_name,
                                                       tag, digest)
            if resolved_version:
                return uri_resolver.load_bundle_from_cache(cache_dir, resolved_version['download_url'])
            else:
                return False, None, None, None
        except MalformedBundleUriError as e:
            return False, None, None, e
        except HTTPError as e:
            return False, None, None, e
        except ConnectionError as e:
            return False, None, None, e


def handle_http_error(http_error, org, repo):
    log = logging.getLogger(__name__)
    if http_error.response.status_code == requests.codes.not_found:
        if all(s in http_error.response.text for s in ['Repo', repo, 'was not found']):
            log.debug(
                'Unable to find Bintray repository {}/{}. '
                'If this is a private repository make sure to setup the Bintray credentials at {}'
                .format(org, repo, BINTRAY_CREDENTIAL_FILE_PATH)
            )

    return False, None, None


def resolve_bundle_version(uri):
    log = logging.getLogger(__name__)
    try:
        bintray_auth = load_bintray_credentials(raise_error=False)
        urn, org, repo, package_name, tag, digest = bundle_shorthand.parse_bundle(uri)
        log.info(log_message('Resolving bundle version', org, repo, package_name, tag, digest))
        resolved_version = bintray_resolve_version(bintray_auth, org, repo, package_name, tag=tag, digest=digest)
        return (resolved_version, None) if resolved_version else (None, None)
    except MalformedBundleUriError as e:
        return None, e
    except HTTPError as e:
        return None, e
    except ConnectionError as e:
        return None, e


def continuous_delivery_uri(resolved_version):
    if resolved_version and \
            'resolver' in resolved_version and \
            resolved_version['resolver'] == __name__ and \
            'org' in resolved_version and \
            'repo' in resolved_version:
        return 'deployments/{}/{}/{}'.format(resolved_version['org'], resolved_version['repo'], resolved_version['org'])
    else:
        return None


def bintray_download_artefact(cache_dir, artefact, auth, raise_error=False):
    if artefact:
        return uri_resolver.resolve_file(cache_dir, artefact['download_url'], auth, raise_error)
    else:
        return False, None, None, None


def load_bintray_credentials(raise_error=True, disable_instructions=False):
    log = logging.getLogger(__name__)
    if not os.path.exists(BINTRAY_CREDENTIAL_FILE_PATH):
        if raise_error:
            raise BintrayCredentialsNotFoundError(BINTRAY_CREDENTIAL_FILE_PATH)
        else:
            return None, None, None
    else:
        with open(BINTRAY_CREDENTIAL_FILE_PATH, 'r') as cred_file:
            lines = [line.replace('\n', '') for line in cred_file.readlines()]
            data = dict()
            realm = BINTRAY_DOWNLOAD_REALM
            for line in lines:
                match = BINTRAY_PROPERTIES_RE.match(line)
                if match is not None:
                    try:
                        key, value = match.group(1, 2)
                        if key == 'realm':
                            realm = value
                        elif realm == BINTRAY_DOWNLOAD_REALM:
                            data[key] = value
                    except IndexError:
                        pass

            if 'user' not in data or 'password' not in data:
                if raise_error:
                    raise MalformedBintrayCredentialsError(BINTRAY_CREDENTIAL_FILE_PATH)
                else:
                    return None, None, None

            if not disable_instructions:
                log.info('Bintray credentials loaded from {}'.format(BINTRAY_CREDENTIAL_FILE_PATH))
            return BINTRAY_DOWNLOAD_REALM, data['user'], data['password']


def bintray_resolve_version(bintray_auth, org, repo, package_name,
                            tag=None, digest=None):
    if tag is None and digest is None:
        # Get latest version
        package_endpoint = '{}/packages/{}/{}/{}'.format(BINTRAY_API_BASE_URL, org, repo, package_name)
        package = get_json(bintray_auth, package_endpoint)
        latest_version = package['latest_version']
        if not latest_version:
            # Try to derive from latest tag stored within attribute names
            tags = [attribute_name.replace('latest-', '')
                    for attribute_name in package['attribute_names']
                    if attribute_name.startswith('latest-')]

            if tags:
                latest_tag = tags[-1]
                return bintray_resolve_version(bintray_auth, org, repo, package_name, tag=latest_tag)
            else:
                raise BintrayResolutionError(
                    'Unable to find latest version for owner={} repo={} package={}'.format(org, repo, package_name))

        elif '-' not in latest_version:
            raise BintrayResolutionError(
                'Malformed latest version number {} for owner={} repo={} package={}'.format(
                    latest_version, org, repo, package_name))

        else:
            latest_tag, latest_digest = package['latest_version'].rsplit('-', 1)
            return bintray_resolve_version(bintray_auth,
                                           org, repo, package_name,
                                           tag=latest_tag, digest=latest_digest)

    elif tag is not None and digest is None:
        # Get latest tag
        latest_tag = 'latest-{}'.format(tag)
        attributes_endpoint = '{}/packages/{}/{}/{}/attributes?names={}'.format(BINTRAY_API_BASE_URL, org, repo,
                                                                                package_name,
                                                                                latest_tag)
        attributes = get_json(bintray_auth, attributes_endpoint)
        matching_versions = [attribute['values'][0]
                             for attribute in attributes
                             if attribute['type'] == 'version' and
                             attribute['name'] == latest_tag and
                             attribute['values']]
        if not matching_versions:
            return None
        else:
            matching_version = matching_versions[0]
            matching_tag, matching_digest = matching_version.rsplit('-', 1)
            return bintray_resolve_version(bintray_auth, org, repo, package_name,
                                           tag=matching_tag, digest=matching_digest)
    else:
        bintray_version = '{}-{}'.format(tag, digest)
        artefacts = bintray_artefacts_by_version(bintray_auth,
                                                 org, repo, package_name, bintray_version)

        if len(artefacts) > 1:
            raise BintrayResolutionError(
                'Unable to resolve - multiple versions found for owner={} repo={} package={} version={}'.format(
                    org, repo, package_name, bintray_version))

        elif not artefacts:
            raise BintrayResolutionError(
                'Unable to find version for owner={} repo={} package={} version={}'.format(
                    org, repo, package_name, bintray_version))

        else:
            resolved_version = artefacts[0].copy()
            resolved_version.update({
                'tag': tag,
                'digest': digest
            })
            return resolved_version


def bintray_artefacts_by_version(bintray_auth, org, repo, package_name, bintray_version):
    files_endpoint = '{}/packages/{}/{}/{}/versions/{}/files'.format(BINTRAY_API_BASE_URL, org, repo, package_name,
                                                                     bintray_version)
    files = get_json(bintray_auth, files_endpoint)
    return [
        {
            'org': org,
            'repo': repo,
            'package_name': package_name,
            'version': bintray_version,
            'path': f['path'],
            'download_url': '{}/{}/{}/{}'.format(BINTRAY_DOWNLOAD_BASE_URL, org, repo, f['path']),
            'resolver': __name__
        }
        for f in files
        if f['owner'] == org and
        f['repo'] == repo and
        f['package'] == package_name and
        f['version'] == bintray_version
    ]


def get_json(auth, uri):
    realm, username, password = auth if auth else (None, None, None)

    if username is not None and password is not None:
        response = requests.get(uri, auth=(username, password))
    else:
        response = requests.get(uri)
    response.raise_for_status()
    return json.loads(response.text)


def log_message(message, org, repo, package_name, tag, digest):
    if tag is None and digest is None:
        return '{} {}/{}/{}'.format(message, org, repo, package_name)
    elif tag is not None and digest is None:
        return '{} {}/{}/{}:{}'.format(message, org, repo, package_name, tag)
    else:
        version = '{}-{}'.format(tag, digest)
        return '{} {}/{}/{}:{}'.format(message, org, repo, package_name, version)
