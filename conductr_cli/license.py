from conductr_cli import conduct_request, conduct_url, validation
from conductr_cli.conduct_url import conductr_host
import arrow
import datetime
import json


EXPIRY_DATE_DISPLAY_FORMAT = '%a %d %b %Y %H:%M%p'

UNLICENSED_DISPLAY_TEXT = 'UNLICENSED - please use "conduct load-license" to use more than one agent. ' \
                          'Additional agents are freely available for registered users.\n' \
                          'Max ConductR agents: 1\n' \
                          'Grants: conductr, cinnamon, akka-sbr'


def download_license(args, save_to):
    """
    Downloads license from Lightbend.com.
    :param args: input args obtained from argparse.
    :param save_to: the path where downloaded license will be saved to.
    :return: path to the license file.
    """
    pass


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
    :param args: input args obtained from argparse
    """
    url = conduct_url.url('license', args)
    response = conduct_request.get(args.dcos_mode, conductr_host(args), url, auth=args.conductr_auth)
    if response.status_code == 404:
        return None
    else:
        validation.raise_for_status_inc_3xx(response)
        return json.loads(response.text)


def format_expiry(expiry_date):
    expiry_date_local = arrow.get(expiry_date).to('local')
    expiry_date_display = expiry_date_local.strftime(EXPIRY_DATE_DISPLAY_FORMAT)

    now = arrow.get(current_date()).to('local')

    diff = expiry_date_local - now
    diff_day = diff.days

    if diff_day > 0:
        expiry_state = '{} days'.format(diff_day)
    elif diff_day == 0:
        expiry_state = 'Today'
    else:
        expiry_state = 'Expired'

    return '{} ({})'.format(expiry_state, expiry_date_display)


def current_date():
    """
    Method is created since Python's `patch` method doesn't work with datetime.datetime.now()
    :return: datetime.now()
    """
    return datetime.datetime.now()
