from conductr_cli import conduct_info_inspect, conduct_info_list, conduct_request, conduct_url, validation
from conductr_cli.conduct_url import conductr_host
import json
import logging
from conductr_cli.http import DEFAULT_HTTP_TIMEOUT


@validation.handle_connection_error
@validation.handle_http_error
def info(args):
    """`conduct info` command"""

    log = logging.getLogger(__name__)
    url = conduct_url.url('bundles', args)
    response = conduct_request.get(args.dcos_mode, conductr_host(args), url, auth=args.conductr_auth,
                                   verify=args.server_verification_file, timeout=DEFAULT_HTTP_TIMEOUT)
    validation.raise_for_status_inc_3xx(response)

    if log.is_verbose_enabled():
        log.verbose(validation.pretty_json(response.text))

    bundles = json.loads(response.text)
    if args.bundle:
        return conduct_info_inspect.display_bundle(args, bundles, args.bundle)
    else:
        return conduct_info_list.display_bundles(args, bundles)
