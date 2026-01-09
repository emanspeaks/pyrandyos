"""
This module is intended for internal use only.  No user documentation is
provided at this time.  Use at your own discretion.
"""
from ctypes import c_uint

try:  # pragma: no cover
    from ctypes import WinDLL, WinError, get_last_error, OleDLL  # noqa: F401
    from ctypes.wintypes import (
        DWORD, HANDLE, LPDWORD, LPVOID, LPCWSTR,
        # LPCWSTR, ULONG, PHANDLE, PULONG,
    )
    from win32wnet import WNetOpenEnum, WNetCloseEnum, WNetEnumResource  # noqa: F401, E501
    from win32netcon import (  # noqa: F401
        RESOURCETYPE_DISK, RESOURCE_CONNECTED, RESOURCEDISPLAYTYPE_NETWORK,
        RESOURCEDISPLAYTYPE_DOMAIN, RESOURCEDISPLAYTYPE_SERVER,
        RESOURCEDISPLAYTYPE_SHARE, RESOURCEDISPLAYTYPE_DIRECTORY,
        RESOURCEDISPLAYTYPE_GENERIC,
    )
except ImportError:  # pragma: no cover
    IS_WIN_CTYPES = False
else:  # pragma: no cover
    IS_WIN_CTYPES = True

    kernel32 = WinDLL("kernel32", use_last_error=True)
    WriteConsoleW = kernel32.WriteConsoleW
    WriteConsoleW.argtypes = (HANDLE, LPVOID, DWORD, LPDWORD, LPVOID)
    GetConsoleMode = kernel32.GetConsoleMode
    GetConsoleMode.argtypes = (HANDLE, LPDWORD)

    shcore = OleDLL('shcore', use_last_error=True)
    SetProcessDpiAwareness = shcore.SetProcessDpiAwareness
    SetProcessDpiAwareness.argtypes = (c_uint,)

    shell32 = WinDLL("shell32", use_last_error=True)
    SetCurrentProcessExplicitAppUserModelID = shell32.SetCurrentProcessExplicitAppUserModelID  # noqa: E501
    SetCurrentProcessExplicitAppUserModelID.argtypes = (LPCWSTR,)

    RESOURCEDISPLAYTYPES = {
        # The resource is a network provider.
        RESOURCEDISPLAYTYPE_NETWORK: 'RESOURCEDISPLAYTYPE_NETWORK',
        # The resource is a collection of servers.
        RESOURCEDISPLAYTYPE_DOMAIN: 'RESOURCEDISPLAYTYPE_DOMAIN',
        # The resource is a server.
        RESOURCEDISPLAYTYPE_SERVER: 'RESOURCEDISPLAYTYPE_SERVER',
        # The resource is a share point.
        RESOURCEDISPLAYTYPE_SHARE: 'RESOURCEDISPLAYTYPE_SHARE',
        # The resource is a directory.
        RESOURCEDISPLAYTYPE_DIRECTORY: 'RESOURCEDISPLAYTYPE_DIRECTORY',
        # The resource type is unspecified.
        # This value is used by network providers that do not specify
        # resource types.
        RESOURCEDISPLAYTYPE_GENERIC: 'RESOURCEDISPLAYTYPE_GENERIC',
    }
