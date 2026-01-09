"""
This module is intended for internal use only.  No user documentation is
provided at this time.  Use at your own discretion.
"""

# code adapted from https://github.com/Drekin/win-unicode-console/
from logging import Logger
from pathlib import Path
from ctypes import c_ulong, byref, create_string_buffer, cast

from ...logging import log_func_call
from ..string import ensure_bytes
from ..constants import IS_WIN32
from ..constants.windows import (
    ErrCodeLookup, DllErrMsgDict, DriveList, ERROR_INVALID_HANDLE,
    PROCESS_SYSTEM_DPI_AWARE, MAX_PREFERRED_LENGTH, WIN_WCHAR_ENCODING
)
from .ctypes import IS_WIN_CTYPES

if IS_WIN_CTYPES:
    from .ctypes import (
        WriteConsoleW, GetConsoleMode, get_last_error, WNetOpenEnum,
        WNetCloseEnum, WNetEnumResource, WinError, SetProcessDpiAwareness,
        RESOURCETYPE_DISK, RESOURCE_CONNECTED, LPCWSTR,
        SetCurrentProcessExplicitAppUserModelID,
    )


@log_func_call
def build_error_message(codelookup: ErrCodeLookup, dllerrs: DllErrMsgDict,
                        func: str, code: int,):
    errname = codelookup.get(code)
    funcerrs = dllerrs.get(func)
    errmsg = funcerrs.get(errname) if funcerrs else None

    msg = f'{func} error: {errname or "[Unknown]"}({hex(code)})'
    if errmsg:
        msg += f': {errmsg}'

    return msg


@log_func_call
def win_write(handle: int, data: bytes):
    bytes_to_be_written = len(data)
    buffer = create_string_buffer(data)
    code_units_to_be_written = bytes_to_be_written//2
    code_units_written = c_ulong()

    if not WriteConsoleW(handle, buffer, code_units_to_be_written,
                         byref(code_units_written), None):
        exc = WinError(get_last_error())
        raise exc  # use traceback from here

    return 2 * code_units_written.value  # bytes written


@log_func_call
def is_win_console(handle: int):
    mode = c_ulong()
    retval = GetConsoleMode(handle, byref(mode))
    return bool(retval) or get_last_error() != ERROR_INVALID_HANDLE


@log_func_call
def set_high_dpi_support(value: int = PROCESS_SYSTEM_DPI_AWARE,
                         log: Logger = None):
    if IS_WIN_CTYPES:
        if log:
            log.debug(f'setting process to DPI aware ({value})')

        SetProcessDpiAwareness(value)


@log_func_call
def get_mapped_drives():
    """
    Gets all currently mapped drives in Windows.

    Returns:
        DriveList: list of tuples of mapped drives.
            The two Paths in the tuple are (local, remote), where the local
            is a drive letter and remote is the UNC of the network share.
    """
    if not IS_WIN32:
        return list()
    handle = WNetOpenEnum(RESOURCE_CONNECTED, RESOURCETYPE_DISK, 0, None)
    drives: DriveList = list()
    try:
        items = True
        while items:
            items = WNetEnumResource(handle, MAX_PREFERRED_LENGTH)
            drives += [(Path(f'{it.lpLocalName}/'), Path(it.lpRemoteName))
                       for it in items]
            # for it in items:
            #     print(it.dwScope)
            #     print(it.dwType)
            #     print(it.dwDisplayType)
            #     print(RESOURCEDISPLAYTYPES[it.dwDisplayType])
            #     print(it.dwUsage)
            #     print(it.lpLocalName)
            #     print(it.lpRemoteName)
            #     print(it.lpComment)
            #     print(it.lpProvider)

        return drives
    finally:
        WNetCloseEnum(handle)


@log_func_call
def set_windows_process_app_id(appid: str):
    if IS_WIN32:
        buffer = create_string_buffer(ensure_bytes(appid, WIN_WCHAR_ENCODING))
        SetCurrentProcessExplicitAppUserModelID(cast(byref(buffer), LPCWSTR))
