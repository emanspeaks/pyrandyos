from .gregorian import ymdhms_to_sec

_JAN = 1
_JUL = 7

# default leap seconds from naif0012.tls
LEAPS_TABLE = [
    10, ymdhms_to_sec(1972, _JAN, 1, 0, 0, 0),  # -883656000.0,
    11, ymdhms_to_sec(1972, _JUL, 1, 0, 0, 0),  # -867931200.0,
    12, ymdhms_to_sec(1973, _JAN, 1, 0, 0, 0),  # -852033600.0,
    13, ymdhms_to_sec(1974, _JAN, 1, 0, 0, 0),  # -820497600.0,
    14, ymdhms_to_sec(1975, _JAN, 1, 0, 0, 0),  # -788961600.0,
    15, ymdhms_to_sec(1976, _JAN, 1, 0, 0, 0),  # -757425600.0,
    16, ymdhms_to_sec(1977, _JAN, 1, 0, 0, 0),  # -725803200.0,
    17, ymdhms_to_sec(1978, _JAN, 1, 0, 0, 0),  # -694267200.0,
    18, ymdhms_to_sec(1979, _JAN, 1, 0, 0, 0),  # -662731200.0,
    19, ymdhms_to_sec(1980, _JAN, 1, 0, 0, 0),  # -631195200.0,
    20, ymdhms_to_sec(1981, _JUL, 1, 0, 0, 0),  # -583934400.0,
    21, ymdhms_to_sec(1982, _JUL, 1, 0, 0, 0),  # -552398400.0,
    22, ymdhms_to_sec(1983, _JUL, 1, 0, 0, 0),  # -520862400.0,
    23, ymdhms_to_sec(1985, _JUL, 1, 0, 0, 0),  # -457704000.0,
    24, ymdhms_to_sec(1988, _JAN, 1, 0, 0, 0),  # -378734400.0,
    25, ymdhms_to_sec(1990, _JAN, 1, 0, 0, 0),  # -315576000.0,
    26, ymdhms_to_sec(1991, _JAN, 1, 0, 0, 0),  # -284040000.0,
    27, ymdhms_to_sec(1992, _JUL, 1, 0, 0, 0),  # -236779200.0,
    28, ymdhms_to_sec(1993, _JUL, 1, 0, 0, 0),  # -205243200.0,
    29, ymdhms_to_sec(1994, _JUL, 1, 0, 0, 0),  # -173707200.0,
    30, ymdhms_to_sec(1996, _JAN, 1, 0, 0, 0),  # -126273600.0,
    31, ymdhms_to_sec(1997, _JUL, 1, 0, 0, 0),  # -79012800.0,
    32, ymdhms_to_sec(1999, _JAN, 1, 0, 0, 0),  # -31579200.0,
    33, ymdhms_to_sec(2006, _JAN, 1, 0, 0, 0),  # 189345600.0,
    34, ymdhms_to_sec(2009, _JAN, 1, 0, 0, 0),  # 284040000.0,
    35, ymdhms_to_sec(2012, _JUL, 1, 0, 0, 0),  # 394372800.0,
    36, ymdhms_to_sec(2015, _JUL, 1, 0, 0, 0),  # 488980800.0,
    37, ymdhms_to_sec(2017, _JAN, 1, 0, 0, 0),  # 536500800.0,
]


def get_leaps_at_utc(utc: float):
    # if the current time equals the timestamp, it means
    # our current "seconds" are ambiguous.  If we had additional information
    # that can distinguish leap seconds, we could do that instead.
    # Since we do not, we are forced to use the same TAI
    # for 23:59:60 and 0:00:00 in this current implementation.

    # for epochs before the first leap second, return delta et at
    # the epoch of the leap second minus one second.
    lastleap = LEAPS_TABLE[0] - 1
    leap = utc*0.0 + lastleap

    for newleap, epoch in zip(LEAPS_TABLE[::2], LEAPS_TABLE[1::2]):
        # tai = utc + leap
        dleap = newleap - lastleap
        leap += (utc >= epoch)*dleap
        lastleap = newleap

    return leap


def get_leaps_at_tai(tai: float):
    # for epochs before the first leap second, return delta et at
    # the epoch of the leap second minus one second.
    lastleap = LEAPS_TABLE[0] - 1
    leap = tai*0.0 + lastleap

    for newleap, epoch in zip(LEAPS_TABLE[::2], LEAPS_TABLE[1::2]):
        # tai = utc + leap
        dleap = newleap - lastleap
        leap += ((tai - newleap) >= epoch)*dleap
        lastleap = newleap

    return leap
