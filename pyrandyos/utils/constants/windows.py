"""
This module is intended for internal use only.  No user documentation is
provided at this time.  Use at your own discretion.
"""

from pathlib import Path
from ctypes import POINTER, c_ssize_t, c_ulonglong, c_ubyte

ErrCodeLookup = dict[int, str]
FuncErrMsgDict = dict[str, str]
DllErrMsgDict = dict[str, FuncErrMsgDict]
DriveList = list[tuple[Path, Path]]

c_ssize_p = POINTER(c_ssize_t)
UCHAR = c_ubyte
PUCHAR = POINTER(UCHAR)
PUCHARType = type[PUCHAR]
ULONGLONG = c_ulonglong

MAX_PREFERRED_LENGTH = -1

ERROR_INVALID_HANDLE = 6

PROCESS_DPI_UNAWARE = 0
PROCESS_SYSTEM_DPI_AWARE = 1
PROCESS_PER_MONITOR_DPI_AWARE = 2

WIN_WCHAR_ENCODING = 'utf-16-le'
"""
Win API only has UTF-16-LE support because they were early adopters before
the rest of the internet converged on utf-8.  Calls to Win API funcs need to
encode as utf-16-le.  Use this constant when doing low-level codec operations.
"""

# https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-erref/596a1078-e883-4972-9bbc-49e60bebca55  # noqa: E501
NTSTATUS_CODES = {
    0x00000000: 'STATUS_SUCCESS',
    0xC0000225: 'STATUS_NOT_FOUND',
    0xC000000D: 'STATUS_INVALID_PARAMETER',
    0xC0000017: 'STATUS_NO_MEMORY',
    0xC0000008: 'STATUS_INVALID_HANDLE',
    0xC00000BB: 'STATUS_NOT_SUPPORTED',
    0xC0000023: 'STATUS_BUFFER_TOO_SMALL',
    0xC000A002: 'STATUS_AUTH_TAG_MISMATCH',
    0xC0000206: 'STATUS_INVALID_BUFFER_SIZE',
}
