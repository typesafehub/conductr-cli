from conductr_cli import license
from conductr_cli.constants import DEFAULT_SCHEME, DEFAULT_PORT, DEFAULT_BASE_PATH, DEFAULT_API_VERSION
from conductr_cli.exceptions import LicenseValidationError
import os

CONDUCTR_GRANT = 'conductr'
DEFAULT_NUMBER_OF_AGENTS = 1
DEFAULT_GRANTS = [CONDUCTR_GRANT]


class LicenseArgs:
    """
    The `args` to be passed in the methods available on the `license` module.

    This provides the equivalent of the arguments normally retrieved from the user input from `argparse` required by
    the `license` module.

    This class is meant to be used internally within this module.
    """
    def __init__(self, core_addr):
        self.host = str(core_addr)

    scheme = DEFAULT_SCHEME
    port = DEFAULT_PORT
    base_path = DEFAULT_BASE_PATH
    api_version = DEFAULT_API_VERSION
    dcos_mode = False
    conductr_auth = None
    server_verification_file = None

    def __eq__(self, other):
        return self.__dict__ == other.__dict__ if isinstance(other, self.__class__) else False


def validate_license(conductr_version, core_addr, nr_of_agent_instances, license_file):
    """
    Validates the license contained within `license_file`.
    Waits for ConductR to be available on the `core_addr` by checking the `/members` endpoint.
    Once ConductR is available, `license_file` is posted, and subsequently retrieved from ConductR as JSON.

    The resulting JSON payload is then validated:
    - Version is in the list of what is allowed.
    - Number of agent requested < what is allowed.
    - Expiry: license must not expire.
    - Grants must include `conductr`.

     If validation failed, sandbox will be stopped and `LicenseValidationError` exception will be raised.

    :param conductr_version: Version of ConductR to be run as sandbox.
    :param core_addr: Host address of one of the core node.
    :param nr_of_agent_instances: Number of agents requested.
    :param license_file: License file to be validated.
    :return:
    """

    args = LicenseArgs(core_addr)

    has_license_support, license_existing = license.get_license(args)
    if has_license_support:
        if os.path.exists(license_file):
            license.post_license(args, license_file)

        has_license_support, license_updated = license.get_license(args)
        validate_license_data(conductr_version, nr_of_agent_instances, license_updated)


def validate_license_data(conductr_version, nr_of_agent_instances, license):
    validate_version(conductr_version, license)
    validate_nr_of_agents(nr_of_agent_instances, license)
    validate_expiry(license)
    validate_grants(license)


def validate_version(conductr_version, license_data):
    versions = get_value(license_data, 'conductrVersions')
    if versions:
        for version in versions:
            if can_run_version(version, conductr_version):
                return

        raise LicenseValidationError([
            'Sandbox version {} requested'.format(conductr_version),
            'The license allows for version {}'.format(', '.join(versions))
        ])


def validate_nr_of_agents(nr_of_agent_instances, license_data):
    nr_of_allowed_agents = get_value(license_data, 'maxConductrAgents')
    if nr_of_allowed_agents and nr_of_agent_instances > nr_of_allowed_agents:
        raise LicenseValidationError([
            '{} agents requested'.format(nr_of_agent_instances),
            'The license allows for {} agent(s)'.format(nr_of_allowed_agents)
        ])


def validate_expiry(license_data):
    expiry_date = get_value(license_data, 'expires')
    if expiry_date:
        days_to_expiry = license.calculate_days_to_expiry(expiry_date)
        if days_to_expiry < 0:
            raise LicenseValidationError([
                'License has expired',
                license.format_expiry(expiry_date)
            ])


def validate_grants(license_data):
    grants = get_value(license_data, 'grants')
    if not grants:
        raise LicenseValidationError([
            'License does not include grant for {}'.format(CONDUCTR_GRANT),
            'The license does not have any grant declared'
        ])
    elif CONDUCTR_GRANT not in grants:
        raise LicenseValidationError([
            'License does not include grant for {}'.format(CONDUCTR_GRANT),
            'The license has grants for {}'.format(', '.join(grants))
        ])


def get_value(license_data, key):
    if license_data:
        if key in license_data:
            value = license_data[key]
            if value:
                return value

    return None


def can_run_version(version_pattern, version_number):
    if version_pattern != version_number:
        version_pattern_parts = version_pattern.split('.')
        version_number_parts = version_number.split('.')

        for idx, pattern in enumerate(version_pattern_parts):
            if idx >= len(version_number_parts):
                return False
            elif pattern == '*':
                return True

            number_part = version_number_parts[idx]
            if pattern != number_part:
                return False

    return True
