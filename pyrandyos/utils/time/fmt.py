from enum import Enum

from pyrandyos.utils.casesafe import casesafe_key_in_dict

from .string import (
    format_number, sec_to_dhms_str, sec_to_y_doy_hms_str, sec_to_ymdhms_str
)
from .julian import DAY2SEC
from .dhms import sec_to_dhms
from .gregorian import sec_to_ymdhms, sec_to_y_doy_hms


class TimeFormat(Enum):
    S = 's'
    M = 'm'
    H = 'h'
    D = 'd'
    DHMS = 't'  # T as in T-Minus
    Y_DOY_HMS = 'g'  # short for "GMT day"
    YMDHMS = 'c'  # short for "calendar"
    # ISO = 'i'


FLOAT_FMTS = (
    TimeFormat.S,
    TimeFormat.M,
    TimeFormat.H,
    TimeFormat.D,
)


def parse_time_format(input_fmt: str):
    if input_fmt is None:
        return

    fmt_map = TimeFormat.__members__
    if not casesafe_key_in_dict(fmt_map, input_fmt, True):
        x = input_fmt[0].lower()
        if x in fmt_map.values():
            return TimeFormat(x)

    return TimeFormat[input_fmt.upper()]


def sec_as_fmt_str(t: float, fmt: TimeFormat, digits: int = 0,
                   zeropad: int = 0):
    if fmt in FLOAT_FMTS:
        return format_number(sec_as_fmt(t, fmt, digits),
                             digits, zeropad)

    if fmt is TimeFormat.DHMS:
        return sec_to_dhms_str(t, digits)
    elif fmt is TimeFormat.Y_DOY_HMS:
        return sec_to_y_doy_hms_str(t, digits)
    elif fmt is TimeFormat.YMDHMS:
        return sec_to_ymdhms_str(t, digits)


def sec_as_fmt(t: float, fmt: TimeFormat, digits: int = None):
    if fmt is TimeFormat.S:
        return t
    elif fmt is TimeFormat.M:
        return t/60
    elif fmt is TimeFormat.H:
        return t/3600
    elif fmt is TimeFormat.D:
        return t/DAY2SEC
    elif fmt is TimeFormat.DHMS:
        return sec_to_dhms(t, digits)
    elif fmt is TimeFormat.Y_DOY_HMS:
        return sec_to_y_doy_hms(t, digits)
    elif fmt is TimeFormat.YMDHMS:
        return sec_to_ymdhms(t, digits)


class TimeFormatter:
    def __init__(self, time_format: TimeFormat = None, digits: int = 0,
                 zeropad: int = 0):
        self.digits = digits
        self.zeropad = zeropad
        self.time_format = time_format
        # or (TimeFormat.YMDHMS if is_base else TimeFormat.DHMS)

    def sec_as_fmt(self, t: float):
        return sec_as_fmt(t, self.time_format, self.digits)

    def sec_as_fmt_str(self, t: float):
        return sec_as_fmt_str(t, self.time_format, self.digits,
                              self.zeropad)
