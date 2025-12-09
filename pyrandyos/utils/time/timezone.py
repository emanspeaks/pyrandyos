from datetime import datetime, tzinfo, timedelta, timezone

HOUR = timedelta(hours=1)
ZERO = timedelta()


class AmbiguousDstError(ValueError):
    pass


class USTimeZone(tzinfo):
    def __init__(self, name: str, std_offset_hr: int):
        self.std_offset = timedelta(hours=-abs(std_offset_hr))

        self.name = name
        basechar = name.strip().upper()[0]
        self.std_name = f'{basechar}ST'
        self.dst_name = f'{basechar}DT'

    def tzname(self, dt: datetime, *, is_utc: bool = None,
               dst_known: bool = False):
        return (self.dst_name
                if self.is_dt_dst(dt, is_utc=is_utc, dst_known=dst_known)
                else self.std_name)

    def utcoffset(self, dt: datetime, *, is_utc: bool = None,
                  dst_known: bool = False):
        return self.std_offset + self.dst(dt, is_utc=is_utc,
                                          dst_known=dst_known)

    def dst(self, dt: datetime, *, is_utc: bool = None,
            dst_known: bool = False):
        return (HOUR if self.is_dt_dst(dt, is_utc=is_utc, dst_known=dst_known)
                else ZERO)

    def is_dt_dst(self, dt: datetime, *, is_utc: bool = None,
                  dst_known: bool = False):
        """
        dst_known should be set to True if we know that dt.fold is
        correctly set
        """
        naive_dt = dt.replace(tzinfo=None)

        if is_utc is None:
            tzi = dt.tzinfo
            if tzi:
                if isinstance(tzi, self.__class__):
                    is_utc = False

                else:
                    offset = tzi.utcoffset(dt).total_seconds()
                    is_utc = offset == 0

            else:
                # assume local time:
                is_utc = False

        dst_start_utc, dst_end_utc = self.get_utc_dst_start_end(dt.year)
        if not is_utc:
            # try to convert to utc, assuming std time
            naive_dt -= self.std_offset
            # fold is 1 if we are in std time and know it, so only check if
            # fold is 0 or not set
            if not dt.fold:
                dst_end_ambig_utc = dst_end_utc + HOUR
                in_ambig = (naive_dt >= dst_end_utc
                            and naive_dt < dst_end_ambig_utc)
                if in_ambig:
                    if dst_known:
                        naive_dt -= HOUR

                    else:
                        raise AmbiguousDstError

        # naive_dt is now utc
        return naive_dt >= dst_start_utc and naive_dt < dst_end_utc

    def get_utc_dst_start_end(self, year: int):
        dst_start_base = datetime(year, 3, 8, 2)
        dst_end_base = datetime(year, 11, 1, 1)

        # isoweekday: 1 = mon, 7 = sat
        dst_start_delta = timedelta(days=7 - dst_start_base.isoweekday())
        dst_end_delta = timedelta(days=7 - dst_end_base.isoweekday())

        dst_start_std = dst_start_base + dst_start_delta
        dst_end_std = dst_end_base + dst_end_delta

        baseoffset = self.std_offset
        dst_start_utc = dst_start_std - baseoffset
        dst_end_utc = dst_end_std - baseoffset

        return dst_start_utc, dst_end_utc

    def fromutc(self, dt: datetime):
        naive_dt = dt.replace(tzinfo=None)
        new_dt = dt + self.utcoffset(dt, is_utc=True)
        _, dst_end_utc = self.get_utc_dst_start_end(dt.year)
        if naive_dt >= dst_end_utc and naive_dt < (dst_end_utc + HOUR):
            new_dt = new_dt.replace(fold=1)

        return new_dt


TZEAS = USTimeZone('Eastern', 5)
TZCEN = USTimeZone('Central', 6)
TZMTN = USTimeZone('Mountain', 7)
TZPAC = USTimeZone('Pacific', 8)
TZUTC = timezone.utc
