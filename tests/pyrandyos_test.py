from unittest import TestCase, main as utmain, TextTestRunner, mock
import sys
from os import environ
from pathlib import Path
from datetime import datetime, timedelta

HERE = Path(__file__).expanduser().resolve().parent
REPOROOT = HERE.parent
if __name__ == '__main__':
    sys.path.append(str(REPOROOT))

    # so we can get testing constants without importing pyrandyos
    sys.path.insert(0, str(REPOROOT/'pyrandyos/_testing'))

from _pyrandyos_testing import (  # noqa: E402
    ENV_PYRANDYOS_UNITTEST_ACTIVE,
)

ZERO = timedelta()
HOUR = timedelta(hours=1)


@mock.patch.dict(environ, {ENV_PYRANDYOS_UNITTEST_ACTIVE: '1'})
class TestPyRandyOS(TestCase):
    def test_import(self):
        import pyrandyos  # noqa: F401

    def single_tz_test(self, local_naive: datetime,
                       expected_utcoffset_hr: int, expect_error: bool = False,
                       fold: int = 0):
        from pyrandyos.utils.time.timezone import (
            TZCEN, TZUTC, AmbiguousDstError
        )
        local_aware = local_naive.replace(tzinfo=TZCEN, fold=fold)
        try:
            local_aware_offset = local_aware.utcoffset()
        except AmbiguousDstError:
            if expect_error:
                local_aware_offset = TZCEN.utcoffset(local_aware,
                                                     dst_known=True)

            else:
                self.fail("Unexpected AmbiguousDstError")

        finally:
            self.assertEqual(local_aware_offset.total_seconds()/3600,
                             expected_utcoffset_hr)

        utc_naive = local_naive - timedelta(hours=expected_utcoffset_hr)
        utc_aware = utc_naive.replace(tzinfo=TZUTC)
        local_fromutc = utc_aware.astimezone(TZCEN)
        self.assertEqual(local_aware, local_fromutc)
        self.assertEqual(local_fromutc.fold, fold)

    def test_dst(self):
        cen_pre_dst_start = datetime(2025, 3, 9, 1)
        cen_dst_start = datetime(2025, 3, 9, 3)
        cen_dst_post_start = datetime(2025, 3, 9, 4)
        cen_pre_dst_end = datetime(2025, 11, 2, 0)
        cen_dst_end_ambig = datetime(2025, 11, 2, 1)
        cen_dst_end_midambig = datetime(2025, 11, 2, 1, 59)
        cen_dst_end = datetime(2025, 11, 2, 2)
        cen_dst_post_end = datetime(2025, 11, 2, 3)

        self.single_tz_test(cen_pre_dst_start, -6)
        self.single_tz_test(cen_dst_start, -5)
        self.single_tz_test(cen_dst_post_start, -5)
        self.single_tz_test(cen_pre_dst_end, -5)
        self.single_tz_test(cen_dst_end_ambig, -5, True)
        self.single_tz_test(cen_dst_end_midambig, -5, True)
        self.single_tz_test(cen_dst_end_ambig, -6, fold=1)
        self.single_tz_test(cen_dst_end_midambig, -6, fold=1)
        self.single_tz_test(cen_dst_end, -6)
        self.single_tz_test(cen_dst_post_end, -6)


if __name__ == '__main__':
    ttr = TextTestRunner(stream=sys.stdout,
                         verbosity=9,
                         failfast=True)
    try:
        utmain(testRunner=ttr)
    except SystemExit:
        pass
