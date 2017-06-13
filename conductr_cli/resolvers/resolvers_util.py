from urllib.parse import urlparse
from conductr_cli import bundle_shorthand
from conductr_cli.exceptions import MalformedBundleUriError
from conductr_cli.resolvers.schemes import SCHEME_BUNDLE, SCHEME_FILE, SCHEME_STDIN
import os
import sys


def is_local_file(uri, require_bundle_conf):
    parsed = urlparse(uri, scheme='file')

    return parsed.scheme == 'file' and os.path.exists(parsed.path) and (
        os.path.isfile(parsed.path) or (
            os.path.isdir(parsed.path) and
            (not require_bundle_conf or os.path.exists(os.path.join(parsed.path, 'bundle.conf')))
        )
    )


def detect_schemes(uri):
    """
    Detects one or more scheme applicable for a given URI. Returns one or more scheme, because it's possible to apply
    one or more scheme given a URI.

    For example, if the `uri` is `my-bundle`, this is a valid reference to a bundle (indicated by `urn:x-bundle`
    scheme) which can be resolved via `bintray_resolver` or `docker_resolver`.

    However, it is also possible for the local path `my-bundle` to be present also. If the path is present, then the
    `file` scheme is applicable, and therefore in this case both `urn:x-bundle` and `file` are applicable.

    :param uri: input URI
    :return: one or more applicable scheme for the given input URI
    """

    stdin_scheme = detect_stdin(uri)
    if stdin_scheme:
        # No other schemes is possible when accepting input from stdin.
        return [stdin_scheme]

    result = []

    bundle_scheme = detect_bundle_scheme(uri)
    if bundle_scheme:
        result.append(bundle_scheme)

    parsed_scheme = detect_scheme_from_parsed_uri(uri)
    if parsed_scheme:
        result.append(parsed_scheme)

    if SCHEME_FILE not in result:
        local_file_scene = detect_scheme_from_path(uri)
        if local_file_scene:
            result.append(local_file_scene)

    return result


def detect_bundle_scheme(uri):
    """
    Detects if bundle scheme is applicable for the given `uri`.

    :param uri:
    :return: bundle scheme if it's a valid bundle URI, otherwise `None`.
    """
    try:
        bundle_shorthand.parse_bundle(uri)
        return SCHEME_BUNDLE
    except MalformedBundleUriError:
        return None


def detect_scheme_from_parsed_uri(uri):
    """
    Parse the input `uri` using Python's built-in `urlparse`, and then obtains the `scheme` from the parsed result.

    :param uri:
    :return: the scheme from the parsed `uri` result.
    """
    parsed = urlparse(uri)
    return parsed.scheme


def detect_stdin(uri):
    """
    Detects for stdin input.

    :param uri:
    :return: stdin scheme if stdin input is present, otherwise `None`.
    """
    return SCHEME_STDIN if not sys.stdin.isatty() and uri == '-' else None


def detect_scheme_from_path(uri):
    """
    Detects if the `uri` is present on the local file system.

    :param uri:
    :return: file scheme if uri is present on the local file system, otherwise `None`
    """
    return SCHEME_FILE if os.path.exists(uri) else None
