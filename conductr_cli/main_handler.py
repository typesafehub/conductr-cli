import logging
import logging.handlers
import sys


def run(callback):
    try:
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
