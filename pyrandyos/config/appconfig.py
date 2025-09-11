from logging import Logger
from pathlib import Path
from copy import deepcopy

from ..logging import (
    DEBUGLOW2, log_func_call, set_trace_logging, set_func_call_logging,
    set_global_logger, get_global_logger
)
from ..utils.classproperty import classproperty
from ..utils.paths import (
    get_expanded_pathobj, get_expanded_pureposixpath, pureposixpath_to_pathobj
)
from ..utils.json import load_jsonc
from ..utils.cfgdict import (
    config_dict_get, config_dict_set, config_dict_update,
)
from ..utils.constants import NODEFAULT, IS_WIN32
from ..utils.system import build_cmd_arg_list
from ..utils.casesafe import casesafe_is_equal, casesafe_value_in_container
from ..utils.stack import set_show_traceback_locals

from .defaults import get_defaults
from .keys import (
    BASE_LOG_DIR_KEY, BASE_PATH_KEY, LOG_TIMESTAMP_KEY,
    APPEND_LOG_KEY, CLI_LOG_LEVEL_KEY, get_path_keys, BASE_LOG_PATH_KEY,
    FILE_LOG_LEVEL_KEY, ABS_BASE_PATH_KEY, LOG_TRACE_ENABLED_KEY,
    SHOW_TRACEBACK_LOCALS_KEY, LOG_FUNC_CALL_ENABLED_KEY,
)
from .expandutils import expand_key_recursively

_GLOBAL_CFG: dict = None


class AppConfigType(type):
    # this is really just here for VSCode syntax highlighting because the real
    # class won't necessarily have access to this as a metaclass.
    # Don't overthink this.  Just make sure it's set in AppConfig and
    # its subclasses.
    CONFIG_CASE_INSENSITIVE: bool

    @log_func_call(DEBUGLOW2, trace_only=True)
    def get_case(cls, case_insensitive: bool = None):
        return (cls.CONFIG_CASE_INSENSITIVE if case_insensitive is None
                else case_insensitive)

    @log_func_call(DEBUGLOW2, trace_only=True)
    def __contains__(cls, item):
        return casesafe_value_in_container(_GLOBAL_CFG, item, cls.get_case())


