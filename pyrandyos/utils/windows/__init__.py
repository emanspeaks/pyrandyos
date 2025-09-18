from .ctypes import IS_WIN_CTYPES  # noqa: F401
from ..constants import IS_WIN32

if IS_WIN32:
    from os import system as syscall
    syscall('color')  # allows color console outputs
