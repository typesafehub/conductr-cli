from dcos import http
import requests


def delete(dcos_mode, host, url, **kwargs):
    kwargs = enrich_args(host, **kwargs)
    if dcos_mode:
        return http.delete(url, **kwargs)
    else:
        return requests.delete(url, **kwargs)


def get(dcos_mode, host, url, **kwargs):
    kwargs = enrich_args(host, **kwargs)
    if dcos_mode:
        return http.get(url, **kwargs)
    else:
        return requests.get(url, **kwargs)


def post(dcos_mode, host, url, **kwargs):
    kwargs = enrich_args(host, **kwargs)
    if dcos_mode:
        return http.post(url, **kwargs)
    else:
        return requests.post(url, **kwargs)


def put(dcos_mode, host, url, **kwargs):
    kwargs = enrich_args(host, **kwargs)
    if dcos_mode:
        return http.put(url, **kwargs)
    else:
        return requests.put(url, **kwargs)


def enrich_args(host, **kwargs):
    # At the time when this comment is being written, we need to pass the Host header when making HTTP request due to
    # a bug with requests python library not working properly when IPv6 address is supplied:
    # https://github.com/kennethreitz/requests/issues/3002
    # The workaround for this problem is to explicitly set the Host header when making HTTP request.
    # This fix is benign and backward compatible as the library would do this when making HTTP request anyway.
    revised_headers = kwargs['headers'] if 'headers' in kwargs else {}
    revised_headers.update({'Host': host})
    kwargs['headers'] = revised_headers
    return kwargs
