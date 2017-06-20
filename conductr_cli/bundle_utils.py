from conductr_cli.constants import DIGEST_TRAIL_SIZE, IO_CHUNK_SIZE
import os
import tempfile
from zipfile import ZipFile


def short_id(bundle_id):
    return '-'.join([part[:7] for part in bundle_id.split('-')])


def conf(bundle_path):
    bundle_zip = ZipFile(bundle_path)
    bundle_configurations = [bundle_zip.read(name) for name in bundle_zip.namelist() if name.endswith('bundle.conf')]
    return bundle_configurations[0].decode('utf-8') if len(bundle_configurations) > 0 else None


def digest_extract_and_open(path):
    """
    Inspects a given `path` for a digest marker at the end of the file and returns
    an open file object that will not include the digest.

    :param path:
    :return: file object without digest, possible digest
    """

    input = open(path, 'rb')
    input.seek(
        -DIGEST_TRAIL_SIZE,
        os.SEEK_END
    )
    digest, trailer_starts, trailer_len = digest_calculate(input.read())
    input.seek(0)

    if trailer_len > 0:
        output = tempfile.NamedTemporaryFile()
        reader = DigestedRead(input)
        done = False

        while not done:
            chunk = reader.read(IO_CHUNK_SIZE)

            if chunk:
                output.write(chunk)
            else:
                done = True

        output.seek(0)

        return output, digest
    else:
        return input, None


def digest_calculate(data):
    digests = ['sha-256']
    digest = None
    trailer_starts = None
    trailer_bytes = []

    for i, v in reversed(list(enumerate(data))):
        if v == 10:
            trailer_starts = i
            break
        else:
            trailer_bytes.insert(0, v)

    if len(trailer_bytes) > 0:
        try:
            parts = bytes(trailer_bytes).decode('UTF-8').split('/')

            if len(parts) == 2 and parts[0] in digests:
                digest = parts[0], parts[1]
        except UnicodeDecodeError:
            pass

    return digest, trailer_starts, 0 if trailer_starts is None else len(trailer_bytes) + 1


class DigestedRead(object):
    def __init__(self, r):
        self.reader = r
        self.digest = None
        self.buffer = b''
        self.done = False
        self.emitted = 0

    def read(self, num_bytes):
        if self.done:
            return b''
        else:
            chunk = self.reader.read(num_bytes)

            if chunk:
                self.buffer += chunk

                if len(self.buffer) > DIGEST_TRAIL_SIZE:
                    data = self.buffer[0:len(self.buffer) - DIGEST_TRAIL_SIZE]

                    self.buffer = self.buffer[-DIGEST_TRAIL_SIZE:]

                    self.emitted += len(data)

                    return data
                else:
                    return self.read(num_bytes)
            else:
                digest, trailer_starts, trailer_length = digest_calculate(self.buffer)

                self.digest = digest
                self.done = True

                return_value = self.buffer if digest is None else self.buffer[0:trailer_starts]

                self.emitted += len(return_value)

                self.buffer = b''

                return return_value
