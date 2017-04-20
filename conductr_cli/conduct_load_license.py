from conductr_cli import license, validation
from conductr_cli.constants import DEFAULT_LICENSE_FILE
from conductr_cli.conduct_url import conductr_host
from conductr_cli.exceptions import LicenseLoadError
import logging
import os


@validation.handle_connection_error
@validation.handle_http_error
@validation.handle_license_load_error
@validation.handle_license_download_error
def load_license(args):
    log = logging.getLogger(__name__)

    if license.get_license(args) == (False, None):
        if not args.quiet:
            # Only log the info if quite is False.
            # This is the default when the user executes conduct load-license
            # If the function is called from another Python function it might makes sense to set quiet to True
            # to do not print any license output for ConductR versions prior to 2.1
            log.info('conduct load-license is only supported by ConductR 2.1+')
        return True
    else:
        license_file = DEFAULT_LICENSE_FILE
        if args.offline_mode:
            log.info('Skipping downloading license from Lightbend.com')
        else:
            license.download_license(args, save_to=license_file, use_cached_auth_token=(not args.force_flag_enabled))

        if os.path.exists(license_file):
            host = conductr_host(args)
            log.info('Loading license into ConductR at {}'.format(host))
            license.post_license(args, license_file)

            _, uploaded_license = license.get_license(args)
            if uploaded_license:
                license_to_display = license.format_license(uploaded_license)
                log.info('\n{}\n'.format(license_to_display))
                log.info('License successfully loaded')
                return True
            else:
                raise LicenseLoadError('Unable to find recently loaded license')
        else:
            raise LicenseLoadError('Please ensure the license file exists at {}'.format(license_file))
