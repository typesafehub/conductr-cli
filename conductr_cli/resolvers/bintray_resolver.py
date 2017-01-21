from conductr_cli.exceptions import MalformedBundleUriError, BintrayResolutionError, \
    BintrayCredentialsNotFoundError, MalformedBintrayCredentialsError
from conductr_cli.resolvers import uri_resolver
from conductr_cli import bundle_shorthand
from requests.exceptions import HTTPError, ConnectionError
from urllib.parse import urlparse
import json
import logging
import os
import re
import requests

BINTRAY_API_BASE_URL = 'https://api.bintray.com'
BINTRAY_DOWNLOAD_BASE_URL = 'https://dl.bintray.com'
BINTRAY_DOWNLOAD_REALM = 'Bintray'
BINTRAY_CREDENTIAL_FILE_PATH = '{}/.lightbend/commercial.credentials'.format(os.path.expanduser('~'))
BINTRAY_PROPERTIES_RE = re.compile('^(\S+)\s*=\s*([\S]+)$')
BINTRAY_LIGHTBEND_ORG = 'lightbend'
BINTRAY_CONDUCTR_REPO = 'commercial-releases'
BINTRAY_CONDUCTR_CORE_PACKAGE_NAME = 'ConductR-Universal'
BINTRAY_CONDUCTR_AGENT_PACKAGE_NAME = 'ConductR-Agent-Universal'


def resolve_bundle(cache_dir, uri):
    log = logging.getLogger(__name__)
    try:
        urn, org, repo, package_name, compatibility_version, digest = bundle_shorthand.parse_bundle(uri)
        log.info(log_message('Resolving bundle', org, repo, package_name, compatibility_version, digest))
        return bintray_download(cache_dir, org, repo, package_name,
                                compatibility_version=compatibility_version, digest=digest)
    except MalformedBundleUriError:
        return False, None, None
    except HTTPError:
        return False, None, None
    except ConnectionError:
        return False, None, None


def load_bundle_from_cache(cache_dir, uri, offline_mode=False):
    # When the supplied uri points to a local file, don't load from cache so file can be used as is.
    if is_local_file(uri):
        return False, None, None
    else:
        log = logging.getLogger(__name__)
        try:
            urn, org, repo, package_name, compatibility_version, digest = bundle_shorthand.parse_bundle(uri)
            log.info(log_message('Loading bundle from cache', org, repo, package_name, compatibility_version, digest))
            bundle_download_url, auth = bintray_download_details(org, repo, package_name,
                                                                 compatibility_version=compatibility_version,
                                                                 digest=digest)
            if bundle_download_url:
                return uri_resolver.load_bundle_from_cache(cache_dir, bundle_download_url, offline_mode)
            else:
                return False, None, None
        except MalformedBundleUriError:
            return False, None, None
        except HTTPError:
            return False, None, None
        except ConnectionError:
            return False, None, None


def resolve_bundle_configuration(cache_dir, uri):
    log = logging.getLogger(__name__)
    try:
        urn, org, repo, package_name, compatibility_version, digest = bundle_shorthand.parse_bundle_configuration(uri)
        log.info(log_message('Resolving bundle configuration', org, repo, package_name, compatibility_version, digest))
        return bintray_download(cache_dir, org, repo, package_name,
                                compatibility_version=compatibility_version, digest=digest)
    except MalformedBundleUriError:
        return False, None, None
    except HTTPError:
        return False, None, None
    except ConnectionError:
        return False, None, None


def load_bundle_configuration_from_cache(cache_dir, uri, offline_mode=False):
    # When the supplied uri points to a local file, don't load from cache so file can be used as is.
    if is_local_file(uri):
        return False, None, None
    else:
        log = logging.getLogger(__name__)
        try:
            urn, org, repo, package_name, compatibility_version, digest = bundle_shorthand.parse_bundle_configuration(uri)
            log.info(log_message('Loading bundle configuration from cache',
                                 org, repo, package_name, compatibility_version, digest))
            bundle_download_url, auth = bintray_download_details(org, repo, package_name,
                                                                 compatibility_version=compatibility_version,
                                                                 digest=digest)
            if bundle_download_url:
                return uri_resolver.load_bundle_from_cache(cache_dir, bundle_download_url, offline_mode)
            else:
                return False, None, None
        except MalformedBundleUriError:
            return False, None, None
        except HTTPError:
            return False, None, None
        except ConnectionError:
            return False, None, None


