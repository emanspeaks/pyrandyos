from collections.abc import Callable

from ..logging import log_func_call
from ..utils.stack import get_stack_frame, get_framesummary_for_frame


class QtCallable:
    def __init__(self, func: Callable, stacklevel: int = 1):
        self.func = func
        # stacklevel arg should account for this function at a minimum, hence 1
        # but then we need to add 1 for get_stack_frame.  This should end up
        # returning the frame that called the QtCallable ctor
        fs = get_framesummary_for_frame(get_stack_frame(stacklevel + 1))
        self.caller = fs
        self.caller_line = fs.line

    def __call__(self, *args, **kwargs):
        caller = self.caller  # noqa: F841
        caller_line = self.caller_line  # noqa: F841
        return log_func_call(self.func)(*args, **kwargs)


def qt_callback(f: Callable):
    # increment the stacklevel from default by 1 to account for this frame
    return QtCallable(f, 2)
