JY2DAY = 365.25
DAY2SEC = 86400.0
CY2DAY = JY2DAY*100

# from the FreeFlyer documentation:
# * Julian Date: Jan 1 4713 BCE 12:00:00.000 TAI
JDJ2K = 2451545.0
# * MJD GSFC: Jan 05 1941 12:00:00.000 TAI
# used by FreeFlyer
GSFC_MJD = 2430000.0
# * MJD USNO: Nov 17 1858 00:00:00.000 TAI
# used by SOFA and IERS
USNO_MJD = 2400000.5
# * MJD 1950 (Besselian Date 1950.0): Dec 31 1949 22:09:46.862 TAI
M50_EPOCH_TAI_YMDHMS = (1949, 12, 31, 22, 9, 46.862)


def to_usno_mjd(t_sec_j2k: float):
    return t_sec_j2k/DAY2SEC + (JDJ2K - USNO_MJD)


def to_gsfc_mjd(t_sec_j2k: float):
    return t_sec_j2k/DAY2SEC + (JDJ2K - GSFC_MJD)
