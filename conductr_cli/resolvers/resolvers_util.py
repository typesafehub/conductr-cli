from urllib.parse import urlparse
import os


def is_local_file(uri, require_bundle_conf):
    parsed = urlparse(uri, scheme='file')

    return parsed.scheme == 'file' and os.path.exists(parsed.path) and (
        os.path.isfile(parsed.path) or (
            os.path.isdir(parsed.path) and
            (not require_bundle_conf or os.path.exists(os.path.join(parsed.path, 'bundle.conf')))
        )
    )
