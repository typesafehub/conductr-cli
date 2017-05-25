from conductr_cli import conduct_request, conduct_url, license_auth, validation
from conductr_cli.conduct_url import conductr_host
from conductr_cli.exceptions import LicenseDownloadError
from dcos.errors import DCOSHTTPException
import arrow
import base64
import datetime
import json
import logging
import requests
import os

EXPIRY_DATE_DISPLAY_FORMAT = '%a %d %b %Y %H:%M%p'

UNLICENSED_DISPLAY_TEXT = 'UNLICENSED - please use "conduct load-license" to use more agents. ' \
                          'Additional agents are freely available for registered users.'


def download_license(args, save_to, use_cached_auth_token):
    """
    Downloads license from Lightbend.com.
    :param args: input args obtained from argparse.
    :param save_to: the path where downloaded license will be saved to.
    :return: path to the license file.
    """

    log = logging.getLogger(__name__)

    auth_token = None
    if use_cached_auth_token:
        auth_token = license_auth.get_cached_auth_token()

    if not auth_token:
        auth_token = license_auth.prompt_for_auth_token()

    auth_token_b64_bytes = base64.b64encode(bytes(auth_token, 'UTF-8'))
    auth_token_b64 = auth_token_b64_bytes.decode('UTF-8')

    auth_header = {'Authorization': 'Bearer {}'.format(auth_token_b64)}
    response = requests.get(args.license_download_url,
                            headers=auth_header,
                            verify=args.server_verification_file)

    if log.is_verbose_enabled():
        log.verbose(response.text)

    if response.status_code == 401 or response.status_code == 303:
        license_auth.remove_cached_auth_token()
        raise LicenseDownloadError([response.text])

    elif response.status_code == 403:
        raise LicenseDownloadError([response.text])

    validation.raise_for_status_inc_3xx(response)

    license_auth.save_auth_token(auth_token)
    save_license_data(response.text, save_to)


def save_license_data(license_data, save_to):
    """
    Saves license data to a specified path.
    :param license_data: The license data in text
    :param save_to: the file where the license will be saved to
    """
    os.makedirs(os.path.dirname(save_to), exist_ok=True)
    with open(save_to, 'w', encoding="utf-8") as f:
        f.write(license_data)


def post_license(args, license_file):
    """
    Post license file to ConductR.
    :param args: input args obtained from argparse
    :param license_file: the path to license file
    """
    url = conduct_url.url('license', args)
    response = conduct_request.post(args.dcos_mode, conductr_host(args), url,
                                    data=open(license_file, 'rb'),
                                    auth=args.conductr_auth,
                                    verify=args.server_verification_file)
    if response.status_code == 503:
        return False
    else:
        validation.raise_for_status_inc_3xx(response)
        return True


def format_license(license):
    """
    Returns formatted license for display, or None if the input is none

    :param args: input args obtained from argparse
    """

    def format(key, title_text, format_value=None):
        if key in license:
            if license[key]:
                value = license[key]
                display_value = format_value(value) if format_value else value
                return '{}: {}'.format(title_text, display_value)

        return None

    def format_multiple(key, title_text):
        if key in license:
            values = license[key]
            if values:
                return '{}: {}'.format(title_text, ', '.join(values))

        return None

    if license:
        license_entries = [
            format('user', 'Licensed To'),
            format('maxConductrAgents', 'Max ConductR agents'),
            format('expires', 'Expires In', format_value=format_expiry),
            format_multiple('conductrVersions', 'ConductR Version(s)'),
            format_multiple('grants', 'Grants'),
        ]
        return '\n'.join([v for v in license_entries if v])
    else:
        return None


def get_license(args):
    """
    Get license from ConductR.
    Returns a tuple of Boolean, get_license_payload. The following return values are allowed
    - False, None: License endpoint does not exist at the ConductR control protocol
    - True, None: No license has been uploaded to ConductR
    - True, license_data: Returns the current license from ConductR
    :param args: input args obtained from argparse
    """
    url = conduct_url.url('license', args)
    try:
        response = conduct_request.get(args.dcos_mode, conductr_host(args), url, auth=args.conductr_auth)
        if response.status_code == 404 or response.status_code == 503:
            return False, None
        else:
            validation.raise_for_status_inc_3xx(response)
            return True, json.loads(response.text)
    except DCOSHTTPException as e:
        if e.response.status_code == 404 or e.response.status_code == 503:
            return False, None
        else:
            raise e


def format_expiry(expiry_date):
    expiry_date_local = arrow.get(expiry_date).to('local')
    expiry_date_display = expiry_date_local.strftime(EXPIRY_DATE_DISPLAY_FORMAT)

    days_to_expiry = calculate_days_to_expiry(expiry_date)

    if days_to_expiry > 0:
        expiry_state = '{} days'.format(days_to_expiry)
    elif days_to_expiry == 0:
        expiry_state = 'Today'
    else:
        expiry_state = 'Expired'

    return '{} ({})'.format(expiry_state, expiry_date_display)


def calculate_days_to_expiry(expiry_date):
    expiry_date_local = arrow.get(expiry_date).to('local')

    now = arrow.get(current_date()).to('local')

    diff = expiry_date_local - now
    return diff.days


def current_date():
    """
    Method is created since Python's `patch` method doesn't work with datetime.datetime.now()
    :return: datetime.now()
    """
    return datetime.datetime.now()
