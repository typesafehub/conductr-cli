from pyhocon import ConfigFactory
from pyhocon.exceptions import ConfigMissingException
from conductr_cli import conduct_url

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
        conductr_host = conduct_url.conductr_host(args)
        conductr_port = args.port
        auth_config = get_auth_config(custom_settings, conductr_host, conductr_port)

        if get_config_value(auth_config, 'enabled'):
            username = get_config_value(auth_config, 'username')
            password = get_config_value(auth_config, 'password')
            if username and password:
                return username, password
    return None


def load_server_ssl_verification_file(args):
    # When running within DCOS CLI, DCOS CLI has its own setting related to server side SSL verification.
    if not args.dcos_mode:
        custom_settings = load_from_file(args)
        conductr_host = conduct_url.conductr_host(args)
        conductr_port = args.port
        auth_config = get_auth_config(custom_settings, conductr_host, conductr_port)

        verification_file = get_config_value(auth_config, 'server_ssl_verification_file')
        if verification_file:
            return verification_file

    return None


def load_bintray_webhook_secret(args):
    custom_settings = load_from_file(args)
    return get_config_value(custom_settings, 'conductr.continuous-delivery.bintray-webhook-secret')


def get_auth_config(custom_settings, host, port):
    auth_config_host_port = get_config(custom_settings, 'conductr.auth.\"{}:{}\"'.format(host, port))
    auth_config_host = get_config(custom_settings, 'conductr.auth.\"{}\"'.format(host))
    if auth_config_host_port:
        return auth_config_host_port
    else:
        return auth_config_host


def get_config(config, key):
    try:
        if config:
            return config.get_config(key)
        else:
            return None
    except ConfigMissingException:
        return None


def get_config_value(config, key):
    try:
        if config:
            return config.get(key)
        else:
            return None
    except ConfigMissingException:
        return None
