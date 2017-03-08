from conductr_cli import license, validation
from conductr_cli.constants import DEFAULT_LICENSE_FILE
from conductr_cli.exceptions import LicenseLoadError
import logging
import os


@validation.handle_connection_error
@validation.handle_http_error
@validation.handle_license_load_error
def load_license(args):
    log = logging.getLogger(__name__)

    license_file = DEFAULT_LICENSE_FILE

    if args.offline_mode:
        log.info('Skipping downloading license from Lightbend.com')
    else:
        log.info('Downloading license from Lightbend.com')
        license.download_license(args, save_to=license_file)

    if os.path.exists(license_file):
        log.info('Loading license into ConductR at {}'.format(args.host))
        license.post_license(args, license_file)

        uploaded_license = license.get_license(args)
        if uploaded_license:
            license_to_display = license.format_license(uploaded_license)
            log.info('\n{}\n'.format(license_to_display))
            log.info('License successfully loaded')
            return True
        else:
            raise LicenseLoadError('Unable to find recently loaded license')
    else:
        raise LicenseLoadError('Please ensure the license file exists at {}'.format(license_file))
