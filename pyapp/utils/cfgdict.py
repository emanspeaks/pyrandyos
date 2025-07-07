# from ..logging import DEBUGLOW2, log_func_call
from .constants import NODEFAULT, IS_WIN32
from .casesafe import (
    casesafe_dict_get, casesafe_dict_set, casesafe_key_in_dict,
)


# @log_func_call(DEBUGLOW2, trace_only=True)
def try_get_item(config: dict | list | tuple, key: str | int,
                 default=NODEFAULT, case_insensitive: bool = IS_WIN32):
    try:
        return casesafe_dict_get(config, key, default, case_insensitive)
    except TypeError:
        return try_get_item(config, int(key), default)
    except (KeyError, IndexError):
        return default


# @log_func_call(DEBUGLOW2, trace_only=True)
def config_dict_get(config: dict[str] | list | tuple, key: str,
                    default=NODEFAULT, case_insensitive: bool = IS_WIN32):
    """
    Get the value from a dict with given key.  If the key contains '.', it
    assumes that the key is a dot-delimited list of keys of nested dicts or
    lists, and will recursively drill down through the given "root" dict
    to return the ultimate value.

    Args:
        config (dict): dict (of nested dicts or lists) to search for key
        key (str): key to get from dict or dot-delimited list of keys
        default (Any, optional): Value to return if key not found.
           Defaults to NODEFAULT, which raises a KeyError if key is not found.

    Raises:
        KeyError: key not found in `config` or its nested children

    Returns:
        Any: value for key or default value (if provided)
    """
    parts = key.split('.', 1)
    part0 = parts[0]
    part1 = '.'.join(parts[1:])
    if hasattr(config, 'get'):
        value = casesafe_dict_get(config, part0, default, case_insensitive)

    elif hasattr(config, '__getitem__'):
        value = try_get_item(config, part0, default, case_insensitive)

    if part1 and hasattr(value, '__getitem__'):
        value = config_dict_get(value, part1, default, case_insensitive)

    if value is NODEFAULT:
        raise KeyError(key)
    return value


# @log_func_call(DEBUGLOW2, trace_only=True)
def config_dict_set(config: dict, key: str, value,
                    case_insensitive: bool = IS_WIN32):
    """
    Set the value in a dict with given key.  If the key contains '.', it
    assumes that the key is a dot-delimited list of keys of nested dicts or
    lists, and will recursively drill down through the given "root" dict
    to set the ultimate value.

    Args:
        config (dict): dict (of nested dicts or lists) to search for key to set
        key (str): key to set in dict or dot-delimited list of keys
        value (Any): Value to set
    """
    parts = key.split('.', 1)
    part0 = parts[0]
    part1 = '.'.join(parts[1:])
    if key == part0:
        casesafe_dict_set(config, key, value, case_insensitive)
    else:
        if not casesafe_key_in_dict(config, part0, case_insensitive):
            casesafe_dict_set(config, part0, dict(), case_insensitive)

        config_dict_set(config[part0], part1, value)


# @log_func_call(DEBUGLOW2, trace_only=True)
def config_dict_update(config: dict, data: dict,
                       case_insensitive: bool = IS_WIN32):
    """
    Update a dict with data from another dict.  The keys in incoming dict may
    be dot-delimited, indicating that the update will be performed recursively
    on any specified nested dicts or lists.

    Args:
        config (dict): dict (of nested dicts or lists) to update
        data (dict): incoming data to add/replace in `config` (recursively)
    """
    for k, v in data.items():
        config_dict_set(config, k, v, case_insensitive)
