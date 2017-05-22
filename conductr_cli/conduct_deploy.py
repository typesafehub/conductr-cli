from conductr_cli import bundle_deploy_v2, bundle_deploy_v3, conduct_deploy_bintray, conduct_deploy_bundle, validation
import json
import logging


DEFAULT_WAIT_TIMEOUT = 180  # seconds


@validation.handle_connection_error
@validation.handle_http_error
@validation.handle_invalid_config
@validation.handle_no_file
@validation.handle_bad_zip
@validation.handle_malformed_bundle
@validation.handle_bundle_resolution_error
@validation.handle_wait_timeout_error
@validation.handle_conduct_load_read_timeout_error
@validation.handle_insecure_file_permissions
@validation.handle_bintray_resolution_error
@validation.handle_bintray_credentials_error
def deploy(args):
    """`conduct deploy` command"""

    log = logging.getLogger(__name__)

    webhook = args.webhook
    if webhook and webhook.lower() == 'bintray':
        response = conduct_deploy_bintray.deploy(args)
    elif webhook:
        log.error('Unsupported webhook {}'.format(webhook))
        return False
    else:
        response = conduct_deploy_bundle.deploy(args)

    if not response:
        return False

    validation.raise_for_status_inc_3xx(response)

    if is_json_response(response):
        deployment_batch = json.loads(response.text)
        deployment_batch_id = deployment_batch['value']
        if not args.no_wait:
            bundle_deploy_v3.wait_for_deployment_complete(deployment_batch_id, args)
    else:
        deployment_id = response.text
        if not args.no_wait:
            bundle_deploy_v2.wait_for_deployment_complete(deployment_id, args)

    return True


def is_json_response(response):
    return 'Content-Type' in response.headers and response.headers['Content-Type'] == 'application/json'
