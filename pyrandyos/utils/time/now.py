from time import time as _unixnow

from .base_convert import unix_to_utc, utc_to_tai


def now_unix_sec():
    return _unixnow()


def now_utc_sec():
    unix = now_unix_sec()
    return unix_to_utc(unix)


def now_tai_sec():
    utc = now_utc_sec()
    return utc_to_tai(utc)
