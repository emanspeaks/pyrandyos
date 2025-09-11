import sys
from inspect import signature
from collections.abc import Callable
from functools import partial, update_wrapper
from textwrap import dedent

from .stack import (
    safe_exec, get_framesummary_for_frame, get_stack_frame,
    mark_next_tb_reraise_to_skip,
)


def generate_signature_aware_wrapper(func: Callable, arg_handler: Callable,
                                     *handler_args, **handler_kwargs):
    # __traceback_hide__ = True  # noqa: F841
    __traceback_hide_locals__ = True  # noqa: F841

    # If func is a partial, get the original function
    # to ensure signature and metadata are correct.
    if isinstance(func, partial):
        original_func = func.func
    else:
        original_func = func

    handler_partial = partial(arg_handler, handler_args, handler_kwargs, func)
    sig = signature(func)
    sigparams = sig.parameters

    # Build code to collect args and kwargs from the named parameters
    args_list = list()
    kwargs_list = list()
    param_list = list()
    defaults = dict()
    for p in sigparams.values():
        if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD):
            args_list.append(p.name)
            if p.default is not p.empty:
                param_list.append(f'{p.name}=__defaults[{p.name!r}]')
                defaults[p.name] = p.default
            else:
                param_list.append(p.name)
        elif p.kind == p.VAR_POSITIONAL:
            s = f'*{p.name}'
            args_list.append(s)
            param_list.append(s)
        elif p.kind == p.KEYWORD_ONLY:
            kwargs_list.append(f'{p.name}={p.name}')
            if p.default is not p.empty:
                param_list.append(f'{p.name}=__defaults[{p.name!r}]')
                defaults[p.name] = p.default
            else:
                param_list.append(p.name)
        elif p.kind == p.VAR_KEYWORD:
            s = f'**{p.name}'
            kwargs_list.append(s)
            param_list.append(s)

    args_str = ', '.join(args_list)
    kwargs_str = ', '.join(kwargs_list)
    params = ', '.join(param_list)
    bindparams = f'{args_str}{", " if kwargs_str else ""}{kwargs_str}'

    # Create the wrapper source code with the same signature
    f = get_stack_frame()
    src_frame = get_framesummary_for_frame(f, lineno=f.f_lineno + 1)
    src = dedent(f"""
    def signature_aware_wrapper({params}):
        __traceback_hide__ = True  # noqa: F841
        try:
            __bound = __sig.bind({bindparams})
            __bound.apply_defaults()
            __func_args, __func_kwargs = __handler_partial(*__bound.args,
                                                           **__bound.kwargs)
            return __func(*__func_args, **__func_kwargs)
        except BaseException as __e:
            __e._pyrandyos_exec_source = __src
            __e._pyrandyos_exec_source_frame = __src_frame
            __mark_next_tb_reraise_to_skip(__e)
            raise __e
    """)

    # Create wrapper in a safe namespace
    env = {'__func': func, '__sig': sig, '__handler_partial': handler_partial,
           '__src': src, '__src_frame': src_frame, '__defaults': defaults,
           '__mark_next_tb_reraise_to_skip': mark_next_tb_reraise_to_skip}
    loc = None  # {'func_args': None, 'func_kwargs': None,}
    e_to_raise = None
    modules = sys.modules
    tryagain = True
    while tryagain:
        tryagain = False
        try:
            safe_exec(src, env, loc, log_errors=False, src_frame=src_frame)
        except NameError as e:
            name = e.name
            if name in modules:
                # If the name is in sys.modules, it might be a module import
                # that needs to be added to the environment.
                env[name] = modules[name]
                tryagain = True

            else:
                # If the name is not found, it might be a real missing import
                # or other name error or typo.
                # Raise the original exception.
                e_to_raise = e

        except BaseException as e:
            e_to_raise = e

    if e_to_raise:
        try:
            from ..logging import log_exc
        except ImportError:
            pass
        else:
            log_exc(e_to_raise)

        raise e_to_raise

    signature_aware_wrapper = env['signature_aware_wrapper']
    update_wrapper(signature_aware_wrapper, func)

    # Copy metadata (from the original function if it's a partial)
    signature_aware_wrapper.__name__ = original_func.__name__
    signature_aware_wrapper.__doc__ = original_func.__doc__
    signature_aware_wrapper.__module__ = original_func.__module__

    return signature_aware_wrapper


def example_decorator_arg_handler(handler_args: tuple, handler_kwargs: dict,
                                  func: Callable, *func_args, **func_kwargs):
    """
    This method can be used to handle the function arguments
    before calling the actual function.  Override this method
    in subclasses to customize argument handling.
    """
    print(f"Decorator args: {handler_args}, kwargs: {handler_kwargs}")
    print(f"Function args: {func_args}, kwargs: {func_kwargs}")
    print(f"Function name: {func.__qualname__}")
    return func_args, func_kwargs


def example_decorator(message: str):
    def example_decorator_factory(func):
        return generate_signature_aware_wrapper(func,
                                                example_decorator_arg_handler,
                                                message)
    return example_decorator_factory


@example_decorator("argument passed to decorator at compile time, "
                   "handled by arg_handler at run time")
def example_decorated_function():
    print("Example function executed.")
