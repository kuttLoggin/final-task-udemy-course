from hashlib import blake2b
from hmac import compare_digest

SEC_KEY = b'secret key to user code'
DIG_SIZE = 18


def encode(code):
    h = blake2b(digest_size=DIG_SIZE, key=SEC_KEY)
    h.update(code)
    return h.hexdigest().encode('utf-8')


def verify(code, sig):
    good_sig = encode(code)
    return compare_digest(good_sig, sig)


def decode(code):
    return code.decode('utf-8')