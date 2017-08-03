import json
import logging

from conductr_cli import conduct_url, conduct_request, validation
from conductr_cli.conduct_url import conductr_host
from conductr_cli.http import DEFAULT_HTTP_TIMEOUT


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

    return json.loads(response.text)


def stop_bundle(args):
    log = logging.getLogger(__name__)

    path = 'bundles/{}?scale=0'.format(args.bundle)
    url = conduct_url.url(path, args)
    response = conduct_request.put(args.dcos_mode, conductr_host(args), url, auth=args.conductr_auth,
                                   verify=args.server_verification_file, timeout=DEFAULT_HTTP_TIMEOUT)
    validation.raise_for_status_inc_3xx(response)

    if log.is_verbose_enabled():
        log.verbose(validation.pretty_json(response.text))

    return json.loads(response.text)


def get_agents(args):
    log = logging.getLogger(__name__)

    url = conduct_url.url('agents', args)
    response = conduct_request.get(args.dcos_mode, conductr_host(args), url, auth=args.conductr_auth,
                                   verify=args.server_verification_file, timeout=DEFAULT_HTTP_TIMEOUT)

    validation.raise_for_status_inc_3xx(response)

    if log.is_verbose_enabled():
        log.verbose(validation.pretty_json(response.text))

    return json.loads(response.text)


def get_members(args):
    log = logging.getLogger(__name__)

    url = conduct_url.url('members', args)
    response = conduct_request.get(args.dcos_mode, conductr_host(args), url, auth=args.conductr_auth,
                                   verify=args.server_verification_file, timeout=DEFAULT_HTTP_TIMEOUT)

    validation.raise_for_status_inc_3xx(response)

    if log.is_verbose_enabled():
        log.verbose(validation.pretty_json(response.text))

    return json.loads(response.text)


def run_bundle(args):
    log = logging.getLogger(__name__)
    if args.affinity is not None:
        path = 'bundles/{}?scale={}&affinity={}'.format(args.bundle, args.scale, args.affinity)
    else:
        path = 'bundles/{}?scale={}'.format(args.bundle, args.scale)

    url = conduct_url.url(path, args)
    response = conduct_request.put(args.dcos_mode, conductr_host(args), url, auth=args.conductr_auth,
                                   verify=args.server_verification_file)
    validation.raise_for_status_inc_3xx(response)

    if log.is_verbose_enabled():
        log.verbose(validation.pretty_json(response.text))

    return json.loads(response.text)


def get_scale(args):
    bundles_url = conduct_url.url('bundles', args)
    response = conduct_request.get(args.dcos_mode, conduct_url.conductr_host(args), bundles_url,
                                   auth=args.conductr_auth, verify=args.server_verification_file)
    response.raise_for_status()
    return json.loads(response.text)
