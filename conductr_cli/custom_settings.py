from pyhocon import ConfigFactory
from pyhocon.exceptions import ConfigMissingException

import os


def load_from_file(args):
    custom_settings_file = vars(args).get('custom_settings_file')
    if custom_settings_file and os.path.exists(custom_settings_file):
        return ConfigFactory.parse_file(custom_settings_file)
    else:
        return None


def load_conductr_credentials(args):
    # When running within DCOS CLI, DCOS CLI will provide authentication functionality.
    if not args.dcos_mode:
        custom_settings = load_from_file(args)
        if custom_settings and get_config_value(custom_settings, 'conductr.auth.enabled'):
            username = get_config_value(custom_settings, 'conductr.auth.username')
            password = get_config_value(custom_settings, 'conductr.auth.password')
            if username and password:
                return username, password
    return None


def load_server_ssl_verification_file(args):
    # When running within DCOS CLI, DCOS CLI has its own setting related to server side SSL verification.
    if not args.dcos_mode:
        custom_settings = load_from_file(args)
        if custom_settings:
            verification_file = get_config_value(custom_settings, 'conductr.server_ssl_verification_file')
            if verification_file:
                return verification_file
    return None


def get_config_value(config, key):
    try:
        return config.get(key)
    except ConfigMissingException:
        return None
