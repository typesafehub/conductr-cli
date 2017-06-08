import os

BNDL_DEFAULT_CHECK_RETRY_DELAY = 10

BNDL_DEFAULT_CHECK_RETRY_COUNT = 6

# Preload this much data in the bndl tool to determine input type of a stream. Since we use this to determine
# if a stream is a plain bundle conf, this should be set to hold the maximum size of a reasonable bundle.conf
# or else auto-detection will fail.
BNDL_PEEK_SIZE = 65536

BNDL_IGNORE_TAGS = ['latest']

CONDUCTR_SCHEME = 'CONDUCTR_SCHEME'

DEFAULT_SCHEME = os.getenv(CONDUCTR_SCHEME, 'http')
DEFAULT_PORT = os.getenv('CONDUCTR_PORT', '9005')
DEFAULT_SERVICE_LOCATOR_PORT = os.getenv('CONDUCTR_SERVICE_LOCATOR_PORT', '9008')
DEFAULT_BASE_PATH = os.getenv('CONDUCTR_BASE_PATH', '/')
DEFAULT_API_VERSION = os.getenv('CONDUCTR_API_VERSION', '2')
DEFAULT_DCOS_SERVICE = os.getenv('CONDUCTR_DCOS_SERVICE', 'conductr')
DEFAULT_CLI_SETTINGS_DIR = os.getenv('CONDUCTR_CLI_SETTINGS_DIR', '{}/.conductr'.format(os.path.expanduser('~')))
DEFAULT_RESOLVE_CACHE_DIR = '{}/cache'.format(DEFAULT_CLI_SETTINGS_DIR)
DEFAULT_CLI_TMP_DIR = os.path.abspath(os.getenv('CONDUCTR_CLI_TMP_DIR', '{}/tmp'.format(DEFAULT_CLI_SETTINGS_DIR)))
DEFAULT_BUNDLE_RESOLVE_CACHE_DIR = os.getenv('CONDUCTR_BUNDLE_RESOLVE_CACHE_DIR',
                                             '{}/bundle'.format(DEFAULT_RESOLVE_CACHE_DIR))
DEFAULT_CONFIGURATION_RESOLVE_CACHE_DIR = os.getenv('CONDUCTR_CONFIGURATION_RESOLVE_CACHE_DIR',
                                                    '{}/configuration'
                                                    .format(DEFAULT_RESOLVE_CACHE_DIR))
DEFAULT_CUSTOM_SETTINGS_FILE = os.getenv('CONDUCTR_CUSTOM_SETTINGS_FILE',
                                         '{}/settings.conf'.format(DEFAULT_CLI_SETTINGS_DIR))
DEFAULT_CUSTOM_PLUGINS_DIR = os.getenv('CONDUCTR_CUSTOM_PLUGINS_DIR',
                                       '{}/plugins'.format(DEFAULT_CLI_SETTINGS_DIR))
DEFAULT_OFFLINE_MODE = os.getenv('CONDUCTR_OFFLINE_MODE', False)
DEFAULT_SANDBOX_IMAGE_DIR = os.path.abspath(os.getenv('CONDUCTR_SANDBOX_IMAGE_DIR',
                                                      '{}/images'.format(DEFAULT_CLI_SETTINGS_DIR)))
DEFAULT_SANDBOX_TMP_DIR = os.path.abspath(os.getenv('CONDUCTR_SANDBOX_TMP_DIR',
                                                    '{}/tmp'.format(DEFAULT_SANDBOX_IMAGE_DIR)))
DEFAULT_SANDBOX_ADDR_RANGE = os.getenv('CONDUCTR_SANDBOX_ADDR_RANGE', '192.168.10.0/24')
DEFAULT_SANDBOX_PROXY_DIR = os.path.abspath(os.getenv('CONDUCTR_SANDBOX_PROXY_DIR',
                                                      '{}/proxy'.format(DEFAULT_CLI_SETTINGS_DIR)))
# Prefixed with `sandbox-` to avoid overlap with `cond-` ConductR container names, causing the proxy to be stopped
# when sandbox stop is called for docker containers.
DEFAULT_SANDBOX_PROXY_CONTAINER_NAME = os.getenv('CONDUCTR_SANDBOX_PROXY_CONTAINER_NAME', 'sandbox-haproxy')
DEFAULT_ERROR_LOG_FILE = os.path.abspath(os.getenv('CONDUCTR_CLI_ERROR_LOG',
                                                   '{}/errors.log'.format(DEFAULT_CLI_SETTINGS_DIR)))
DEFAULT_LICENSE_DOWNLOAD_URL = os.getenv('CONDUCTR_LICENSE_DOWNLOAD_URL',
                                         'https://www.lightbend.com/product/conductr/license')
DEFAULT_LICENSE_FILE = os.path.abspath(os.getenv('CONDUCTR_LICENSE_FILE',
                                                 '{}/.lightbend/license'.format(os.path.expanduser('~'))))
DEFAULT_AUTH_TOKEN_FILE = os.path.abspath(os.getenv('CONDUCTR_AUTH_TOKEN_FILE',
                                                    '{}/.lightbend/auth-token'.format(os.path.expanduser('~'))))
DEFAULT_WAIT_TIMEOUT = 60  # seconds

# Must be able to hold the digest value, name of algorithm, and newline character
DIGEST_TRAIL_SIZE = 100

FEATURE_PROVIDE_PROXYING = 'proxying'

FEATURE_PROVIDE_LOGGING = 'logging'


# When reading and writing to IO devices, buffer this many bytes at a time
IO_CHUNK_SIZE = 32768

# Time to wait when retrieving logs (in follow mode) results in an error
LOGS_FOLLOW_ERROR_SLEEP_SECONDS = 10.0

# Time to wait between log requests (in follow mode)
LOGS_FOLLOW_SLEEP_SECONDS = 1.0

# ZIP has a minimum date for timestamps - 315705599 is 01/02/1980 @ 11:59pm (UTC)
SHAZAR_TIMESTAMP_MIN = 315705599

# For auto-detection of input streams, per:
# https://en.wikipedia.org/wiki/Tar_(computing)
# https://en.wikipedia.org/wiki/Zip_(file_format)

MAGIC_NUMBER_TAR = b'ustar'
MAGIC_NUMBER_TAR_OFFSET = 257
MAGIC_NUMBERS_ZIP = [b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08']
