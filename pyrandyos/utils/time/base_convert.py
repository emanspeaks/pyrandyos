from math import sin

from .leaps import get_leaps_at_tai, get_leaps_at_utc
from .datetime import utcoffset, utcoffset_local
from .timezone import TZCEN, TZEAS, TZMTN, TZPAC

# GPS: Jan 06 1980 00:00:00.000 UTC
GPST_EPOCH_TAI = -630763181.0

# GPS: Jan 1 1970 00:00:00.000 UTC
UNIX_UTC_SEC = -946728000.0

TT_MINUS_TAI_SEC = 32.184

# The formulation for UNITIM in SPICE depends on a number of kernel pool
# variables set in the leap second kernel file.  The pool variable names
# are all prefixed with `DELTET/`, so variable names referred to below are
# assumed to have this prefix.
#
# The offset between Teph (called ET/TDB in SPICE parlance) and TT
# is a function of the heliocentric orbit of the Earth-Moon barycenter
# (EMB).  As such, the constants `EB`, `M[0]`, and `M[1]` define properties of
# that orbit.
#  - `EB` is the eccentricity of the heliocentric EMB orbit (we call it e)
#  - `M[0]` is the mean anomaly at J2000.0 TT (we call it m0)
#  - `M[1]` is the mean motion (we call it n)
#
# The constant `K` is defined in Moyer Part 2.
#   K = 2*sqrt(mu_sun*a_emb)/c^2
# (from eq. 2 in section 2.1, coefficient of the sin E terms)
#
# Note that the values referenced directly in the text of the paper itself
# differ in their last digit from what is specified here.  Perhaps the paper
# employed rounding while these values are truncated.  Regardless, for
# for consistency with JPL products, we must assume the values as given in the
# leap second kernels.  These values are unlikely to change so as not to break
# backwards compatibility with older kernels.  However, users can supply their
# own values to our `unitim` should they ever need to be different.
#
# Reference:
#   Moyer, T.D., Transformation from Proper Time on Earth to
#   Coordinate Time in Solar System Barycentric Space-Time Frame
#   of Reference, Part 2, Celestial Mechanics 23 (1981), Pages 58-59
MOYER_K = 1.657e-3
EMB_E = 1.671e-2
# The provenance of these exact values in the LSK are unknown at this time
EMB_M0 = 6.239996e0
EMB_N = 1.99096871e-7


def emb_kepler(tt: float):
    m = EMB_M0 + EMB_N*tt
    return MOYER_K*sin(m + EMB_E*sin(m))


def et_to_tt(et: float):
    # Since K*M1*(1+EB) is quite small (on the order of 10**-9)
    # 3 iterations should get us as close as we can get to the
    # solution for TDT
    tt = et
    for i in range(3):
        tt = et - emb_kepler(tt)
    return tt


def utc_to_et(utc: float):
    tai = utc_to_tai(utc)
    tt = tai_to_tt(tai)
    return tt_to_et(tt)


def et_to_utc(et: float):
    tt = et_to_tt(et)
    tai = tt_to_tai(tt)
    return tai_to_utc(tai)


def et_to_ut1(et: float, dut1: float):
    utc = et_to_utc(et)
    return utc_to_ut1(utc, dut1)


def tt_to_et(tt: float):
    return tt + emb_kepler(tt)


def tai_to_tt(tai: float):
    return tai + TT_MINUS_TAI_SEC


def tt_to_tai(tt: float):
    return tt - TT_MINUS_TAI_SEC


def tai_to_utc(tai: float, leap: float = None):
    if leap is None:
        leap = get_leaps_at_tai(tai)

    # tai = utc + leap
    return tai - leap


def utc_to_ut1(utc: float, dut1: float):
    return utc + dut1


def tai_to_gpst(tai: float):
    return tai + GPST_EPOCH_TAI


def gpst_to_tai(gpst: float):
    return gpst - GPST_EPOCH_TAI


def utc_to_gpst(utc: float, leap: float = None):
    tai = utc_to_tai(utc, leap)
    return tai_to_gpst(tai)


def gpst_to_utc(gpst: float, leap: float = None):
    tai = gpst_to_tai(gpst)
    return tai_to_utc(tai, leap)


def utc_to_eastern(utc: float):
    return utc + utcoffset(utc, TZEAS)


def utc_to_central(utc: float):
    return utc + utcoffset(utc, TZCEN)


def utc_to_mountain(utc: float):
    return utc + utcoffset(utc, TZMTN)


def utc_to_pacific(utc: float):
    return utc + utcoffset(utc, TZPAC)


def eastern_to_utc(local: float, fold: int = 0, dst_known: bool = False):
    return local - utcoffset_local(local, TZEAS, fold, dst_known)


def central_to_utc(local: float, fold: int = 0, dst_known: bool = False):
    return local - utcoffset_local(local, TZCEN, fold, dst_known)


def mountain_to_utc(local: float, fold: int = 0, dst_known: bool = False):
    return local - utcoffset_local(local, TZMTN, fold, dst_known)


def pacific_to_utc(local: float, fold: int = 0, dst_known: bool = False):
    return local - utcoffset_local(local, TZPAC, fold, dst_known)


def ut1_to_utc(ut1: float, dut1: float):
    return ut1 - dut1


def utc_to_tai(utc: float, leap: float = None):
    if leap is None:
        leap = get_leaps_at_utc(utc)

    # tai = utc + leap
    return utc + leap


def unix_to_utc(unix: float):
    return unix + UNIX_UTC_SEC


def utc_to_unix(utc: float):
    return utc - UNIX_UTC_SEC


def unix_to_central(unix: float):
    utc = unix_to_utc(unix)
    return utc_to_central(utc)
