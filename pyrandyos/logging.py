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
    Logger, getLevelName as _getLevelName, LogRecord as _LogRecord,
)
try:
    from logging import getLevelNamesMapping as _getLevelNamesMapping
except ImportError:
    # not available until Python 3.12
    _getLevelNamesMapping = None

from .utils.signature_wrapper import (
    generate_signature_aware_wrapper as _sig_aware_wrapper
)
from ._testing.debug import is_debug_enabled
from .utils.stack import (
    exc_info as _exc_info, log_find_caller as _find_caller,
    format_exc as _format_exc, get_stack_frame as _get_stack_frame,
    ExcInfoType as _ExcInfoType,
    is_code_the_given_func as _is_code_the_given_func,
    get_show_traceback_locals,
)

_RecFactoryType = _Callable[..., _LogRecord]


Logger.root.setLevel(0)

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
_GLOBAL_LOG: Logger = None


def get_global_logger():
    return _GLOBAL_LOG


def set_global_logger(log: Logger):
    global _GLOBAL_LOG
    _GLOBAL_LOG = log


def get_logger(modname: str = None, stacklevel: int = 2) -> Logger:
    __traceback_hide__ = True  # noqa: F841
    log = _GLOBAL_LOG
    if log:
        return log
    # default stack level here is 2 because we want to pop off both
    # get_stack_frame and get_logger.
    if not modname:
        f = _get_stack_frame(stacklevel)
        if f:
            modname = f.f_globals['__name__']

        else:
            # if we exhausted the whole stack, it's probably because the issue
            # is in the main script, so let's just assume it's '__main__'
            modname = '__main__'

    return _getLogger(modname)


def log_message(level: int | str, msg: str, *args,
                exc_info: _ExcInfoType | BaseException = None,
                extra: _Mapping[str, object] = None, stack_info: bool = False,
                stacklevel: int = 1):
    # the default stacklevel is 1 because we assume we don't want to include
    # the call to log_message, which would be first on the stack after removing
    # all the internals already.
    #
    # the stacklevel for get_logger, however, is an ABSOLUTE stack level
    # since the value is passed directly to get_stack_frame.  Therefore,
    # the value we pass here needs to account for:
    # 1. get_stack_frame
    # 2. get_logger
    # 3. log_message
    # This is why the offset is two because we assume stacklevel is starting to
    # count up the stack including log_message, so we only need the extra
    # levels for get_logger and get_stack_frame.
    #
    # Finally, the stacklevel for _log itself only adds one level because the
    # stacklevel there is used to pop elements off the end of the stack list
    # from filter_stack.  With a stacklevel of 1, it should return the first
    # non-hidden function it finds (because it's actually a -1).  However,
    # THIS function is NOT hidden with __traceback_hide__, and therefore this
    # is the function it would return.  Since we assume we actually want the
    # caller of THIS function, we need to pop one additional level.
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
    stacklevel: int = handler_kwargs.get('stacklevel', 1)
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
                stacklevel=stacklevel,
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
                stacklevel=stacklevel,
            )

    return func_args, func_kwargs


F = _TypeVar("F", bound=_Callable[..., _Any])
@_overload
def log_func_call(func: F) -> F: ...
@_overload  # noqa: E302
def log_func_call(level: int | str, *,
                  trace_only: bool = False,
                  stacklevel: int = 1) -> _Callable[[F], F]: ...
def log_func_call(arg, *,  # noqa: E302
                  trace_only: bool = False,
                  stacklevel: int = 1):
    if _environ.get("PYRANDYOS_BYPASS_CALL_LOG"):
        return arg if callable(arg) else lambda f: f

    def log_decorator(func: F) -> F:
        return _sig_aware_wrapper(func, _log_func_call_handler, level,
                                  trace_only=trace_only, stacklevel=stacklevel)

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
            mark_handled: bool = True,
            stacklevel: int = 1):
    __traceback_hide__ = True  # noqa: F841
    # see comments on stacklevel in log_message.  Note that this function IS
    # hidden, so no offset is applied for the arg to _log.
    excnfo = _exc_info(exc_or_type, exc, traceback)
    _log(get_logger(stacklevel=stacklevel + 2), ERROR, msg, exc_info=excnfo,
         stacklevel=stacklevel)
    if mark_handled:
        excnfo[1]._pyrandyos_handled = True


