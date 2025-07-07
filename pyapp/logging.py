import sys as _sys

from typing import (
    TypeVar as _TypeVar, cast as _cast, overload as _overload, Any as _Any
)
from types import TracebackType as _TracebackType
from collections.abc import Callable as _Callable
from functools import wraps as _wraps
# want to export these for convenience, so they are not hidden by default
from logging import (  # noqa: F401
    getLogger as _getLogger, WARN, ERROR, DEBUG, INFO, CRITICAL, WARNING,
    Logger,
)
from traceback import format_exception_only

from ._testing.debug import is_debug_enabled
from .utils.stack import (
    exc_info as _exc_info, find_caller as _find_caller,
    format_exc as _format_exc, get_stack_frame as _get_stack_frame
)


Logger.root.setLevel(0)

# from .utils.logging import DEBUGLOW, LOGSTDOUT, LOGSTDERR, LOGTQDM  # noqa: F401, E501
LOGSTDOUT = INFO + 1
LOGSTDERR = INFO + 2
LOGTQDM = INFO + 3
DEBUGLOW = DEBUG - 1
DEBUGLOW2 = DEBUG - 2

APP_LOG_LEVEL_NAMES = {
    'STDOUT': LOGSTDOUT,
    'STDERR': LOGSTDERR,
    'TQDM': LOGTQDM,
    'DEBUGLOW': DEBUGLOW,
    'DEBUGLOW2': DEBUGLOW2,
}

TRACELOG: bool = False


def get_logger(modname: str = None) -> Logger:
    __traceback_hide__ = True  # noqa: F841
    modname = modname or _get_stack_frame(2).f_globals['__name__']

    log = None
    # if _AppConfig:
    #     log = _AppConfig.log
    return log or _getLogger(modname)


F = _TypeVar("F", bound=_Callable[..., _Any])
@_overload
def log_func_call(func: F) -> F: ...
@_overload  # noqa: E302
def log_func_call(level: int | str, *,
                  trace_only: bool = False) -> _Callable[[F], F]: ...
def log_func_call(arg, *, trace_only: bool = False):  # noqa: E302
    def log_decorator(func: F) -> F:
        @_wraps(func)
        def log_func_call_wrapper(*args, **kwargs):
            __traceback_hide__ = True  # noqa: F841
            if not trace_only or get_tracelog():
                log = get_logger(func.__module__)
                try:
                    code = func.__code__
                    funcname = func.__name__
                    _log(
                        log,
                        level,
                        f"Function call: {func.__qualname__}"
                        f"({', '.join(
                            'self' if not i and funcname == '__init__'
                            else
                            repr(arg) for i, arg in enumerate(args)
                        )}{', ' if args and kwargs else ''}"
                        f"{', '.join(f'{k}={v!r}'
                                     for k, v in kwargs.items())}) "
                        f"{{function defined {code.co_filename}"
                        f"({code.co_firstlineno})}}",
                        # stacklevel=2,
                    )
                except BaseException as e:
                    _log(
                        log,
                        level,
                        "Error logging function call: "
                        f"{func.__qualname__} - "
                        f"{''.join(format_exception_only(e)).strip()} "
                        f"{{function defined {code.co_filename}"
                        f"({code.co_firstlineno})}}",
                        # stacklevel=2,
                    )
            return func(*args, **kwargs)
        return _cast(F, log_func_call_wrapper)

    if callable(arg):
        # Used as @log_func_call
        level = DEBUGLOW
        return log_decorator(arg)
    else:
        # Used as @log_func_call(level)
        level = arg
        return log_decorator


def set_trace_logging(enabled: bool = True):
    global TRACELOG
    TRACELOG = bool(enabled)


def get_tracelog() -> bool:
    global TRACELOG
    return TRACELOG


def log_exc(exc_or_type: type | BaseException = None,
            exc: BaseException = None,
            traceback: _TracebackType = None):
    __traceback_hide__ = True  # noqa: F841
    _log(get_logger(), ERROR, 'Unhandled exception', stacklevel=2,
         exc_info=_exc_info(exc_or_type, exc, traceback))


def _log_exc_hook(exc_or_type: type | BaseException = None,
                  exc: BaseException = None,
                  traceback: _TracebackType = None):
    if not is_debug_enabled():
        log_exc(exc_or_type, exc, traceback)


_sys.excepthook = _log_exc_hook
# _sys.excepthook = (lambda: None) if is_debug_enabled() else log_exc


def _log(log: Logger, level, msg, *args, exc_info=None, extra=None,
         stack_info=False, stacklevel=1):
    __traceback_hide__ = True  # noqa: F841
    fn, lno, func, sinfo = _find_caller(stack_info, stacklevel)
    record = log.makeRecord(log.name, level, fn, lno, msg, args, exc_info,
                            func, extra, sinfo)
    if exc_info:
        record.exc_text = _format_exc(exc_info[1], exc_info[2])
    log.handle(record)
