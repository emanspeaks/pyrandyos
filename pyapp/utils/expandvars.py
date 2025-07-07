# adapted from code in Python stdlib posixpath.py
from typing import Any
from collections.abc import Callable
from re import compile, ASCII
from functools import partial
from os import environ

from ..logging import log_func_call, DEBUGLOW2
from .cfgdict import config_dict_get
from .constants import IS_WIN32
from .casesafe import casesafe_is_equal, casesafe_value, casesafe_key_in_dict

_VARPROG = compile(r'\$(\w+|\{[^}]*\})', ASCII)
_STARTBRAK = '{'
_ENDBRAK = '}'
_NOTFOUND = object()


@log_func_call(DEBUGLOW2, trace_only=True)
def expandvars_base(x: str, callback: Callable) -> str:
    """
    Invokes `callback()` when string `x` contains a variable of the form
    "$variable" or "${variable}" and returns the resultant string after
    callbacks.

    In the context of `expandvars()`, the callable substitutes the variable
    with a value, but `expandvars_base()` allows the user to customize this
    behavior.  Example alternative use cases could be to simply collect a list
    of all the variables in the string and perform no substitutions or to do
    some sort of conditional substitution.

    The user-provided `callback` should have the signature
    `callback(data: dict)`.  The argument `data` is a dictionary with the
    following keys/values:

        * `x`: current working version of the full modified string
        * `i`: index of the `$` character in `x` for the current variable upon
            which the callback is to operate
        * `j`: index of the first character in `x` following the current
            variable upon which the callback is to operate
        * `name`: the name of the variable

    The callback should return True if `expandvars_base()` should continue
    searching for more variables in `x` or False to end the search early and
    return `x` in its current state.

    See the code for `expandvars()` or `get_unresolved_keys()` for complete
    usage examples.

    Args:
        x (str): input string to search for variables to expand
        callback (Callable): user-provided callback with signature
            `callback(data: dict) -> bool`

    Returns:
        str: value of `x` after performing callbacks
    """
    search = _VARPROG.search
    data = {'x': x, 'i': 0}
    ok_to_continue = True
    while ok_to_continue:
        m = search(data['x'], data['i'])
        if not m:
            break

        data['i'], data['j'] = m.span(0)
        name = m.group(1)
        if name.startswith(_STARTBRAK) and name.endswith(_ENDBRAK):
            name = name[1:-1]

        data['name'] = name
        ok_to_continue = callback(data)
        if ok_to_continue is None:
            ok_to_continue = True

    return data['x']


@log_func_call(DEBUGLOW2, trace_only=True)
def substitute_callback(key: str, subst: str, case_insensitive: bool,
                        data: dict):
    if casesafe_is_equal(data['name'], key, case_insensitive):
        x = data['x']
        tail = x[data['j']:]
        x = x[:data['i']] + str(subst)
        data['i'] = len(x)
        data['x'] = x + tail
        return False
    return True


@log_func_call(DEBUGLOW2, trace_only=True)
def substitute_key(value: str, key: str, subst: str,
                   case_insensitive: bool = IS_WIN32):
    return expandvars_base(value, partial(substitute_callback, key, subst,
                                          case_insensitive))


@log_func_call(DEBUGLOW2, trace_only=True)
def unresolved_keys_callback(keylist: list, data: dict):
    keylist.append(data['name'])
    data['i'] = data['j']
    return True


@log_func_call(DEBUGLOW2, trace_only=True)
def get_unresolved_keys(x: str):
    keys: list[str] = list()
    expandvars_base(x, partial(unresolved_keys_callback, keys))
    return keys


@log_func_call(DEBUGLOW2, trace_only=True)
def expandvars_callback(addl_expand_vars: dict, case_insensitive: bool,
                        data: dict):
    value = _NOTFOUND
    name: str = casesafe_value(data['name'], case_insensitive)
    if '.' in name or casesafe_key_in_dict(addl_expand_vars, name,
                                           case_insensitive):
        value = config_dict_get(addl_expand_vars, name, _NOTFOUND,
                                case_insensitive)

    if value is _NOTFOUND:
        try:
            value = environ[name]
        except KeyError:
            pass

    if value is _NOTFOUND:
        value = None

    if value is None:
        data['i'] = data['j']

    else:
        substitute_callback(name, value, case_insensitive, data)


@log_func_call(DEBUGLOW2, trace_only=True)
def expandvars(x: str, addl_expand_vars: dict[str, Any] = {},
               case_insensitive: bool = IS_WIN32) -> str:
    """
    Expand variables of form $var and ${var}.  Unknown variables
    are left unchanged.  Searches for `var` in `addl_expand_vars` first, then
    checks `os.environ`.  This way, env vars can be overridden locally or
    additional context vars can be used.

    Args:
        x (str): string to search for variables in which to substitute
        addl_expand_vars (dict, optional): additional variables to override or
            supplement the current OS environment variables. Defaults to {}.

    Returns:
        str: string with all known variables substituted
    """

    if '$' not in x:
        return x
    return expandvars_base(x, partial(expandvars_callback, addl_expand_vars,
                                      case_insensitive))


@log_func_call(DEBUGLOW2, trace_only=True)
def is_key_resolved(x: str, key: str, case_insensitive: bool = IS_WIN32):
    return not casesafe_key_in_dict(get_unresolved_keys(x), key,
                                    case_insensitive)
