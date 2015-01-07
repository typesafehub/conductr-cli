from unittest.mock import MagicMock


def respond_with(status_code=200, text=""):
    reasons = {
        200: "OK",
        404: "Not Found"
    }

    response_mock = MagicMock(
        status_code=status_code,
        text=text,
        reason=reasons[status_code])
    response_mock.raise_for_status.return_value = False

    http_method = MagicMock(return_value=response_mock)

    return http_method


def output(logger):
    return "".join([args[0].rstrip(" ") for name, args, kwargs in logger.method_calls])


def strip_margin(string, marginChar='|'):
    return "\n".join([line[line.index(marginChar)+1:] for line in string.split("\n")])
