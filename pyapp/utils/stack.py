import sys
from types import TracebackType, FrameType, ModuleType
from typing import overload
from collections.abc import Callable
from pathlib import Path
from inspect import getfile, getmodule, currentframe
from importlib import import_module
from logging import _srcfile
from traceback import StackSummary, FrameSummary, TracebackException
from itertools import islice
from linecache import (
    lazycache as lazylinecache, checkcache as checklinecache,
    getline as getcachedline
)

SCRIPTPATH = Path(__file__)
STDLIB_LOGGING_SRCFILE = Path(_srcfile)
RUNPY_SRCFILE = (Path(sys.modules['runpy'].__file__) if 'runpy' in sys.modules
                 else None)
SHOW_TRACEBACK_LOCALS = False

ModAndName = tuple[ModuleType, str]


def set_show_traceback_locals(enabled: bool = True):
    global SHOW_TRACEBACK_LOCALS
    SHOW_TRACEBACK_LOCALS = bool(enabled)


def get_stack_frame(level: int = 1):
    __traceback_hide__ = True  # noqa: F841
    frm = currentframe()
    for i in range(level):
        if frm is None:
            raise ValueError(f"Stack frame level {level} does not exist.")
        frm = frm.f_back
    return frm


@overload
def get_module_and_name(modname: str = None) -> ModAndName: ...
@overload
def get_module_and_name(obj: object = None) -> ModAndName: ...
def get_module_and_name(arg=None):  # noqa: E302
    "returns mod, modname"
    mod = (import_module(arg) if isinstance(arg, str)
           else getmodule(arg or get_stack_frame(2)))
    return mod, mod.__name__ if mod else None


@overload
def top_module_and_name(modname: str = None) -> ModAndName: ...
@overload
def top_module_and_name(obj: object = None) -> ModAndName: ...
def top_module_and_name(arg=None):  # noqa: E302
    _, modname = get_module_and_name(arg or get_stack_frame(2))
    if modname:
        modname = modname.split('.')[0]
        try:
            return import_module(modname), modname
        except TypeError:
            pass

    return None, modname


@overload
def get_module_dir_path(modname: str = None) -> Path: ...
@overload
def get_module_dir_path(obj: object = None) -> Path: ...
def get_module_dir_path(arg=None):  # noqa: E302
    mod, modname = get_module_and_name(arg or get_stack_frame(2))
    try:
        return Path(getfile(mod)).parent
    except TypeError:
        if modname == '__main__':
            from .notebook import is_notebook
            # if it's not running in VSCode, idk my bff jill, why is this hard
            f = globals().get('__vsc_ipynb_file__') if is_notebook() else None
            if f:
                return Path(f).parent


@overload
def top_package_dir_path(modname: str = None) -> Path: ...
@overload
def top_package_dir_path(obj: object = None) -> Path: ...
def top_package_dir_path(arg=None):  # noqa: E302
    return get_module_dir_path(top_module_and_name(arg
                                                   or get_stack_frame(2))[0])


def is_internal_frame(frame: FrameSummary):
    __traceback_hide__ = True  # noqa: F841
    # adapted from stdlib logging._is_internal_frame
    p = Path(frame.filename).resolve()
    loc = frame.locals or {}
    return (p == STDLIB_LOGGING_SRCFILE
            or ('importlib' == p.parent and '_bootstrap' in p.name)
            or 'debugpy' in p.parts
            or 'pydevd' in p.parts
            or p == RUNPY_SRCFILE
            or p == SCRIPTPATH
            or loc.get('__traceback_hide__'))


