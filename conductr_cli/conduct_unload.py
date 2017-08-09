from conductr_cli import validation, bundle_installation, control_protocol
import logging


@validation.handle_connection_error
@validation.handle_http_error
def unload(args):
    """`conduct unload` command"""

    log = logging.getLogger(__name__)

    response_json = control_protocol.unload_bundle(args)
    log.info('Bundle unload request sent.')

    if not args.no_wait:
        bundle_installation.wait_for_uninstallation(response_json['bundleId'], args)

    if not args.disable_instructions:
        log.info('Print ConductR info with: {} info{}'.format(args.command, args.cli_parameters))

    if not log.is_info_enabled() and log.is_quiet_enabled():
        log.quiet(response_json['bundleId'])

    return True
