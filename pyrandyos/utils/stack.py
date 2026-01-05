import sys
from types import TracebackType, FrameType, ModuleType, CodeType, CellType
from typing import overload, TYPE_CHECKING, Any
from collections.abc import Callable, Mapping
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
from textwrap import indent
if TYPE_CHECKING:
    from _typeshed import ReadableBuffer


SCRIPTPATH = Path(__file__)
STDLIB_LOGGING_SRCFILE = Path(_srcfile)
RUNPY_SRCFILE = (Path(sys.modules['runpy'].__file__) if 'runpy' in sys.modules
                 else None)
SHOW_TRACEBACK_LOCALS = None

ModAndName = tuple[ModuleType, str]
ExcInfoType = tuple[type, BaseException, TracebackType]


class AnnotatedFrameSummary(FrameSummary):
    pass


def set_show_traceback_locals(enabled: bool = True):
    global SHOW_TRACEBACK_LOCALS
    SHOW_TRACEBACK_LOCALS = bool(enabled)


def get_show_traceback_locals():
    global SHOW_TRACEBACK_LOCALS
    return SHOW_TRACEBACK_LOCALS


def get_stack_frame(level: int = 1):
    __traceback_hide__ = True  # noqa: F841
    f = currentframe()
    for i in range(level):
        if f is None:
            raise ValueError(f"Stack frame level {level} does not exist.")
        f = f.f_back
    return f


def is_code_the_given_func(func: Callable, code: CodeType):
    qualname = getattr(code, 'co_qualname', None)
    bytecode = code.co_code
    match_code = False
    if not qualname:
        match_code = func.__code__.co_code == bytecode

    return qualname == func.__qualname__ if qualname else match_code


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
    filename = frame.filename
    p = Path(filename).resolve()
    loc = frame.locals or {}

    # tests broken out for debugging purposes
    testdict = dict(
        is_frozen=filename.startswith('<frozen '),
        is_stdlib_logging=p == STDLIB_LOGGING_SRCFILE,
        is_runpy=p == RUNPY_SRCFILE,
        # is_this_file=p == SCRIPTPATH,
        is_debugpy='debugpy' in p.parts,
        is_pydevd='pydevd' in p.parts,
        is_shiboken2='shiboken2' in p.parts,
        is_importlib_bootstrap=('importlib' == p.parent
                                and '_bootstrap' in p.name),
        is_traceback_hide=loc.get('__traceback_hide__')
    )
    internal = any(testdict.values())
    which = [k for k, v in testdict.items() if v] if internal else None  # noqa: E501, F841
    return internal


