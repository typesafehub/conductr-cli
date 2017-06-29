import logging
import logging.handlers
import os
import sys


# Needs to be Python 3.4 or above
SUPPORTED_PYTHON_VERSION = (3, 4)


def run(callback):
    try:
        enforce_python_version()
        enforce_cwd_exists()
        result = callback()
        return result
    except KeyboardInterrupt:
        # Ctrl+C is pressed - silently exit
        pass
    except SystemExit as e:
        # The callback requested system exit - comply accordingly
        raise e
    except:
        from conductr_cli.constants import DEFAULT_ERROR_LOG_FILE

        # Ensure log dir is present before errors are being logged
        log_dir = os.path.abspath(os.path.join(DEFAULT_ERROR_LOG_FILE, '..'))
        os.makedirs(log_dir, exist_ok=True)

        log = logging.getLogger('conductr_cli.main')
        log.error('Encountered unexpected error.')
        ex_type, ex, ex_trace = sys.exc_info()
        log.error('Reason: {} {}'.format(ex_type.__name__, str(ex)))
        log.error('Further information of the error can be found in the error log file: {}'.format(
            DEFAULT_ERROR_LOG_FILE))

        exception_log = logging.getLogger('conductr_cli.main.exception')
        # Set propagate to false to prevent log message being propagated to default error level log handler to prevent
        # the stacktrace being displayed on screen
        exception_log.propagate = False
        fmt = logging.Formatter('%(asctime)s: %(message)s')
        handler = logging.handlers.RotatingFileHandler(DEFAULT_ERROR_LOG_FILE, maxBytes=3000000, backupCount=1)
        handler.setFormatter(fmt)
        exception_log.addHandler(handler)
        exception_log.error('Failure running the following command: {}'.format(sys.argv), exc_info=True)

        sys.exit(1)


def enforce_cwd_exists():
    try:
        os.getcwd()
    except FileNotFoundError:
        sys.exit('Unable to start CLI due to missing current/working directory.\n'
                 'Change into a new directory and try again.\n')


def enforce_python_version():
    if sys.version_info < SUPPORTED_PYTHON_VERSION:
        major, minor, micro, release_level, serial = sys.version_info
        supported_major_version, supported_minor_version = SUPPORTED_PYTHON_VERSION
        sys.exit('Unable to start CLI.\n'
                 'Current python version is {}.{}.{}\n'
                 'Please use python version {}.{} and above.'.format(major, minor, micro,
                                                                     supported_major_version, supported_minor_version))
