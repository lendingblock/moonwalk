import random
import string


def rand_str(n=10):
    return ''.join(random.choices(
        string.ascii_lowercase + string.digits,
        k=n,
    ))


class GeneralError(Exception):
    """raised when something is wrong and we cannot handle it properly"""
