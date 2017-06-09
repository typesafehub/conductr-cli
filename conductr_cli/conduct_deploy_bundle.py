from conductr_cli import bundle_utils, conduct_load, conduct_request, conduct_url, constants, resolver, validation
from conductr_cli.bndl_utils import BndlFormat
from conductr_cli.conduct_url import conductr_host
from conductr_cli.exceptions import MalformedBundleError
import logging
import os
import tempfile
import urllib


def deploy(args):
    log = logging.getLogger(__name__)

    log.info('Retrieving bundle..')
    custom_settings = args.custom_settings
    bundle_resolve_cache_dir = args.bundle_resolve_cache_dir
    configuration_cache_dir = args.configuration_resolve_cache_dir

    conduct_load.validate_cache_dir_permissions(bundle_resolve_cache_dir, configuration_cache_dir, log)

    bundle_file_name, bundle_file = resolver.resolve_bundle(custom_settings,
                                                            bundle_resolve_cache_dir,
                                                            args.bundle,
                                                            args.offline_mode)

    if not conduct_load.is_bundle(bundle_file):
        bundle_fileobj = conduct_load.invoke_bndl(bundle_file)
        bundle_file = bundle_fileobj.name

    bundle_conf = bundle_utils.conf(bundle_file)

    if bundle_conf is None:
        raise MalformedBundleError('Unable to find bundle.conf within the bundle file')

    configuration_file_name, configuration_file = (None, None)
    if args.configuration is not None:
        log.info('Retrieving configuration..')
        configuration_file_name, configuration_file = \
            resolver.resolve_bundle_configuration(custom_settings, configuration_cache_dir,
                                                  args.configuration, args.offline_mode)
        if not conduct_load.is_bundle(configuration_file) or conduct_load.bndl_arguments_present(args):
            configuration_fileobj = conduct_load.invoke_bndl(configuration_file, BndlFormat.CONFIGURATION.value,
                                                             args, bundle_conf)
            configuration_file = configuration_fileobj.name
            configuration_file_name = os.path.basename(configuration_file)
    elif conduct_load.bndl_arguments_present(args):
        with tempfile.NamedTemporaryFile() as empty_file:
            os.utime(empty_file.name, (constants.SHAZAR_TIMESTAMP_MIN, constants.SHAZAR_TIMESTAMP_MIN))
            configuration_fileobj = conduct_load.invoke_bndl(empty_file.name, BndlFormat.CONFIGURATION.value,
                                                             args, bundle_conf)
            configuration_file = configuration_fileobj.name
            configuration_file_name = os.path.basename(configuration_file)

    bundle_file_name, bundle_open_file = conduct_load.open_bundle(bundle_file_name, bundle_file, bundle_conf)
    files = [('bundle', (bundle_file_name, bundle_open_file))]
    if configuration_file is not None:
        open_configuration_file, config_digest = bundle_utils.digest_extract_and_open(configuration_file)
        if config_digest is not None and not configuration_file_name.endswith('-{}.zip'.format(config_digest)):
            configuration_file_name = 'config-{}.zip'.format(config_digest[1])

        files.append(('configuration', (configuration_file_name, open_configuration_file)))

    # Confirm with the user unless auto deploy is enabled
    accepted = True if args.auto_deploy else request_deploy_confirmation(bundle_file_name, args)
    if not accepted:
        log.info('Abort')
        return False

    multipart = conduct_load.create_multipart(log, files)

    bundle_file_name_parts = bundle_file_name.split('-')
    bundle_name = '-'.join(bundle_file_name_parts[:len(bundle_file_name_parts) - 2])
    deploy_params = [('bundleName', bundle_name)]

    if args.target_tags:
        tags = [('tag', tag) for tag in args.target_tags]
        deploy_params.extend(tags)

    deploy_uri = 'deployments?' + urllib.parse.urlencode(deploy_params)
    url = conduct_url.url(deploy_uri, args)

    response = conduct_request.post(args.dcos_mode, conductr_host(args), url,
                                    data=multipart,
                                    auth=args.conductr_auth,
                                    verify=args.server_verification_file,
                                    headers={'Content-Type': multipart.content_type})
    validation.raise_for_status_inc_3xx(response)

    return response


def request_deploy_confirmation(bundle_file_name, args):
    user_input = input('Deploy {}? [Y/n]: '.format(bundle_file_name))
    confirmation = (user_input if user_input else 'y').lower().strip()
    return confirmation == 'y' or confirmation == 'yes'
