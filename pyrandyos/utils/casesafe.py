from typing import TypeVar
from collections.abc import Container, Sequence, Mapping

# from ..logging import DEBUGLOW2, log_func_call
from .constants import NODEFAULT, IS_WIN32

ContainerType = TypeVar('T', bound=Container)


# @log_func_call(DEBUGLOW2, trace_only=True)
def casesafe_value(x, case_insensitive: bool = IS_WIN32):
    # if isinstance(x, str) and case_insensitive:
    if hasattr(x, 'lower') and case_insensitive:
        return x.lower()
    return x


# @log_func_call(DEBUGLOW2, trace_only=True)
def casesafe_container(x: ContainerType, case_insensitive: bool = IS_WIN32
                       ) -> ContainerType:
    return type(x)(casesafe_value(z, case_insensitive) for z in x)


# @log_func_call(DEBUGLOW2, trace_only=True)
def casesafe_sequence_index(x: Sequence, value,
                            case_insensitive: bool = IS_WIN32):
    seq = casesafe_container(x, case_insensitive)
    return seq.index(casesafe_value(value, case_insensitive))


# @log_func_call(DEBUGLOW2, trace_only=True)
def casesafe_dict_key_map(d: Mapping, case_insensitive: bool = IS_WIN32):
    return {casesafe_value(x, case_insensitive): x for x in d}


# @log_func_call(DEBUGLOW2, trace_only=True)
def casesafe_dict_get(d: Mapping, key, default=NODEFAULT,
                      case_insensitive: bool = IS_WIN32):
    key = casesafe_value(key, case_insensitive)
    lookup = casesafe_dict_key_map(d, case_insensitive)
    return d[lookup[key]] if key in lookup else default


# @log_func_call(DEBUGLOW2, trace_only=True)
def casesafe_dict_set(d: Mapping, key, value,
                      case_insensitive: bool = IS_WIN32):
    lookup = casesafe_dict_key_map(d, case_insensitive)
    key = casesafe_value(key, case_insensitive)
    key = lookup[key] if key in lookup else key
    d[key] = value


# @log_func_call(DEBUGLOW2, trace_only=True)
def casesafe_key_in_dict(d: Mapping, key, case_insensitive: bool = IS_WIN32):
    return casesafe_value_in_container(d, key, case_insensitive)


# @log_func_call(DEBUGLOW2, trace_only=True)
def casesafe_value_in_container(c: Container, key,
                                case_insensitive: bool = IS_WIN32):
    # if isinstance(c, Mapping):
    if hasattr(c, 'keys'):
        c = tuple(casesafe_dict_key_map(c, case_insensitive).keys())
    return (casesafe_value(key, case_insensitive)
            in casesafe_container(c, case_insensitive))


# @log_func_call(DEBUGLOW2, trace_only=True)
def casesafe_is_equal(a, b, case_insensitive: bool = IS_WIN32):
    a = casesafe_value(a, case_insensitive)
    b = casesafe_value(b, case_insensitive)
    return a == b