def get_framesummary_for_frame(f: FrameType, tb: TracebackType = None,
                               src: str = None, lineno: int = None):
    # adapted from stdlib traceback._walk_tb_with_full_positions
    # and from stdlib traceback.StackSummary._extract_from_extended_frame_gen
    __traceback_hide__ = True  # noqa: F841
    lasti = tb.tb_lasti if tb else f.f_lasti
    f_locals = f.f_locals
    code = f.f_code
    name = code.co_name
    filename = code.co_filename
    lazylinecache(filename, f.f_globals)
    checklinecache(filename)
    fixed_lineno = lineno
    if not lineno:
        lineno = None if lasti < 0 else (tb.tb_lineno if tb else f.f_lineno)

    posgen: Callable = (getattr(code, 'co_positions', None)
                        if fixed_lineno is None else None)
    underlines = bool(posgen)
    if posgen:
        lineno2, end_lineno, colno, end_colno = next(islice(posgen(),
                                                            lasti // 2, None))
        if lineno2 is not None:
            lineno = lineno2

    line = ((src.splitlines()[lineno - 1] if src else '<unknown source>')
            if filename == '<string>' else
            getcachedline(filename, lineno))
    if underlines:
        # I like seeing the underlines in the tracebacks, but if the issue is
        # the entire line, it doesn't print them.  As a hack, just lop off the
        # last character of the line.
        stripped_line = line.strip()
        striplen = len(stripped_line)
        endstriplen = len(line.rstrip())
        start_offset = byte_offset_to_character_offset(line, colno or 0)
        end_offset = byte_offset_to_character_offset(line, end_colno
                                                     or endstriplen)
        if lineno != end_lineno:
            # this is in traceback.StackSummary.format_frame_summary()
            # in Python 3.12.11, but probably is a bug?  It's not doing the
            # byte offset and just doing a raw line length...
            # which overrides the end_colno value.  Maybe this is correct
            # since it is supposed to be accounting for multiline blocks?
            # Either way, it's a problem for us since we are just printing
            # the first line, which may also not be correct.
            end_offset = endstriplen

        if end_offset - start_offset >= striplen:
            if lineno != end_lineno:
                # handles the "bug" above
                end_lineno = lineno

            # do this regardless
            end_colno = end_offset - 1

    kwargs = {
        'end_lineno': end_lineno,
        'colno': colno,
        'end_colno': end_colno
    } if posgen else {}

    summary = AnnotatedFrameSummary(filename, lineno, name, lookup_line=False,
                                    locals=f_locals, line=line, **kwargs)
    hide = f_locals.get('__traceback_hide_locals__', False)
    summary._pyrandyos_hide_locals = hide
    return summary


def build_stacksummary_for_frame(f: FrameType | None = None,
                                 reverse: bool = True):
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

    if reverse:
        result.reverse()

    return result


def build_stacksummary_for_tb(tb: TracebackType, exc: BaseException = None):
    # adapted from stdlib traceback._walk_tb_with_full_positions
    # and from stdlib traceback.StackSummary._extract_from_extended_frame_gen
    __traceback_hide__ = True  # noqa: F841

    # If you want to limit the stack, you'll have to just slice the output
    # because I am removing the limits here to reduce complexity.
    result = StackSummary()
    tb: TracebackType | None
    src: str = getattr(exc, '_pyrandyos_exec_source', '<unknown source>')
    src_f: FrameSummary = getattr(exc, '_pyrandyos_exec_source_frame', None)
    skipset = getattr(exc, '_pyrandyos_skip_next_reraise', None) or set()
    while tb is not None:
        fs = get_framesummary_for_frame(tb.tb_frame, tb, src)
        fs._pyrandyos_skip_next_reraise = id(tb) in skipset
        result.append(fs)
        tb = tb.tb_next

    if src_f:
        result.append(src_f)

    return result


def filter_stack(stk: StackSummary = None, stacklevel: int = 2):
    __traceback_hide__ = True  # noqa: F841
    # default stacklevel here is 2 since this is an absolute stacklevel
    # and we need to pop off the current frame and get_stack_frame.
    # We return the stack for the caller of this function immediately here
    # by default.
    stk = (stk or build_stacksummary_for_frame(get_stack_frame(stacklevel))
           or ())
    # return StackSummary.from_list([f for f in stk
    #                                if not is_internal_frame(f)])

    def stackgen():
        __traceback_hide__ = True  # noqa: F841
        last = None
        for f in stk:
            skip = getattr(f, '_pyrandyos_skip_next_reraise', False)
            if last and not skip:
                yield last

            if is_internal_frame(f):
                last = None
                continue

            last = f

        if last:
            yield last

    return StackSummary.from_list(list(stackgen()))


def byte_offset_to_character_offset(s: str, offset: int):
    __traceback_hide__ = True  # noqa: F841
    as_utf8 = s.encode('utf-8')
    return len(as_utf8[:offset].decode("utf-8", errors="replace"))


def get_real_caller_stack(stacklevel: int = 1):
    __traceback_hide__ = True  # noqa: F841
    f = get_stack_frame(1 + stacklevel)
    return build_stacksummary_for_frame(f, reverse=False) or ()


def filter_tb_stacksummary_if_not_internal(tb: TracebackType,
                                           exc: BaseException = None):
    __traceback_hide__ = True  # noqa: F841
    stk = build_stacksummary_for_tb(tb, exc)
    if stk:
        f = stk[-1]
        if not is_internal_frame(f):
            return filter_stack(stk)
    return stk


def log_find_caller(stack_info: bool = False, stacklevel: int = 1,
                    exc_info: ExcInfoType | None = None):
    __traceback_hide__ = True  # noqa: F841
    # stacklevel in this context is used to return the entry from the end
    # of the list from filter_stack when not given exc_info and building from
    # a traceback (in which case the stacklevel argument is effectively
    # ignored).  Because filter_stack automatically excludes __traceback_hide__
    # functions, including this one and likely any of its callers, we do NOT
    # need to apply an offset to the stack; the only reason for the default
    # stacklevel 1 is because it's actually a negative value and NOT because
    # it implies the need to pop more entries off of the stack.
    if exc_info:
        stk = filter_tb_stacksummary_if_not_internal(exc_info[2], exc_info[1])
        stacklevel = 0
    else:
        # with only default args here, filter_stack() will return a list
        # whose last element is the most recent caller that is NOT a hidden
        # function.  That means it will also exclude this current function.
        stk = filter_stack()

    if not stk:
        return "(unknown file)", 0, "(unknown function)", None
    f = stk[-stacklevel]
    sinfo = (f"Stack (most recent call last):\n{''.join(stk.format())}"
             if stack_info else None)
    return f.filename, f.lineno, f.name, sinfo


def filter_traceback_fullstack(tb: TracebackType, exc: BaseException):
    __traceback_hide__ = True  # noqa: F841
    tbstack = filter_tb_stacksummary_if_not_internal(tb, exc)
    stk = filter_stack(build_stacksummary_for_frame(tb.tb_frame))
    fullstack = StackSummary.from_list(stk[:-1] + tbstack)
    for f in fullstack:
        if SHOW_TRACEBACK_LOCALS or SHOW_TRACEBACK_LOCALS is None:
            # make a copy so we don't actually modify the frame
            loc = dict(f.locals)
            if loc:
                hide = f._pyrandyos_hide_locals
                if hide is True:
                    # remove locals from the stack frame
                    loc = None
                else:
                    if hide is False:
                        hide = ()

                    elif isinstance(hide, str):
                        hide = (hide,)

                    hide = set(('__builtins__',) + tuple(hide))
                    for n in hide:
                        if n in loc:
                            del loc[n]

            f.locals = loc
        else:
            # remove locals from the stack frames
            f.locals = None

    return fullstack


def add_src_note_to_traceback_exception(te: TracebackException,
                                        exc: BaseException,
                                        top_te: TracebackException = None):
    src = getattr(exc, '_pyrandyos_exec_source', None)
    if src:
        if hasattr(te, '__notes__'):
            noteattr = '__notes__'
            if not getattr(te, '__notes__', None):
                notelist = list()
                te.__notes__ = notelist

        else:
            te = top_te or te
            noteattr = '_pyrandyos_notes'

        notelist = getattr(te, noteattr, None)
        if notelist is None:
            notelist = list()
            setattr(te, noteattr, notelist)

        notelist.append("\n<string> code:\n" + indent(src, '    '))


def process_traceback_exception_pyrandyos_notes(te: TracebackException):
    return '\n'.join(getattr(te, '_pyrandyos_notes', ()))


def build_traceback_exception(exc: BaseException | TracebackException,
                              tb: TracebackType = None, compact: bool = False):
    __traceback_hide__ = True  # noqa: F841

    seen = set()
    seen.add(id(exc))

    tb = tb or exc.__traceback__
    te = (exc if isinstance(exc, TracebackException)
          else TracebackException(type(exc), exc, tb, compact=compact))
    te.stack = filter_traceback_fullstack(tb, exc)
    add_src_note_to_traceback_exception(te, exc)
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
            te_cause.stack = filter_traceback_fullstack(tb, exc_cause)
            add_src_note_to_traceback_exception(te_cause, exc_cause)
            queue.append((te_cause, exc_cause))

        te_context = te.__context__
        exc_context = exc.__context__ if te_context else None
        exc_context_id = id(exc_context)
        if te_context and exc_context_id not in seen:
            seen.add(exc_context_id)
            tb = exc_context.__traceback__
            te_context.stack = filter_traceback_fullstack(tb, exc_context)
            add_src_note_to_traceback_exception(te_context, exc_context)
            queue.append((te_context, exc_context))

        te_exceptions = getattr(te, 'exceptions', None)
        if te_exceptions:
            exc_exceptions = exc.exceptions
            for i, e in enumerate(exc_exceptions):
                e_id = id(e)
                if e_id not in seen:
                    seen.add(e_id)
                    tb = e.__traceback__
                    te_exceptions[i].stack = filter_traceback_fullstack(tb, e)
                    add_src_note_to_traceback_exception(te_exceptions[i], e)

            queue.extend(zip(te_exceptions, exc_exceptions))

    return top_te


def format_exc(exc: BaseException, tb: TracebackType = None):
    __traceback_hide__ = True  # noqa: F841
    te = build_traceback_exception(exc, tb)
    s = ''.join(te.format())
    s += process_traceback_exception_pyrandyos_notes(te)
    return s


def exc_info(exc_or_type: type | BaseException | ExcInfoType = None,
             exc: BaseException | None = None,
             traceback: TracebackType = None, skip_if_none: bool = False):
    __traceback_hide__ = True  # noqa: F841
    if skip_if_none and not any((exc_or_type, exc, traceback)):
        return
    if isinstance(exc_or_type, tuple):
        exc_or_type, exc, traceback = exc_or_type

    if isinstance(exc_or_type, BaseException):
        exc = exc_or_type
        exc_or_type = None

    if exc:
        exc_or_type = exc_or_type or type(exc)
        traceback = traceback or exc.__traceback__

    else:
        exc_or_type, exc, traceback = sys.exc_info()

    return exc_or_type, exc, traceback


def safe_exec(source: 'str | ReadableBuffer | CodeType',
              globals_: dict[str, Any] | None = None,
              locals_: Mapping[str, object] | None = None,
              /, *,
              closure: tuple[CellType, ...] | None = None,
              src_frame: FrameType = None,
              log_errors: bool = True):
    """
    Safely execute a Python source code string in the given environment.

    Args:
        src (str): The Python source code to execute.
        globals (dict): The global environment in which to execute the code.
        locals (dict): The local environment in which to execute the code.

    Raises:
        Exception: If there is an error during execution.
    """
    __traceback_hide__ = True  # noqa: F841
    __traceback_hide_locals__ = True  # noqa: F841
    kw = {'closure': closure} if sys.version_info >= (3, 11) else {}
    try:
        exec(source, globals_, locals_, **kw)
    except BaseException as e:
        e._pyrandyos_exec_source = source
        e._pyrandyos_exec_source_frame = src_frame
        # the next frame here will just be re-raising, so skip it
        mark_next_tb_reraise_to_skip(e)
        if log_errors:
            try:
                from ..logging import log_exc
            except ImportError:
                pass
            else:
                log_exc(e)

        raise e


def mark_next_tb_reraise_to_skip(exc: BaseException):
    """
    Skip the last re-raise in the traceback of an exception.
    This is useful for cleaning up tracebacks that have been modified
    by decorators or other code that re-raises exceptions.
    """
    __traceback_hide__ = True  # noqa: F841
    # the next frame here is just re-raising, so skip it
    # tb.tb_next = tb.tb_next.tb_next
    skipset = getattr(exc, '_pyrandyos_skip_next_reraise', None) or set()
    skipset.add(id(exc.__traceback__))
    exc._pyrandyos_skip_next_reraise = skipset
