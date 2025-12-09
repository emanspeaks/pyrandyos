from datetime import datetime, tzinfo, timedelta

from .timezone import USTimeZone, TZUTC
from .gregorian import sec_to_ymdhms

MS = timedelta(milliseconds=1)
YMDHMSKEYS = ('year', 'month', 'day', 'hour', 'minute', 'second')


def ymdhms_dict_to_ymdhmsms_dict(ymdhms: dict):
    ymdhmsms = {k: v if isinstance(v, tzinfo) else v + 0
                for k, v in ymdhms.items()}
    sec, ms = divmod(ymdhms['second']*1e6, 1e6)
    ymdhmsms['second'] = int(sec)
    ymdhmsms['microsecond'] = int(ms)
    return ymdhmsms


def sec_to_datetime(sec: float):
    return ymdhms_dict_to_datetime({k: v for k, v in zip(YMDHMSKEYS,
                                                         sec_to_ymdhms(sec))})


def utc_sec_to_datetime(utc: float):
    return sec_to_datetime(utc).replace(tzinfo=TZUTC)


def ymdhms_dict_to_datetime(ymdhms: dict):
    return datetime(**ymdhms_dict_to_ymdhmsms_dict(ymdhms))


def datetime_to_ymdhms(dt: datetime):
    return dt.timetuple()[:6]


def utcoffset(utc: float, tz: tzinfo):
    return utc_sec_to_datetime(utc).astimezone(tz).utcoffset().total_seconds()


def utcoffset_local(local: float, tz: tzinfo, fold: int = 0,
                    dst_known: bool = False):
    dt = sec_to_datetime(local)
    dt.replace(tzinfo=tz, fold=fold)
    kwargs = ({'dst_known': True} if dst_known and isinstance(tz, USTimeZone)
              else {})
    return tz.utcoffset(dt, **kwargs).total_seconds()


def datetime_start_end_to_ms(start: datetime, end: datetime):
    return (end - start)/MS
