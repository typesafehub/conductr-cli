from conductr_cli import bundle_utils, validation, bundle_scale
import logging

from conductr_cli.control_protocol import stop_bundle


@validation.handle_connection_error
@validation.handle_http_error
@validation.handle_wait_timeout_error
def stop(args):
    """`conduct stop` command"""

    log = logging.getLogger(__name__)
    response_json = stop_bundle(args)

    bundle_id = response_json['bundleId'] if args.long_ids else bundle_utils.short_id(response_json['bundleId'])

    log.info('Bundle stop request sent.')

    if not args.no_wait:
        bundle_scale.wait_for_scale(response_json['bundleId'], 0, wait_for_is_active=False, args=args)

    if not args.disable_instructions:
        log.info('Unload bundle with:       {} unload{} {}'.format(args.command, args.cli_parameters, bundle_id))
        log.info('Print ConductR info with: {} info{}'.format(args.command, args.cli_parameters))
        log.info('Print bundle info with:   {} info{} {}'.format(args.command, args.cli_parameters, bundle_id))

    return True
