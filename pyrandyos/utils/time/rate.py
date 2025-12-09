from enum import Enum, auto

from .base_convert import (
    eastern_to_utc, central_to_utc, mountain_to_utc, pacific_to_utc,
    utc_to_eastern, utc_to_central, utc_to_mountain, utc_to_pacific,
    tai_to_tt, tt_to_et, tai_to_utc, utc_to_unix
)


class BaseClockRate(Enum):
    UNIX = auto()
    "Ticks with UTC (folds with UTC leaps); starts prior to beginning of UTC"
    UTC = auto()
    "Ticks with TAI, but stretches/folds with leaps"
    TAI = auto()
    "No leap seconds, ticks with TT but fixed offset for historical reasons"
    TT = auto()
    "No leap seconds"
    T_EPH = auto()
    "SPICE relativistic time, ET = JPL T_eph = SPICE TDB"
    US_ET = auto()
    """
    Tick with UTC, folds with UTC leaps, and folds with DST.
    Combines EST and EDT into one clock.
    """
    US_CT = auto()
    """
    Tick with UTC, folds with UTC leaps, and folds with DST.
    Combines CST and CDT into one clock.
    """
    US_MT = auto()
    """
    Tick with UTC, folds with UTC leaps, and folds with DST.
    Combines MST and MDT into one clock.
    """
    US_PT = auto()
    """
    Tick with UTC, folds with UTC leaps, and folds with DST.
    Combines PST and PDT into one clock.
    """


US_DST = {
    BaseClockRate.US_ET: (eastern_to_utc, utc_to_eastern),
    BaseClockRate.US_CT: (central_to_utc, utc_to_central),
    BaseClockRate.US_MT: (mountain_to_utc, utc_to_mountain),
    BaseClockRate.US_PT: (pacific_to_utc, utc_to_pacific),
}


def tai_to_rate(tai: float, rate: BaseClockRate):
    epoch = tai
    if rate is BaseClockRate.TAI:
        return epoch

    if rate in (BaseClockRate.T_EPH, BaseClockRate.TT):
        epoch = tai_to_tt(epoch)
        if rate is BaseClockRate.TT:
            return epoch
        return tt_to_et(epoch)

    epoch = tai_to_utc(epoch)
    if rate is BaseClockRate.UTC:
        return epoch

    if rate is BaseClockRate.UNIX:
        return utc_to_unix(epoch)

    if rate in US_DST:
        return US_DST[rate][1](epoch)