def resolve_bundle_version(uri):
    log = logging.getLogger(__name__)
    try:
        bintray_username, bintray_password = load_bintray_credentials()
        urn, org, repo, package_name, compatibility_version, digest = bundle_shorthand.parse_bundle(uri)
        log.info(log_message('Resolving bundle version', org, repo, package_name, compatibility_version, digest))
        resolved_version = bintray_resolve_version(bintray_username, bintray_password, org, repo, package_name,
                                                   compatibility_version=compatibility_version, digest=digest)
        return resolved_version if resolved_version else None
    except MalformedBundleUriError:
        return None
    except HTTPError:
        return None
    except ConnectionError:
        return None


def continuous_delivery_uri(resolved_version):
    if resolved_version and \
            'resolver' in resolved_version and \
            resolved_version['resolver'] == __name__ and \
            'org' in resolved_version and \
            'repo' in resolved_version:
        return 'deployments/{}/{}/{}'.format(resolved_version['org'], resolved_version['repo'], resolved_version['org'])
    else:
        return None


def is_local_file(uri):
    parsed = urlparse(uri, scheme='file')
    return parsed.scheme == 'file' and parsed.path.endswith('.zip') and os.path.exists(uri)


def bintray_download(cache_dir, org, repo, package_name,
                     auth=None, version=None, compatibility_version=None, digest=None):
    download_url, auth = bintray_download_details(org, repo, package_name, auth,
                                                  version, compatibility_version, digest)
    if download_url:
        return uri_resolver.resolve_file(cache_dir, download_url, auth)
    else:
        return False, None, None


def bintray_download_details(org, repo, package_name, auth=None, version=None, compatibility_version=None, digest=None):
    if auth:
        bintray_username, bintray_password = (auth[1], auth[2])
    else:
        bintray_username, bintray_password = load_bintray_credentials()
        auth = (BINTRAY_DOWNLOAD_REALM, bintray_username, bintray_password) if bintray_username else None
    resolved_version = bintray_resolve_version(bintray_username, bintray_password, org, repo, package_name,
                                               version, compatibility_version, digest)
    if resolved_version and auth:
        bintray_download_url = '{}/{}/{}/{}'.format(BINTRAY_DOWNLOAD_BASE_URL, resolved_version['org'],
                                                    resolved_version['repo'], resolved_version['path'])
        return bintray_download_url, auth
    else:
        return None, None


def load_bintray_credentials():
    log = logging.getLogger(__name__)
    if not os.path.exists(BINTRAY_CREDENTIAL_FILE_PATH):
        raise BintrayCredentialsNotFoundError(BINTRAY_CREDENTIAL_FILE_PATH)
    else:
        with open(BINTRAY_CREDENTIAL_FILE_PATH, 'r') as cred_file:
            lines = [line.replace('\n', '') for line in cred_file.readlines()]
            data = dict()
            for line in lines:
                match = BINTRAY_PROPERTIES_RE.match(line)
                if match is not None:
                    try:
                        key, value = match.group(1, 2)
                        data[key] = value
                    except IndexError:
                        pass

            if 'user' not in data or 'password' not in data:
                raise MalformedBintrayCredentialsError(BINTRAY_CREDENTIAL_FILE_PATH)
            log.info('Bintray credentials loaded from {}'.format(BINTRAY_CREDENTIAL_FILE_PATH))
            return data['user'], data['password']


