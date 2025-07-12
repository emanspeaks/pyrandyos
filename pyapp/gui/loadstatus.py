from typing import overload, Any, TypeVar, TYPE_CHECKING
from collections.abc import Callable
from contextlib import contextmanager
from functools import wraps

if TYPE_CHECKING:
    from .splash import GuiSplashScreen

LOAD_STEP_REGISTRY: set[str] = set()
COMPLETED_LOAD_STEPS: set[str] = set()
STARTED_LOAD_STEPS: set[str] = set()

F = TypeVar("F", bound=Callable[..., Any])


def register_load_step(arg: str | Callable):  # noqa: E302
    if callable(arg):
        arg()
    else:
        reg = LOAD_STEP_REGISTRY
        reg.add(arg)


@overload
def register_as_load_step(step_name: str) -> F: ...
@overload
def register_as_load_step(func: Callable) -> F: ...
def register_as_load_step(arg):  # noqa: E302
    register_load_step(arg)

    def register_load_step_decorator(func: F) -> F:
        @wraps(func)
        def register_load_step_wrapper(*args, **kwargs):
            __traceback_hide__ = True  # noqa: F841
            return func(*args, **kwargs)
        return register_load_step_wrapper
    return register_load_step_decorator


def load_status_step(step_name: str, show_step_start: bool = True,
                     show_step_done: bool = False):
    def load_status_step_decorator(func: F) -> F:
        @wraps(func)
        def load_status_step_wrapper(*args, **kwargs):
            __traceback_hide__ = True  # noqa: F841
            with loading_step_context(step_name,
                                      show_step_start=show_step_start,
                                      show_step_done=show_step_done):
                return func(*args, **kwargs)

        register_load_step(step_name)
        return load_status_step_wrapper  # type: ignore
    return load_status_step_decorator


def mark_load_step_completed(step_name: str, show_step_name: bool = False,
                             process_events: bool = True):
    if step_name in LOAD_STEP_REGISTRY:
        reg = COMPLETED_LOAD_STEPS
        reg.add(step_name)
        from .gui_app import get_gui_app
        splash: GuiSplashScreen = getattr(get_gui_app(), 'splash', None)
        if splash:
            splash.set_progress(value=len(reg),
                                message=step_name if show_step_name else None,
                                process_events=process_events)


def mark_load_step_started(step_name: str, show_step_name: bool = True,
                           process_events: bool = True):
    if step_name in LOAD_STEP_REGISTRY:
        reg = STARTED_LOAD_STEPS
        reg.add(step_name)
        from .gui_app import get_gui_app
        splash: GuiSplashScreen = getattr(get_gui_app(), 'splash', None)
        if splash:
            splash.set_progress(message=step_name if show_step_name else None,
                                process_events=process_events)


def splash_message(message: str, process_events: bool = True):
    from .gui_app import get_gui_app
    splash: GuiSplashScreen = getattr(get_gui_app(), 'splash', None)
    if splash:
        splash.set_progress(message=message, process_events=process_events)


@contextmanager
def loading_step_context(step_name: str, show_step_start: bool = True,
                         show_step_done: bool = False):
    __traceback_hide__ = True  # noqa: F841
    mark_load_step_started(step_name, show_step_start)
    yield
    # don't do a try block because if the block fails, we didn't complete
    mark_load_step_completed(step_name, show_step_done)
