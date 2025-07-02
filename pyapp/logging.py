from typing import TypeVar, cast, overload, Any
from collections.abc import Callable
from logging import (  # noqa: F401
    getLogger as _getLogger, WARN, ERROR, DEBUG, INFO, CRITICAL, WARNING,
    Logger
)
from inspect import stack as _stack
from functools import wraps

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


def get_logger(modname: str = None) -> Logger:
    # try:
    #     from .config import AppConfig as _AppConfig
    # except ImportError:
    #     _AppConfig = None

    if not modname:
        modname = _stack()[1].frame.f_globals['__name__']

    log = None
    # if _AppConfig:
    #     log = _AppConfig.log
    return log or _getLogger(modname)


F = TypeVar("F", bound=Callable[..., Any])
@overload
def log_func_call(func: F) -> F: ...
@overload
def log_func_call(level: int | str) -> Callable[[F], F]: ...


def log_func_call(arg):
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            log = get_logger(func.__module__)
            log.log(
                level,
                f"Function call: {func.__qualname__}"
                f"({', '.join(repr(arg) for arg in args)}"
                f"{', ' if args and kwargs else ''}"
                f"{', '.join(f'{k}={v!r}' for k, v in kwargs.items())})",
                stacklevel=2,
            )
            return func(*args, **kwargs)
        return cast(F, wrapper)

    if callable(arg):
        # Used as @log_func_call
        level = DEBUGLOW
        return decorator(arg)
    else:
        # Used as @log_func_call(level)
        level = arg
        return decorator