def bintray_resolve_version(bintray_username, bintray_password, org, repo, package_name,
                            version=None, compatibility_version=None, digest=None):
    if version is None and compatibility_version is None and digest is None:
        # Get latest version
        package_endpoint = '{}/packages/{}/{}/{}'.format(BINTRAY_API_BASE_URL, org, repo, package_name)
        package = get_json(package_endpoint, bintray_username, bintray_password)
        latest_version = package['latest_version']
        if not latest_version:
            # Try to derive from latest compatibility versions stored within attribute names
            compatibility_versions = [int(attribute_name.replace('latest-v', ''))
                                      for attribute_name in package['attribute_names']
                                      if attribute_name.startswith('latest-v')]

            if compatibility_versions:
                latest_compatibility_version = sorted(compatibility_versions)[-1]
                return bintray_resolve_version(bintray_username, bintray_password,
                                               org, repo, package_name,
                                               compatibility_version='v{}'.format(latest_compatibility_version))
            else:
                raise BintrayResolutionError(
                    'Unable to find latest version for owner={} repo={} package={}'.format(org, repo, package_name))

        elif '-' not in latest_version:
            raise BintrayResolutionError(
                'Malformed latest version number {} for owner={} repo={} package={}'.format(
                    latest_version, org, repo, package_name))

        else:
            latest_compatibility_version, latest_digest = package['latest_version'].split('-')
            return bintray_resolve_version(bintray_username, bintray_password, org, repo, package_name,
                                           compatibility_version=latest_compatibility_version, digest=latest_digest)

    elif version is None and compatibility_version is not None and digest is None:
        # Get latest of a compatibility version
        latest_compatibility_version = 'latest-{}'.format(compatibility_version)
        attributes_endpoint = '{}/packages/{}/{}/{}/attributes?names={}'.format(BINTRAY_API_BASE_URL, org, repo,
                                                                                package_name,
                                                                                latest_compatibility_version)
        attributes = get_json(attributes_endpoint, bintray_username, bintray_password)
        matching_versions = [attribute['values'][0]
                             for attribute in attributes
                             if attribute['type'] == 'version' and
                             attribute['name'] == latest_compatibility_version and
                             attribute['values']]
        if not matching_versions:
            return None
        else:
            matching_version = matching_versions[0]
            matching_compatibility_version, matching_digest = matching_version.split('-')
            return bintray_resolve_version(bintray_username, bintray_password, org, repo, package_name,
                                           compatibility_version=matching_compatibility_version, digest=matching_digest)
    else:
        if version:
            bintray_version = version
        else:
            bintray_version = '{}-{}'.format(compatibility_version, digest)

        files_endpoint = '{}/packages/{}/{}/{}/versions/{}/files'.format(BINTRAY_API_BASE_URL, org, repo, package_name,
                                                                         bintray_version)
        files = get_json(files_endpoint, bintray_username, bintray_password)
        matching_files = [f
                          for f in files
                          if f['owner'] == org and
                          f['repo'] == repo and
                          f['package'] == package_name and
                          f['version'] == bintray_version]
        if len(matching_files) > 1:
            raise BintrayResolutionError(
                'Unable to resolve - multiple versions found for owner={} repo={} package={} version={}'.format(
                    org, repo, package_name, bintray_version))

        elif not matching_files:
            raise BintrayResolutionError(
                'Unable to find version for owner={} repo={} package={} version={}'.format(
                    org, repo, package_name, bintray_version))

        else:
            path = matching_files[0]['path']
            resolved_version = {
                'org': org,
                'repo': repo,
                'package_name': package_name,
                'compatibility_version': compatibility_version,
                'digest': digest,
                'version': bintray_version,
                'path': path,
                'resolver': __name__
            }
            return resolved_version


def get_json(uri, username, password):
    if username is not None and password is not None:
        response = requests.get(uri, auth=(username, password))
    else:
        response = requests.get(uri)
    response.raise_for_status()
    return json.loads(response.text)


def log_message(message, org, repo, package_name, compatibility_version, digest):
    if compatibility_version is None and digest is None:
        return '{} {}/{}/{}'.format(message, org, repo, package_name)
    elif compatibility_version is not None and digest is None:
        return '{} {}/{}/{}:{}'.format(message, org, repo, package_name, compatibility_version)
    else:
        version = '{}-{}'.format(compatibility_version, digest)
        return '{} {}/{}/{}:{}'.format(message, org, repo, package_name, version)
