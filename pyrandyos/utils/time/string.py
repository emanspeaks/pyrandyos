from .gregorian import sec_to_ymdhms, sec_to_y_doy_hms
from .dhms import sec_to_dhms


def ymdhms_to_iso(y: int, mo: int, d: int, h: int, m: int,
                  s: float, use_T: bool = True, zone: str = 'Z',
                  sec_digits: int = 0):
    if sec_digits is None:
        sec_digits = 0

    ystr = '{:04d}'.format(y)
    mostr = '{:02d}'.format(mo)
    dstr = '{:02d}'.format(d)
    tstr = 'T' if use_T else ' '
    hmsstr = hms_to_str(h, m, s, sec_digits)
    return f'{ystr}-{mostr}-{dstr}{tstr}{hmsstr}{zone}'


def y_doy_hms_to_str(y: int, doy: int, h: int, m: int, s: float,
                     sec_digits: int = 0):
    if sec_digits is None:
        sec_digits = 0

    ystr = '{:04d}'.format(y)
    dhmsstr = dhms_to_met_str(doy, h, m, s, sec_digits=sec_digits,
                              day_digits=3, daysep=':')
    return f'{ystr}:{dhmsstr}'


def format_number(x: float | int, digits: int = None, zeropad: int = 0):
    """
    Print a number with the given number of optional digits.
    If `digits` is none, defaults to Python standard printing.

    Args:
        x (float | int): number to round and print
        digits (int, optional): Prints the given number of digits.
            Positive values are number of digits following the decimal,
            zero rounds to nearest int, negatives are powers of 1/10.
            Defaults to None (use default Python print).
        zeropad (int, optional): Pad the front of the number with zeros,
            ensuring the integer part of the number is at least `zeropad`
            digits wide.  For a time value, this should be 2.
            Defaults to 0 (no zero padding).

    Returns:
        str: formatted number
    """
    if digits is None:
        return str(x)  # just use python default
    pos_dig = digits > 0
    pad = '0' if zeropad else ''
    print_chars = pos_dig*(digits + 1) + 1 + (zeropad - 1)
    scalar = pow(10, digits)
    y = round(x*scalar)/scalar
    return f'{{:{pad}{print_chars}.{digits*pos_dig}f}}'.format(y)


def hms_to_str(h: int, m: int, s: float, sec_digits: int = 3):
    hstr = '{:02d}'.format(h)
    mstr = '{:02d}'.format(m)
    # sstr = f'{{:0{sec_digits + 2 + (sec_digits > 0)}.{sec_digits}f}}'.format(s)  # noqa: E501
    sstr = format_number(s, sec_digits, 2)
    return f'{hstr}:{mstr}:{sstr}'


def dhms_to_met_str(d: int, h: int, m: int, s: float, sign: int = 1,
                    sec_digits: int = 3, day_digits: int = 2,
                    daysep: str = '/'):
    if sec_digits is None:
        sec_digits = 3

    signstr = '-' if sign < 0 else ''
    dstr = f'{{:0{day_digits}d}}'.format(d)
    return f'{signstr}{dstr}{daysep}{hms_to_str(h, m, s, sec_digits)}'


def sec_to_dhms_str(sec: float, sec_digits: int = 3):
    return dhms_to_met_str(*sec_to_dhms(sec, sec_digits), sec_digits)


def sec_to_ymdhms_str(sec: float, sec_digits: int = 0):
    return ymdhms_to_iso(*sec_to_ymdhms(sec, sec_digits), use_T=False, zone='',
                         sec_digits=sec_digits)


def sec_to_y_doy_hms_str(sec: float, sec_digits: int = 0):
    y_doy_hms = sec_to_y_doy_hms(sec, sec_digits)
    return y_doy_hms_to_str(*y_doy_hms, sec_digits=sec_digits)
