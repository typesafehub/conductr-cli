import logging

from conductr_cli import conduct_url, conduct_request, validation
from conductr_cli.conduct_url import conductr_host


def load_bundle(args, multipart_files):
    log = logging.getLogger(__name__)

    url = conduct_url.url('bundles', args)
    response = conduct_request.post(args.dcos_mode, conductr_host(args), url,
                                    data=multipart_files,
                                    auth=args.conductr_auth,
                                    verify=args.server_verification_file,
                                    headers={'Content-Type': multipart_files.content_type})
    validation.raise_for_status_inc_3xx(response)

    if log.is_verbose_enabled():
        log.verbose(validation.pretty_json(response.text))

    return response.text
