from conductr_cli.exceptions import MalformedBundleUriError, BintrayResolutionError
from conductr_cli.resolvers import uri_resolver
from conductr_cli import bundle_shorthand
from requests.exceptions import HTTPError
import json
import logging
import os
import re
import requests


BINTRAY_API_BASE_URL = 'https://api.bintray.com'
BINTRAY_DOWNLOAD_BASE_URL = 'https://dl.bintray.com'
BINTRAY_DOWNLOAD_REALM = 'Bintray'
BINTRAY_CREDENTIAL_FILE_PATH = '{}/.bintray/.credentials'.format(os.path.expanduser('~'))
BINTRAY_PROPERTIES_RE = re.compile('^(\S+)\s*=\s*([\S]+)$')


def resolve_bundle(cache_dir, uri):
    log = logging.getLogger(__name__)
    try:
        bintray_username, bintray_password = load_bintray_credentials()
        urn, org, repo, package_name, compatibility_version, digest = bundle_shorthand.parse(uri)
        log.info(log_message('Resolving bundle', org, repo, package_name, compatibility_version, digest))
        bundle_download_url = bintray_download_url(bintray_username, bintray_password, org, repo, package_name,
                                                   compatibility_version, digest)
        if bundle_download_url:
            auth = (BINTRAY_DOWNLOAD_REALM, bintray_username, bintray_password) if bintray_username else None
            return uri_resolver.resolve_bundle(cache_dir, bundle_download_url, auth)
        else:
            return False, None, None
    except MalformedBundleUriError:
        return False, None, None
    except HTTPError:
        return False, None, None


def load_from_cache(cache_dir, uri):
    log = logging.getLogger(__name__)
    try:
        bintray_username, bintray_password = load_bintray_credentials()
        urn, org, repo, package_name, compatibility_version, digest = bundle_shorthand.parse(uri)
        log.info(log_message('Loading bundle from cache', org, repo, package_name, compatibility_version, digest))
        bundle_download_url = bintray_download_url(bintray_username, bintray_password, org, repo, package_name,
                                                   compatibility_version, digest)
        if bundle_download_url:
            return uri_resolver.load_from_cache(cache_dir, bundle_download_url)
        else:
            return False, None, None
    except MalformedBundleUriError:
        return False, None, None
    except HTTPError:
        return False, None, None


def load_bintray_credentials():
    log = logging.getLogger(__name__)
    if not os.path.exists(BINTRAY_CREDENTIAL_FILE_PATH):
        log.debug('Bintray credentials not found in {}'.format(BINTRAY_CREDENTIAL_FILE_PATH))
        return None, None
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

            username = None if 'user' not in data else data['user']
            password = None if 'password' not in data else data['password']
            log.info('Bintray credentials loaded from {}'.format(BINTRAY_CREDENTIAL_FILE_PATH))
            return username, password


def bintray_download_url(bintray_username, bintray_password, org, repo, package_name, compatibility_version, digest):
    if compatibility_version is None and digest is None:
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
                return bintray_download_url(bintray_username, bintray_password,
                                            org, repo, package_name,
                                            'v{}'.format(latest_compatibility_version), None)
            else:
                raise BintrayResolutionError(
                    'Unable to find latest version for owner={} repo={} package={}'.format(org, repo, package_name))
        elif '-' not in latest_version:
            raise BintrayResolutionError(
                'Malformed latest version number {} for owner={} repo={} package={}'.format(
                    latest_version, org, repo, package_name))
        else:
            latest_compatibility_version, latest_digest = package['latest_version'].split('-')
            return bintray_download_url(bintray_username, bintray_password, org, repo, package_name,
                                        latest_compatibility_version, latest_digest)

    elif compatibility_version is not None and digest is None:
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
            return bintray_download_url(bintray_username, bintray_password, org, repo, package_name,
                                        matching_compatibility_version, matching_digest)
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
            download_url = '{}/{}/{}/{}'.format(BINTRAY_DOWNLOAD_BASE_URL, org, repo, path)
            return download_url


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
