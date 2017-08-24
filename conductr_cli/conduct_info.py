from conductr_cli import conduct_info_inspect, conduct_info_list, validation, control_protocol


@validation.handle_connection_error
@validation.handle_http_error
def info(args):
    """`conduct info command"""

    bundles = control_protocol.get_bundles(args)
    if args.bundle:
        return conduct_info_inspect.display_bundle(args, bundles, args.bundle)
    else:
        return conduct_info_list.display_bundles(args, bundles)
