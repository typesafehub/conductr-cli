import requests


def patch_raise_for_status(original_raise_for_status):
    """
    monkey-patching response objects to raise status when status code 3xx
    """

    def new_raise_for_status(self):
        original_raise_for_status(self)
        if self.status_code >= 300:
            raise requests.exceptions.HTTPError(requests.status_codes._codes[self.status_code], response=self)

    return new_raise_for_status

requests.models.Response.raise_for_status = patch_raise_for_status(requests.models.Response.raise_for_status)
