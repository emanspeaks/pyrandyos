from os import environ
from pathlib import Path

from ..logging import log_func_call, DEBUGLOW2
from ..utils.expandvars import substitute_key, get_unresolved_keys
from ..utils.cfgdict import config_dict_get, config_dict_set
from ..utils.constants import IS_WIN32
from ..utils.casesafe import casesafe_value_in_container


@log_func_call(DEBUGLOW2, trace_only=True)
def _expand_nested(config: dict, key: str, value,
                   skip_expansion: str | list[str] | tuple[str] = None,
                   case_insensitive: bool = IS_WIN32):
    case = case_insensitive
    expand_key_recursively(config, key, skip_expansion, case_insensitive=case)
    return substitute_key(value, key,
                          config_dict_get(config, key,
                                          case_insensitive=case), case)


@log_func_call(DEBUGLOW2, trace_only=True)
def expand_key_recursively(config: dict, key: str,
                           skip_expansion: str | list[str] | tuple[str] = None,
                           fail: bool = False, set_value: bool = True,
                           case_insensitive: bool = IS_WIN32):
    case = case_insensitive
    skip_expansion = skip_expansion or ()
    if isinstance(skip_expansion, str):
        skip_expansion = (skip_expansion,)

    value = config_dict_get(config, key, case_insensitive=case)
    if isinstance(value, Path):
        value = str(value)
    while isinstance(value, str) and '$' in value:
        needed_keys = get_unresolved_keys(value)
        skipped = 0
        for k in needed_keys:
            if casesafe_value_in_container(skip_expansion, k, case):
                skipped += 1
                continue
            if '.' in k or casesafe_value_in_container(config, k, case):
                value = _expand_nested(config, k, value, skip_expansion,
                                       case)
            elif k in environ:
                value = substitute_key(value, k, environ[k])
            else:
                if fail:
                    raise KeyError(f'unknown key: {k}')
                else:
                    skipped += 1

        if skipped and skipped == len(needed_keys):
            break

    if set_value:
        config_dict_set(config, key, value, case)

    return value