def get_framesummary_for_frame(f: FrameType):
    # adapted from stdlib traceback._walk_tb_with_full_positions
    # and from stdlib traceback.StackSummary._extract_from_extended_frame_gen
    __traceback_hide__ = True  # noqa: F841
    lasti = f.f_lasti
    f_locals = f.f_locals
    code = f.f_code
    name = code.co_name
    filename = code.co_filename
    lazylinecache(filename, f.f_globals)
    checklinecache(filename)
    lineno = None if lasti < 0 else f.f_lineno
    posgen: Callable = getattr(code, 'co_positions', None)
    if posgen:
        lineno2, end_lineno, colno, end_colno = next(islice(posgen(),
                                                            lasti // 2, None))
        if lineno2 is not None:
            lineno = lineno2

        # I like seeing the underlines in the tracebacks, but if the issue is
        # the entire line, it doesn't print them.  As a hack, just lop off the
        # last character of the line.
        line = getcachedline(filename, lineno)
        start_offset = byte_offset_to_character_offset(line, colno)
        end_offset = byte_offset_to_character_offset(line, end_colno)
        stripped_line = line.strip()
        if end_offset - start_offset >= len(stripped_line):
            end_colno -= 1

    kwargs = {
        'end_lineno': end_lineno,
        'colno': colno,
        'end_colno': end_colno
    } if posgen else {}

    summary = FrameSummary(filename, lineno, name, lookup_line=False,
                           locals=f_locals, **kwargs)
    summary.line
    return summary


def build_stacksummary_for_frame(f: FrameType | None = None):
    # adapted from stdlib traceback._walk_tb_with_full_positions
    # and from stdlib traceback.StackSummary._extract_from_extended_frame_gen
    __traceback_hide__ = True  # noqa: F841

    # If you want to limit the stack, you'll have to just slice the output
    # because I am removing the limits here to reduce complexity.
    result = StackSummary()
    f = f or get_stack_frame(2)
    while f is not None:
        result.append(get_framesummary_for_frame(f))
        f = f.f_back

    result.reverse()
    return result


def build_stacksummary_for_tb(tb: TracebackType):
    # adapted from stdlib traceback._walk_tb_with_full_positions
    # and from stdlib traceback.StackSummary._extract_from_extended_frame_gen
    __traceback_hide__ = True  # noqa: F841

    # If you want to limit the stack, you'll have to just slice the output
    # because I am removing the limits here to reduce complexity.
    result = StackSummary()
    tb: TracebackType | None
    while tb is not None:
        result.append(get_framesummary_for_frame(tb.tb_frame))
        tb = tb.tb_next

    return result


def filter_stack(stk: StackSummary = None):
    __traceback_hide__ = True  # noqa: F841
    stk = stk or build_stacksummary_for_frame(get_stack_frame(2)) or ()
    return StackSummary.from_list([f for f in stk if not is_internal_frame(f)])


def byte_offset_to_character_offset(s: str, offset: int):
    as_utf8 = s.encode('utf-8')
    return len(as_utf8[:offset].decode("utf-8", errors="replace"))


def find_caller(stack_info=False, stacklevel=1):
    __traceback_hide__ = True  # noqa: F841
    stk = filter_stack()
    if not stk:
        return "(unknown file)", 0, "(unknown function)", None
    f = stk[stacklevel - 1]
    sinfo = (f"Stack (most recent call last):\n{''.join(stk.format())}"
             if stack_info else None)
    return f.filename, f.lineno, f.name, sinfo


def filter_traceback_fullstack(tb: TracebackType):
    __traceback_hide__ = True  # noqa: F841
    tbstack = filter_stack(build_stacksummary_for_tb(tb))
    stk = filter_stack(build_stacksummary_for_frame(tb.tb_frame))
    fullstack = StackSummary.from_list(stk[:-1] + tbstack)
    if not SHOW_TRACEBACK_LOCALS:
        # remove locals from the stack frames
        for f in fullstack:
            f.locals = None

    return fullstack


def build_traceback_exception(exc: BaseException | TracebackException,
                              tb: TracebackType = None, compact: bool = False):
    __traceback_hide__ = True  # noqa: F841

    seen = set()
    seen.add(id(exc))

    tb = tb or exc.__traceback__
    te = (exc if isinstance(exc, TracebackException)
          else TracebackException(type(exc), exc, tb, compact=compact))
    te.stack = filter_traceback_fullstack(tb)
    top_te = te

    queue = [(te, exc)]
    while queue:
        te, exc = queue.pop()
        te_cause = te.__cause__
        exc_cause = exc.__cause__ if te_cause else None
        exc_cause_id = id(exc_cause)
        if te_cause and exc_cause_id not in seen:
            seen.add(exc_cause_id)
            tb = exc_cause.__traceback__
            te_cause.stack = filter_traceback_fullstack(tb)
            queue.append((te_cause, exc_cause))

        te_context = te.__context__
        exc_context = exc.__context__ if te_context else None
        exc_context_id = id(exc_context)
        if te_context and exc_context_id not in seen:
            seen.add(exc_context_id)
            tb = exc_context.__traceback__
            te_context.stack = filter_traceback_fullstack(tb)
            queue.append((te_context, exc_context))

        te_exceptions = te.exceptions
        if te_exceptions:
            exc_exceptions = exc.exceptions
            for i, e in enumerate(exc_exceptions):
                e_id = id(e)
                if e_id not in seen:
                    seen.add(e_id)
                    tb = e.__traceback__
                    te_exceptions[i].stack = filter_traceback_fullstack(tb)

            queue.extend(zip(te_exceptions, exc_exceptions))

    return top_te


def format_exc(exc: BaseException, tb: TracebackType = None):
    __traceback_hide__ = True  # noqa: F841
    return ''.join(build_traceback_exception(exc, tb).format())


def exc_info(exc_or_type: type | BaseException = None,
             exc: BaseException | None = None,
             traceback: TracebackType = None):
    __traceback_hide__ = True  # noqa: F841
    if isinstance(exc_or_type, BaseException):
        exc = exc_or_type
        exc_or_type = None

    if exc:
        exc_or_type = exc_or_type or type(exc)
        traceback = traceback or exc.__traceback__

    else:
        exc_or_type, exc, traceback = sys.exc_info()

    return exc_or_type, exc, traceback
