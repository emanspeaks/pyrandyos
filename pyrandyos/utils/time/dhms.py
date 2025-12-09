from .julian import DAY2SEC


def dhms_to_sec(d: int, h: int, m: int, s: float, sign: int = 1):
    return sign*(s + 60*m + 3600*h + DAY2SEC*d)


def sec_to_dhms(x: float, sec_digits: int = None):
    "returns d, h, m, s, sign"
    sign = 1 - 2*(x < 0)
    x *= sign
    d, tmp = divmod(x, DAY2SEC)
    h, tmp = divmod(tmp, 3600)
    scalar = pow(10, sec_digits or 0)
    if sec_digits is not None:
        tmp = round(tmp*scalar)

    m, tmp = divmod(tmp, 60*scalar)
    s = tmp/scalar
    return int(d), int(h), int(m), s, sign
