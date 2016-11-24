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
    enriched_kwargs = {}
    for key in kwargs:
        if key not in ['headers', 'auth', 'verify']:
            enriched_kwargs.update({key: kwargs[key]})

    # At the time when this comment is being written, we need to pass the Host header when making HTTP request due to
    # a bug with requests python library not working properly when IPv6 address is supplied:
    # https://github.com/kennethreitz/requests/issues/3002
    # The workaround for this problem is to explicitly set the Host header when making HTTP request.
    # This fix is benign and backward compatible as the library would do this when making HTTP request anyway.
    revised_headers = kwargs['headers'] if 'headers' in kwargs else {}
    revised_headers.update({'Host': host})
    enriched_kwargs['headers'] = revised_headers

    # Setup credentials only if it exists in the `kwargs` and it's not `None`
    if 'auth' in kwargs and kwargs['auth']:
        enriched_kwargs['auth'] = kwargs['auth']

    # Setup SSL cert verification only if it exists in the `kwargs` and it's not `None`
    if 'verify' in kwargs and kwargs['verify']:
        enriched_kwargs['verify'] = kwargs['verify']

    return enriched_kwargs
