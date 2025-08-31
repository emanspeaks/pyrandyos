import sys as _sys
from os import environ as _environ

from typing import (
    TypeVar as _TypeVar, overload as _overload, Any as _Any
)
from types import TracebackType as _TracebackType
from collections.abc import Callable as _Callable, Mapping as _Mapping
from traceback import format_exception_only
from functools import partial as _partial
# want to export these for convenience, so they are not hidden by default
from logging import (  # noqa: F401
    getLogger as _getLogger, WARN, ERROR, DEBUG, INFO, CRITICAL, WARNING,
    Logger, getLevelName as _getLevelName
)
try:
    from logging import getLevelNameMapping as _getLevelNameMapping
except ImportError:
    # not available until Python 3.12...allegedly
    _getLevelNameMapping = None

from .utils.signature_wrapper import (
    generate_signature_aware_wrapper as _sig_aware_wrapper
)
from ._testing.debug import is_debug_enabled
from .utils.stack import (
    exc_info as _exc_info, log_find_caller as _find_caller,
    format_exc as _format_exc, get_stack_frame as _get_stack_frame,
    ExcInfoType as _ExcInfoType,
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
FUNCCALLLOG: bool = False


def get_logger(modname: str = None, stacklevel: int = 2) -> Logger:
    __traceback_hide__ = True  # noqa: F841
    modname = modname or _get_stack_frame(stacklevel).f_globals['__name__']

    log = None
    # if _AppConfig:
    #     log = _AppConfig.log
    return log or _getLogger(modname)


def log_message(level: int | str, msg: str, *args,
                exc_info: _ExcInfoType | BaseException = None,
                extra: _Mapping[str, object] = None, stack_info: bool = False,
                stacklevel: int = 1):
    _log(get_logger(stacklevel=stacklevel + 2), level, msg, *args,
         exc_info=exc_info, extra=extra, stack_info=stack_info,
         stacklevel=stacklevel + 1)


log_debuglow2 = _partial(log_message, DEBUGLOW2)
log_debuglow = _partial(log_message, DEBUGLOW)
log_debug = _partial(log_message, DEBUG)
log_info = _partial(log_message, INFO)
log_warning = _partial(log_message, WARNING)
log_error = _partial(log_message, ERROR)
log_critical = _partial(log_message, CRITICAL)


def _log_func_call_handler(handler_args: tuple, handler_kwargs: dict,
                           func: _Callable, *func_args: tuple,
                           **func_kwargs: dict):
    __traceback_hide__ = True  # noqa: F841
    level: str | int = handler_args[0]
    trace_only: bool = handler_kwargs.get('trace_only', False)
    if get_func_call_logging() and (not trace_only or get_tracelog()):
        log = get_logger(func.__module__)
        try:
            code = func.__code__
            funcname = func.__name__
            funcargstr = ', '.join(
                'self' if not i and funcname == '__init__'
                else repr(arg) for i, arg in enumerate(func_args)
            )
            funcargstr += ', ' if func_args and func_kwargs else ''
            funcargstr += ', '.join(f'{k}={v!r}'
                                    for k, v in func_kwargs.items())
            _log(
                log,
                level,
                f"{'TRACE: ' if trace_only else ''}"
                f"Function call: {func.__qualname__}"
                f"({funcargstr}) "
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

    return func_args, func_kwargs


F = _TypeVar("F", bound=_Callable[..., _Any])
@_overload
def log_func_call(func: F) -> F: ...
@_overload  # noqa: E302
def log_func_call(level: int | str, *,
                  trace_only: bool = False) -> _Callable[[F], F]: ...
def log_func_call(arg, *, trace_only: bool = False):  # noqa: E302
    if _environ.get("PYAPP_BYPASS_CALL_LOG"):
        return arg if callable(arg) else lambda f: f

    def log_decorator(func: F) -> F:
        return _sig_aware_wrapper(func, _log_func_call_handler, level,
                                  trace_only=trace_only)

    if callable(arg):
        # Used as @log_func_call
        level = DEBUGLOW
        return log_decorator(arg)
    else:
        # Used as @log_func_call(level)
        level = arg
        return log_decorator


def set_func_call_logging(enabled: bool = True):
    global FUNCCALLLOG
    FUNCCALLLOG = bool(enabled)


def get_func_call_logging() -> bool:
    global FUNCCALLLOG
    return FUNCCALLLOG


def set_trace_logging(enabled: bool = True):
    global TRACELOG
    TRACELOG = bool(enabled)


def get_tracelog() -> bool:
    global TRACELOG
    return TRACELOG


def log_exc(exc_or_type: type | BaseException = None,
            exc: BaseException = None,
            traceback: _TracebackType = None,
            msg: str = 'Unhandled exception',
            mark_handled: bool = True):
    __traceback_hide__ = True  # noqa: F841
    excnfo = _exc_info(exc_or_type, exc, traceback)
    _log(get_logger(), ERROR, msg, exc_info=excnfo)
    if mark_handled:
        excnfo[1]._pyapp_handled = True


def _log_exc_hook(exc_or_type: type | BaseException = None,
                  exc: BaseException = None,
                  traceback: _TracebackType = None):
    f = _get_stack_frame(2)
    if (not is_debug_enabled() or not f
            or f.f_code.co_qualname == 'QtApp.notify'):
        log_exc(exc_or_type, exc, traceback)

    if not getattr(exc, '_pyapp_handled', False):
        # if we did not handle it, let the default handler do its job
        _sys.__excepthook__(exc_or_type, exc, traceback)


_sys.excepthook = _log_exc_hook
# _sys.excepthook = (lambda: None) if is_debug_enabled() else log_exc


def _log(log: Logger, level: int | str, msg: str, *args,
         exc_info: _ExcInfoType | BaseException = None,
         extra: _Mapping[str, object] = None,
         stack_info: bool = False, stacklevel: int = 1):
    __traceback_hide__ = True  # noqa: F841
    if not isinstance(level, int):
        level, _ = get_loglevel_num_name(level)

    exc_info = _exc_info(exc_info, skip_if_none=True)
    fn, lno, func, sinfo = _find_caller(stack_info, stacklevel, exc_info)
    record = log.makeRecord(log.name, level, fn, lno, msg, args, exc_info,
                            func, extra, sinfo)
    if exc_info:
        record.exc_text = _format_exc(exc_info[1], exc_info[2])
    log.handle(record)


# @log_func_call(DEBUGLOW2)
def log_level_by_name(name: str):
    if _getLevelNameMapping:
        return _getLevelNameMapping().get(name)
    # NOTE: the logic in here is apparently a bug and deprecated, but isn't
    # fixed until Python 3.12.  Supporting both so I don't have to change
    # this code later once we upgrade Python versions.
    num = _getLevelName(name)
    if isinstance(num, str):
        return
    return num


# @log_func_call(DEBUGLOW2)
def get_loglevel_num_name(level: str | int):
    "returns num, name"
    if isinstance(level, str):
        level = level.upper()
        num = log_level_by_name(level)
        if num is None:
            raise ValueError(f'unknown loglevel string {level} given')
        return num, level
    name = _getLevelName(level)
    num = log_level_by_name(name)
    if not isinstance(num, int):
        name = None

    return level, name
