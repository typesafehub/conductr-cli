import hmac
import base64

STRING_ENCODING = 'UTF-8'
HMAC_DIGEST_MOD = 'SHA256'


def generate_hmac_signature(secret_key, text):
    secret_key_bytes = bytes(secret_key, encoding=STRING_ENCODING)
    text_bytes = bytes(text, encoding=STRING_ENCODING)
    hmac_generator = hmac.new(secret_key_bytes, msg=text_bytes, digestmod=HMAC_DIGEST_MOD)
    signature = hmac_generator.digest()
    return base64.b64encode(signature).decode(STRING_ENCODING)
