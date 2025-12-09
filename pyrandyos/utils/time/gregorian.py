from .julian import DAY2SEC

DAYSINMONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
WEEKDAY_CHARS = 'NMTWRFS'


def year_is_divisible(year: int, i: int):
    return max(0, 1 + (year//i)*i - abs(year))


def is_leap_year(year: int):
    return (year_is_divisible(year, 4) - year_is_divisible(year, 100)
            + year_is_divisible(year, 400))


def ymdhms_to_sec(y: int, mo: int, d: int, h: int, m: int,
                  s: float):
    # this code is derived from the SPICE TPARSE subroutine.
    # assumes the list is ymdhms format.

    # Get the year month and day as integers.
    year = round(y)
    month = round(mo)
    day = round(d)

    # Apply the Muller-Wimberly formula and then tack on the seconds.
    day = (367*year - (7*(year + ((month + 9)//12))//4)
           - (3*(((year + ((month - 9)//7))//100) + 1)//4)
           + (275*month//9) + day - 730516)

    spj2k = (day - 0.5)*DAY2SEC
    spj2k += 3600.0*h
    spj2k += 60.0*m
    spj2k += s
    return spj2k


def day_of_year(year: int, month: int, day: int):
    x = 0
    for i, d in enumerate(DAYSINMONTH):
        x += d*(i + 1 < month)
    return x + day + is_leap_year(year)*(month > 2)


def doy2md(year: int, doy: int):
    isleap = is_leap_year(year)
    day = doy*1
    month = 0*doy + 1
    tmp = 0
    for i, d in enumerate(DAYSINMONTH):
        d += isleap*(i == 1)
        tmp += d
        filt = doy > tmp
        day -= filt*d
        month += filt*1

    return month, day


def days_from_jan1_1ad_to_jan1(year: int):
    """
    The number of days elapsed since Jan 1, of year 1 A.D., to
    Jan 1 of ``year``
    """
    y = year - 1
    return 365*y + y//4 - y//100 + y//400


def days_past_jan1_1ad(year: int, month: int, day: int):
    return days_from_jan1_1ad_to_jan1(year) + day_of_year(year, month, day) - 1


_J2K_MINUS_J1 = days_past_jan1_1ad(2000, 1, 1)
# noink = 146097 days (400 Gregorian years)
# dwiffle = 36524 days (about 100 years)
# shwiel = 1461 days (about 4 years)
#
# Yes, I know 100 years is a century, but often in astronomical fields,
# a century means a Julian century, which is 36525 days.
# A Gregorian "century" is 36524 days UNLESS the year is divisible by 400,
# in which case it's obviously a noink.  So get over yourself and have fun.
# Probably no one will see this code anyways.
_NOINK = 365*400 + 97
_DWIFFLE = 365*100 + 24
_SHWIEL = 365*4 + 1


def sec_to_ymdhms(formal: float, sec_digits: int = None):
    "returns y, mo, d, h, m, s"
    # this method based on code from SPICE TTRANS

    tmp = formal
    scalar = pow(10, sec_digits or 0)
    if sec_digits is not None:
        tmp = round(tmp*scalar)

    tmp, stmp = divmod(tmp + 43200*scalar, 60*scalar)
    s = stmp/scalar
    tmp, m = divmod(tmp, 60)
    days_past_j2k, h = divmod(tmp, 24)
    days_since_jan1_1ad = days_past_j2k + _J2K_MINUS_J1

    noinks, days_since_last_noink = divmod(days_since_jan1_1ad, _NOINK)
    dwiffles = min(3, days_since_last_noink//_DWIFFLE)

    days_since_last_dwiffle = days_since_last_noink - dwiffles*_DWIFFLE
    shwiels = min(24, days_since_last_dwiffle//_SHWIEL)

    days_since_last_shwiel = days_since_last_dwiffle - shwiels*_SHWIEL
    net_years = min(3, days_since_last_shwiel//365)

    doy = days_since_last_shwiel - net_years*365 + 1
    year = noinks*400 + dwiffles*100 + shwiels*4 + net_years + 1
    month, day = doy2md(year, doy)

    return (int(year), int(month), int(day), int(h), int(m), s)


def sec_to_y_doy_hms(formal: float, sec_digits: int = None):
    "returns y, doy, h, m, s"
    ymdhms = sec_to_ymdhms(formal, sec_digits)
    return ymdhms[0], day_of_year(*ymdhms[:3]), *ymdhms[3:]