class AppConfig(metaclass=AppConfigType):
    CONFIG_CASE_INSENSITIVE: bool = IS_WIN32

    @log_func_call
    def __init__(self):
        # Class is intended as a singleton
        if type(self) is AppConfig:  # pragma: no cover
            raise NotImplementedError('Singleton class should not be '
                                      'instantiated')

    @classproperty
    @log_func_call(DEBUGLOW2, trace_only=True)
    def log(cls):
        return get_global_logger()

    @classmethod
    @log_func_call
    def set_logger(cls, log: Logger):
        set_global_logger(log)

    @classmethod
    @log_func_call
    def set(cls, key: str, value, case_insensitive: bool = None):
        config_dict_set(_GLOBAL_CFG, key, value,
                        cls.get_case(case_insensitive))

    @classmethod
    @log_func_call(DEBUGLOW2, trace_only=True)
    def __class_getitem__(cls, key: str):
        return config_dict_get(_GLOBAL_CFG, key,
                               case_insensitive=cls.get_case())

    @classmethod
    @log_func_call
    def set_global_config(cls, config: dict):
        log = get_global_logger()
        log.debug('setting global config')
        global _GLOBAL_CFG
        _GLOBAL_CFG = config

    @classmethod
    @log_func_call(DEBUGLOW2)
    def get_global_config(cls):
        return _GLOBAL_CFG

    @classproperty
    @log_func_call(DEBUGLOW2)
    def global_config(cls):
        return cls.get_global_config()

    @global_config.setter
    @log_func_call
    def global_config(cls, config: dict):
        cls.set_global_config(config)

    @classmethod
    @log_func_call(DEBUGLOW2, trace_only=True)
    def get(cls, key: str, default=NODEFAULT,
            case_insensitive: bool = None):
        """
        If the global app config has been set, returns the value for the
        given key if present, else returns the default if provided.
        When no global app config is set, returns None.

        If the key contains '.', it assumes that the key is a dot-delimited
        list of keys of nested dicts or lists, and will recursively drill down
        through the config dict to return the ultimate value.

        Args:
            key (str): key to get from dict or dot-delimited list of keys
            default (Any, optional): Value to return if key not found.
                Defaults to NODEFAULT, which raises a KeyError if key is
                not found.

        Raises:
            KeyError: key not found in `config` or its nested children

        Returns:
            Any: value for key or default value (if provided) or None if the
                global app config is not set.
        """
        if _GLOBAL_CFG:
            return config_dict_get(_GLOBAL_CFG, key, default,
                                   cls.get_case(case_insensitive))

    @classmethod
    @log_func_call
    def update(cls, data: dict, case_insensitive: bool = None):
        config_dict_update(_GLOBAL_CFG, data, cls.get_case(case_insensitive))

    @classmethod
    @log_func_call
    def build_cmd_args_from_config(cls, key: str):
        return build_cmd_arg_list(cls[key])

    @classmethod
    @log_func_call
    def process_config(cls, skip_expansion: str | list[str] = 'skip_expand',
                       config: dict = None, app_path_keys: tuple[str] = (),
                       case_insensitive: bool = None):
        config = config or _GLOBAL_CFG
        case = cls.get_case(case_insensitive)
        skip_expansion = skip_expansion or ()
        if isinstance(skip_expansion, str):
            skip_expansion = (skip_expansion,)

        for k in config.keys():
            # print(k)
            expand_key_recursively(config, k, skip_expansion,
                                   case_insensitive=case)

        base_path = get_expanded_pathobj(config[BASE_PATH_KEY], config, case)
        config_dict_set(config, BASE_PATH_KEY, base_path, case)
        config_dict_set(config, ABS_BASE_PATH_KEY, base_path.absolute(), case)
        for k in get_path_keys(app_path_keys):
            if casesafe_is_equal(k, BASE_PATH_KEY):
                continue

            v = config_dict_get(config, k, None, case)
            if v:
                config_dict_set(config, k, cls.handle_path(v, base_path))

        set_trace_logging(config_dict_get(config, LOG_TRACE_ENABLED_KEY,
                                          case_insensitive=case))
        set_func_call_logging(config_dict_get(config,
                                              LOG_FUNC_CALL_ENABLED_KEY,
                                              case_insensitive=case))
        set_show_traceback_locals(config_dict_get(config,
                                                  SHOW_TRACEBACK_LOCALS_KEY,
                                                  case_insensitive=case))
        return config

    @classmethod
    @log_func_call
    def get_base_logpath(cls):
        return config_dict_get(_GLOBAL_CFG, BASE_LOG_PATH_KEY,
                               case_insensitive=cls.get_case())

    @classmethod
    @log_func_call
    def init_parse_config(cls, indata: dict | str | Path = None,
                          overrides: dict = None, defaults: dict = None,
                          app_global_defaults: dict = {},
                          app_local_defaults: dict = {},
                          case_insensitive: bool = None):
        defaults = defaults or get_defaults(cls, app_global_defaults,
                                            app_local_defaults)

        config = deepcopy(defaults)
        if indata:
            config_dict_update(config, indata if isinstance(indata, dict)
                               else load_jsonc(indata), case_insensitive)

        if overrides:
            config_dict_update(config, overrides, case_insensitive)

        global _GLOBAL_CFG
        _GLOBAL_CFG = config

    @classmethod
    @log_func_call
    def expand_log_config(cls, skip_expansion: str | list[str] = None):
        # An abbreviated function to get the log path quickly before further
        # expansions so further error messages can be logged.
        # All of these keys are hardcoded, so we don't need to worry about case
        config = _GLOBAL_CFG
        expand_key_recursively(config, BASE_PATH_KEY, skip_expansion)
        expand_key_recursively(config, BASE_LOG_DIR_KEY, skip_expansion)
        expand_key_recursively(config, LOG_TIMESTAMP_KEY, skip_expansion)
        expand_key_recursively(config, APPEND_LOG_KEY, skip_expansion)
        expand_key_recursively(config, CLI_LOG_LEVEL_KEY, skip_expansion)
        expand_key_recursively(config, FILE_LOG_LEVEL_KEY, skip_expansion)
        expand_key_recursively(config, LOG_TRACE_ENABLED_KEY, skip_expansion)
        expand_key_recursively(config, LOG_FUNC_CALL_ENABLED_KEY,
                               skip_expansion)
        expand_key_recursively(config, SHOW_TRACEBACK_LOCALS_KEY,
                               skip_expansion)
        base_path = get_expanded_pathobj(config[BASE_PATH_KEY], config)
        logdir = config_dict_get(config, BASE_LOG_DIR_KEY)
        timestamp_name = config_dict_get(config, LOG_TIMESTAMP_KEY)
        append_log = config_dict_get(config, APPEND_LOG_KEY)
        cli_log_level = config_dict_get(config, CLI_LOG_LEVEL_KEY)
        file_log_level = config_dict_get(config, FILE_LOG_LEVEL_KEY)
        log_trace_enabled = config_dict_get(config, LOG_TRACE_ENABLED_KEY)
        log_func_call_enabled = config_dict_get(config,
                                                LOG_FUNC_CALL_ENABLED_KEY)
        tb_locals_enabled = config_dict_get(config, SHOW_TRACEBACK_LOCALS_KEY)
        return (cls.handle_path(logdir, base_path), timestamp_name,
                append_log, cli_log_level, file_log_level, log_trace_enabled,
                tb_locals_enabled, log_func_call_enabled)

    @classmethod
    @log_func_call
    def handle_path(cls, x: str, base_path: Path,
                    case_insensitive: bool = None) -> Path:
        newppp = get_expanded_pureposixpath(x, _GLOBAL_CFG, case_insensitive)
        newpath = pureposixpath_to_pathobj(newppp)

        # any relative paths are assumed to be wrt base path for now
        newpathstr = str(newpath)
        if not newpath.is_absolute() and newpathstr[0] != '$':
            if x[:2] in ('./', '.\\'):
                newpath = get_expanded_pathobj(newpath)
            else:
                newpath = base_path/newpath

        return newpath

    @staticmethod
    @log_func_call
    def get_local_config(base: dict = None, case_insensitive: bool = None):
        from .local import get_local_config as _getlocal
        return _getlocal(base, case_insensitive)

    @staticmethod
    @log_func_call
    def save_local_config(app_path_keys: tuple = (),
                          case_insensitive: bool = None):
        from .local import save_local_config as _savelocal
        _savelocal(app_path_keys, case_insensitive)
