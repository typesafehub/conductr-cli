from conductr_cli import bundle_deploy, bundle_utils, conduct_request, conduct_url, validation, custom_settings, \
    resolver
from conductr_cli.bundle_deploy import display_bundle_id
from conductr_cli.conduct_url import conductr_host
import logging
import urllib


def deploy(args):
    """`conduct deploy` command"""

    log = logging.getLogger(__name__)

    bintray_webhook_secret = custom_settings.load_bintray_webhook_secret(args)
    if not bintray_webhook_secret:
        log.error('The deploy command requires bintray webhook secret to be configured')
        log.error('Add the following configuration to the '
                  'custom settings file {}'.format(vars(args).get('custom_settings_file')))
        log.error('  conductr.continuous-delivery.bintray-webhook-secret = "configured-continuous-delivery-secret"')
        return False

    resolved_version = resolver.resolve_bundle_version(args.custom_settings, args.bundle)
    if not resolved_version:
        log.error('Unable to resolve bundle {}'.format(args.bundle))
        return False

    package_name = resolved_version['package_name']
    tag = resolved_version['tag']
    bundle_id = display_bundle_id(args, resolved_version['digest'])
    bundle_shorthand = '{}:{}-{}'.format(package_name, tag, bundle_id)

    # Build Continuous Delivery URL using our resolver mechanism
    deploy_uri = resolver.continuous_delivery_uri(args.custom_settings, resolved_version)
    if not deploy_uri:
        log.error('Unable to form Continuous Delivery uri for {}'.format(args.bundle))
        return False

    # Confirm with the user unless auto deploy is enabled
    accepted = True if args.auto_deploy else request_deploy_confirmation(resolved_version, args)
    if not accepted:
        log.info('Abort')
        return False

    if args.target_tags:
        tags = [('tag', tag) for tag in args.target_tags]
        deploy_uri += '?' + urllib.parse.urlencode(tags)

    url = conduct_url.url(deploy_uri, args)

    # JSON Payload for deployment request
    payload = {
        'package': resolved_version['package_name'],
        'version': '{}-{}'.format(resolved_version['tag'], resolved_version['digest'])
    }

    # HTTP headers required for deployment request
    hmac_digest = bundle_deploy.generate_hmac_signature(bintray_webhook_secret, resolved_version['package_name'])
    headers = {
        'X-Bintray-Hook-Hmac': hmac_digest
    }

    log.info('Deploying {}'.format(bundle_shorthand))
    response = conduct_request.post(args.dcos_mode, conductr_host(args), url,
                                    json=payload,
                                    headers=headers,
                                    auth=args.conductr_auth,
                                    verify=args.server_verification_file)
    log.info('Deployment request sent.')
    validation.raise_for_status_inc_3xx(response)

    return response


def request_deploy_confirmation(resolved_version, args):
    bundle_id = resolved_version['digest'] if args.long_ids else bundle_utils.short_id(resolved_version['digest'])
    user_input = input('Deploy {}:{}-{}? [Y/n]: '.format(resolved_version['package_name'],
                                                         resolved_version['tag'],
                                                         bundle_id))
    confirmation = (user_input if user_input else 'y').lower().strip()
    return confirmation == 'y' or confirmation == 'yes'