def _log_exc_hook(exc_or_type: type | BaseException = None,
                  exc: BaseException = None,
                  traceback: _TracebackType = None):
    if get_show_traceback_locals() is None:
        _sys.__excepthook__(exc_or_type, exc, traceback)

    f = _get_stack_frame(2)  # excludes _log_exc_hook and get_stack_frame
    # if we are in debug, usually we want to have the debugger handle
    # exceptions so that we can break on them.  If we log the exception with
    # log_exc AND pass to the sys.__excepthook__, it would log the exception
    # twice (at least to the console, perhaps not the log file).  This is why
    # we only enable log_exc here when we are NOT debugging, because otherwise
    # the sys.__excepthook__ would not record the error in the log and would
    # die instantly.  We have multiple mechanisms already in PyRandyOS to try
    # to catch and log exceptions, but if one is showing up here, it somehow
    # got through the cracks since this is the handler of last resort.
    #
    # It seems that the way you can end up here is if exceptions are raised
    # from outside the Python interpreter, like during a callback invoked from
    # a foreign function via ctypes or Qt for example.  QtApp.notify is the
    # event handler for the GUI event loop, so we can check for that as the
    # source of the exception that might otherwise not get caught by the usual
    # Python mechanisms.  However, it is not the only one even with Qt.
    # The signals/slots paradigm for other non-event based callbacks are
    # instead invoked directly and thus do not pass through QtApp.notify.
    # This means there is otherwise not a reliable way to detect those since
    # the Qt caller will be invisible in the Python call stack for all intents
    # and purposes.  We have to rely on the user to decorate slots so that we
    # can know definitively they are being called externally and thus worthy
    # of trapping here even in a debug scenario.
    tbf = traceback.tb_frame
    code = tbf.f_code
    from .gui.callback import QtCallable
    is_qt_callback = _is_code_the_given_func(QtCallable.__call__, code)

    debug = is_debug_enabled()
    is_qt_notify = False
    if debug and f:
        code = f.f_code
        from .gui.gui_app import QtApp
        is_qt_notify = _is_code_the_given_func(QtApp.notify, code)

    if (not debug or not f or is_qt_notify or is_qt_callback):
        # stacklevel here needs to pop an additional level from the default 1
        # for the absolute stacklevel of _log_exc_hook itself for get_logger.
        # The secondary use of stacklevel otherwise would be for getting the
        # right output from filter_stack, but that is only called when not
        # given exc_info.  since we are passing exc_info, we only need to
        # cover the get_logger use case.
        log_exc(exc_or_type, exc, traceback, stacklevel=2)

    if not getattr(exc, '_pyrandyos_handled', False):
        # if we did not handle it, let the default handler do its job
        _sys.__excepthook__(exc_or_type, exc, traceback)


_sys.excepthook = _log_exc_hook
# _sys.excepthook = (lambda: None) if is_debug_enabled() else log_exc


def _default_rec_factory(name: str, level: int, fn: str, lno: int, msg,
                         args: tuple, exc_info: _ExcInfoType, func: str = None,
                         extra: dict = None, sinfo: str = None):
    __traceback_hide__ = True  # noqa: F841
    # adapted from Logger.makeRecord
    rv = _LogRecord(name, level, fn, lno, msg, args, exc_info, func, sinfo)
    if extra is not None:
        for key in extra:
            if (key in ["message", "asctime"]) or (key in rv.__dict__):
                raise KeyError("Attempt to overwrite %r in LogRecord" % key)
            rv.__dict__[key] = extra[key]
    return rv


def make_log_record(level: int | str, msg: str, *args,
                    exc_info: _ExcInfoType | BaseException = None,
                    extra: _Mapping[str, object] = None,
                    stack_info: bool = False, stacklevel: int = 1,
                    logname: str | None = None,
                    recfactory: _RecFactoryType = _default_rec_factory):
    __traceback_hide__ = True  # noqa: F841
    if not isinstance(level, int):
        level, _ = get_loglevel_num_name(level)

    if logname is None:
        # this stacklevel does NOT exclude __traceback_hide__ functions
        # so we must adjust for it.  If we are calling this function
        # (make_log_record) directly, we assume the default stacklevel 1
        # accounts for this frame, the +2 is the same as in log_message,
        # and then we end up at the caller of make_log_record, which is the
        # desired outcome in this case.
        logname = get_logger(stacklevel=stacklevel + 2).name

    exc_info = _exc_info(exc_info, skip_if_none=True)
    # no need to adjust stacklevel because it excludes __traceback_hide__
    # functions in the stack automatically here, including this one, so it
    # should return the caller of this function (or any non-hidden predecessor)
    fn, lno, func, sinfo = _find_caller(stack_info, stacklevel, exc_info)
    record = recfactory(logname, level, fn, lno, msg, args, exc_info,
                        func, extra, sinfo)
    if exc_info:
        record.exc_text = _format_exc(exc_info[1], exc_info[2])

    return record


def _log(log: Logger, level: int | str, msg: str, *args,
         exc_info: _ExcInfoType | BaseException = None,
         extra: _Mapping[str, object] = None,
         stack_info: bool = False, stacklevel: int = 1):
    __traceback_hide__ = True  # noqa: F841
    # no need to adjust stacklevel because it excludes __traceback_hide__
    # functions in the stack automatically
    log.handle(make_log_record(level, msg, *args,
                               exc_info=exc_info, extra=extra,
                               stack_info=stack_info,
                               stacklevel=stacklevel,
                               logname=log.name,
                               recfactory=log.makeRecord))


# @log_func_call(DEBUGLOW2)
def log_level_by_name(name: str):
    if _getLevelNamesMapping:
        return _getLevelNamesMapping().get(name)
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
