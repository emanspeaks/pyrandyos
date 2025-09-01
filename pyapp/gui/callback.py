from collections.abc import Callable

from ..logging import log_func_call


class QtCallable:
    def __init__(self, func: Callable):
        self.func = func

    def __call__(self, *args, **kwargs):
        __traceback_hide__ = True  # noqa: F841
        return log_func_call(self.func)(*args, **kwargs)


def qt_callback(f: Callable):
    return QtCallable(f)
