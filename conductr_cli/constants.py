import os


DEFAULT_SCHEME = os.getenv('CONDUCTR_SCHEME', 'http')
DEFAULT_PORT = os.getenv('CONDUCTR_PORT', '9005')
DEFAULT_BASE_PATH = os.getenv('CONDUCTR_BASE_PATH', '/')
DEFAULT_API_VERSION = os.getenv('CONDUCTR_API_VERSION', '2')
DEFAULT_DCOS_SERVICE = os.getenv('CONDUCTR_DCOS_SERVICE', 'conductr')
DEFAULT_CLI_SETTINGS_DIR = os.getenv('CONDUCTR_CLI_SETTINGS_DIR', '{}/.conductr'.format(os.path.expanduser('~')))
DEFAULT_BUNDLE_RESOLVE_CACHE_DIR = os.getenv('CONDUCTR_BUNDLE_RESOLVE_CACHE_DIR',
                                             '{}/cache'.format(DEFAULT_CLI_SETTINGS_DIR))
DEFAULT_CUSTOM_SETTINGS_FILE = os.getenv('CONDUCTR_CUSTOM_SETTINGS_FILE',
                                         '{}/settings.conf'.format(DEFAULT_CLI_SETTINGS_DIR))
DEFAULT_CUSTOM_PLUGINS_DIR = os.getenv('CONDUCTR_CUSTOM_PLUGINS_DIR',
                                       '{}/plugins'.format(DEFAULT_CLI_SETTINGS_DIR))
DEFAULT_ERROR_LOG_FILE = os.path.abspath(os.getenv('CONDUCTR_CLI_ERROR_LOG',
                                                   '{}/errors.log'.format(DEFAULT_CLI_SETTINGS_DIR)))
DEFAULT_WAIT_TIMEOUT = 60  # seconds
