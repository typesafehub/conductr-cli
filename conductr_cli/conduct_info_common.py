from conductr_cli import bundle_utils

DISPLAY_PADDING = 2


def display_bundle_id(args, bundle):
    bundle_id = bundle['bundleId'] if args.long_ids else bundle_utils.short_id(bundle['bundleId'])
    has_error_display = '! ' if bundle.get('hasError', False) else ''
    return '{}{}'.format(has_error_display, bundle_id)
