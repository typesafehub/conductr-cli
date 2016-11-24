from conductr_cli import conduct_request
import re


SSE_REQUEST_INPUT = {
    'headers': {
        'Cache-Control': 'no-cache',
        'Accept': 'text/event-stream'
    }
}


SSE_END_OF_FIELD = re.compile(r'\r\n\r\n|\r\r|\n\n')


def is_event_complete(buf):
    return re.search(SSE_END_OF_FIELD, buf) is not None


def parse_event(raw_sse_string):
    event, data = None, None
    lines = raw_sse_string.split('\n')
    for line in lines:
        if line.rstrip():
            key, value = line.split(':')
            if key == 'event':
                event = value
            elif key == 'data':
                data = value
    return Event(event, data)


class Event:
    def __init__(self, event, data):
        self.event = event
        self.data = data

    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)


class Client:
    """
    The following SSE Client has been backported, cut down version of https://bitbucket.org/btubbs/sseclient -
    look at sseclient.py.

    We were not be able to use the SSE client library as it does not have the support for Python 3.2 due
    to the presence of unicode string declaration (i.e. u''). The unicode string declaration is valid from Python 3.3 and
    above, while in Python 3.2 it will result in Syntax error.

    Changes introduced as part of the backport:
    - Support for Python 3.2 (i.e. do not use u'')
    - Parse only for event and data string within SSE
    - No support for retries and last event id
    """
    def __init__(self, dcos_mode, host, url, headers=None, **kwargs):
        self.dcos_mode = dcos_mode
        self.host = host
        self.url = url
        self.headers = headers
        self.responseIter = None
        self.kwargs = kwargs

    def connect(self):
        sse_request_input = dict(SSE_REQUEST_INPUT)
        if self.headers:
            sse_request_input['headers'].update(self.headers)

        kwargs_all = {}
        kwargs_all.update(self.kwargs)
        kwargs_all.update(sse_request_input)

        response = conduct_request.get(self.dcos_mode, self.host, self.url, stream=True, **kwargs_all)
        response.raise_for_status()
        self.responseIter = response.iter_content(decode_unicode=True)

    def __iter__(self):
        return self

    def __next__(self):
        buf = ''
        while not is_event_complete(buf):
            next_char = next(self.responseIter)
            buf += next_char

        split = re.split(SSE_END_OF_FIELD, buf)
        raw_sse = split[0]
        return parse_event(raw_sse)


def get_events(dcos_mode, host, url, headers=None, **kwargs):
    client = Client(dcos_mode, host, url, headers, **kwargs)
    client.connect()
    return client
