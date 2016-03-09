from conductr_cli.ansi_colors import RED, YELLOW, UNDERLINE, ENDC
import logging
import sys

# Default python log levels
LOG_LEVEL_DEBUG = logging.DEBUG
LOG_LEVEL_INFO = logging.INFO
LOG_LEVEL_WARN = logging.WARN
LOG_LEVEL_ERROR = logging.ERROR
LOG_LEVEL_CRITICAL = logging.CRITICAL

# Custom log level for ConductR CLI
LOG_LEVEL_VERBOSE = int((LOG_LEVEL_DEBUG + LOG_LEVEL_INFO) / 2)
LOG_LEVEL_PROGRESS = int(LOG_LEVEL_INFO) + 1
LOG_LEVEL_QUIET = int((LOG_LEVEL_INFO + LOG_LEVEL_WARN) / 2)
LOG_LEVEL_SCREEN = int(LOG_LEVEL_CRITICAL + 10)


class ThresholdFilter(logging.Filter):
    def __init__(self, threshold):
        super().__init__()
        self.threshold = threshold

    def filter(self, record):
        return record.levelno < self.threshold


class ExcludeLevelFilter(logging.Filter):
    def __init__(self, level):
        super().__init__()
        self.level = level

    def filter(self, record):
        return record.levelno != self.level


class LevelFilter(logging.Filter):
    def __init__(self, level):
        super().__init__()
        self.level = level

    def filter(self, record):
        return record.levelno == self.level


def verbose(self, message, *args, **kwargs):
    self.log(LOG_LEVEL_VERBOSE, message, *args, **kwargs)


def quiet(self, message, *args, **kwargs):
    self.log(LOG_LEVEL_QUIET, message, *args, **kwargs)


def screen(self, message, *args, **kwargs):
    self.log(LOG_LEVEL_SCREEN, message, *args, **kwargs)


def progress(self, message, *args, **kwargs):
    """
    This method expects `flush` keyword argument.

    If `flush` is set to `False`, then the terminal cursor is moved to the beginning of the line after message is
    printed. This allows text replacement within the terminal, and is used to render something like a progress bar.

    If `flush` is set to `True`, then line break character is appended to the message, causing the terminal cursor to
    move to the next line.

    Thus, the correct use of the progress logging are:

    ```
    log.progress('1%', flush=False) # Terminal shows 1%
    ...
    log.progress('99%', flush=False) # Terminal shows 99% replacing whatever previous value is
    log.progress('Done', flush=True) # Terminal replaces whatever previous value with `Done`, moving to new line

    # continue as normal
    log.info('Hey')
    ```
    """
    flush_required = kwargs.pop('flush')

    line_end = '\r'
    if flush_required:
        line_end = '\n'

    self.log(LOG_LEVEL_PROGRESS, '{}{}'.format(message, line_end), *args, **kwargs)


def is_verbose_enabled(self):
    return self.isEnabledFor(LOG_LEVEL_VERBOSE)


def is_debug_enabled(self):
    return self.isEnabledFor(LOG_LEVEL_DEBUG)


def is_info_enabled(self):
    return self.isEnabledFor(LOG_LEVEL_INFO)


def is_progress_enabled(self):
    return self.isEnabledFor(LOG_LEVEL_PROGRESS)


def is_quiet_enabled(self):
    return self.isEnabledFor(LOG_LEVEL_QUIET)


def is_warn_enabled(self):
    return self.isEnabledFor(LOG_LEVEL_WARN)


def configure_logging(args, output=sys.stdout, err_output=sys.stderr):
    logging.addLevelName(LOG_LEVEL_VERBOSE, 'VERBOSE')
    logging.Logger.verbose = verbose

    logging.addLevelName(LOG_LEVEL_QUIET, 'QUIET')
    logging.Logger.quiet = quiet

    logging.addLevelName(LOG_LEVEL_PROGRESS, 'PROGRESS')
    logging.Logger.progress = progress

    logging.addLevelName(LOG_LEVEL_SCREEN, 'SCREEN')
    logging.Logger.screen = screen

    logging.Logger.is_verbose_enabled = is_verbose_enabled
    logging.Logger.is_debug_enabled = is_debug_enabled
    logging.Logger.is_info_enabled = is_info_enabled
    logging.Logger.is_progress_enabled = is_progress_enabled
    logging.Logger.is_quiet_enabled = is_quiet_enabled
    logging.Logger.is_warn_enabled = is_warn_enabled

    logger = logging.getLogger()
    logger.setLevel('ERROR')

    formatter = logging.Formatter('%(message)s')

    # Clear existing handlers to prevent duplicate log messages
    for handler in logger.handlers:
        logger.removeHandler(handler)

    # Default logger should log all levels up to warning AND exclude LOG_LEVEL_PROGRESS
    # See the progress_handler for more info
    output_handler = logging.StreamHandler(stream=output)
    output_handler.setFormatter(formatter)
    output_handler.addFilter(ThresholdFilter(LOG_LEVEL_WARN))
    output_handler.addFilter(ExcludeLevelFilter(LOG_LEVEL_PROGRESS))
    logger.addHandler(output_handler)

    # Progress logger should exclude all levels of logging except for LOG_LEVEL_PROGRESS
    # The progress logger does not terminate with line break, allowing in-line character replacement in the terminal.
    # This may be used to render something like a progress bar.
    # Because of this, the progress logger should NOT be accumulated with other logs, otherwise the log message display
    # on the terminal will be malformed.
    progress_handler = logging.StreamHandler(stream=output)
    progress_handler.terminator = ''
    progress_handler.setFormatter(logging.Formatter('%(message)s'))
    progress_handler.setLevel(LOG_LEVEL_PROGRESS)
    progress_handler.addFilter(LevelFilter(LOG_LEVEL_PROGRESS))
    logger.addHandler(progress_handler)

    warn_output_formatter = logging.Formatter('{}{}Warning{}: %(message)s'.format(YELLOW, UNDERLINE, ENDC))
    warn_output_handler = logging.StreamHandler(stream=output)
    warn_output_handler.setFormatter(warn_output_formatter)
    warn_output_handler.setLevel(LOG_LEVEL_WARN)
    warn_output_handler.addFilter(ThresholdFilter(LOG_LEVEL_ERROR))
    logger.addHandler(warn_output_handler)

    err_output_formatter = logging.Formatter('{}{}Error{}: %(message)s'.format(RED, UNDERLINE, ENDC))
    err_output_handler = logging.StreamHandler(stream=err_output)
    err_output_handler.setFormatter(err_output_formatter)
    err_output_handler.setLevel(LOG_LEVEL_ERROR)
    err_output_handler.addFilter(ThresholdFilter(LOG_LEVEL_SCREEN))
    logger.addHandler(err_output_handler)

    screen_output_handler = logging.StreamHandler(stream=output)
    screen_output_handler.setFormatter(formatter)
    screen_output_handler.setLevel(LOG_LEVEL_SCREEN)
    logger.addHandler(screen_output_handler)

    conductr_log = logging.getLogger('conductr_cli')
    if vars(args).get('verbose'):
        conductr_log.setLevel('VERBOSE')
    elif vars(args).get('quiet'):
        conductr_log.setLevel('QUIET')
    else:
        conductr_log.setLevel('INFO')
