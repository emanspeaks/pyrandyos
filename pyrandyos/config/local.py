from pathlib import Path
from copy import deepcopy

from ..utils.json import load_jsonc, save_json, jsonify
from ..utils.cfgdict import (
    config_dict_update, config_dict_get, config_dict_set,
)
from ..utils.constants import IS_WIN32
from ..utils.casesafe import casesafe_value_in_container, casesafe_is_equal

from ..logging import log_func_call
from .appconfig import AppConfig
from .expandutils import expand_key_recursively
from .keys import get_path_keys, LOCAL_CONFIG_FILE_KEY, LOCAL_CFG_KEY


@log_func_call
def load_local_config():
    local_cfg_path: Path = AppConfig[LOCAL_CONFIG_FILE_KEY]
    if local_cfg_path.exists():
        return load_jsonc(local_cfg_path)
    return dict()


@log_func_call
def process_local_config(base: dict = None, app_path_keys: tuple[str] = (),
                         case_insensitive: bool = None):
    "returns True if a local config was found and loaded, else False"
    if not base:
        base = AppConfig.get_global_config()
        case = AppConfig.get_case(case_insensitive)
    else:
        case = IS_WIN32 if case_insensitive is None else case_insensitive

    local_cfg = load_local_config()
    use_local = bool(local_cfg)
    if use_local:
        from ..logging import log_info
        log_info(f"Using local config: {AppConfig[LOCAL_CONFIG_FILE_KEY]}")

    for k in local_cfg.keys():
        expand_key_recursively(local_cfg, k, case_insensitive=case)

    config_dict_update(get_local_config(base), local_cfg, case)
    AppConfig.process_config(config=base, app_path_keys=app_path_keys,
                             case_insensitive=case)

    return use_local


@log_func_call
def get_local_config(base: dict = None, case_insensitive: bool = None):
    if not base:
        base = AppConfig.get_global_config()
        case = AppConfig.get_case(case_insensitive)
    else:
        case = IS_WIN32 if case_insensitive is None else case_insensitive

    local_cfg: dict = config_dict_get(base, LOCAL_CFG_KEY, {}, case)
    return local_cfg


@log_func_call
def save_local_config(app_path_keys: tuple = (),
                      case_insensitive: bool = None):
    case = AppConfig.get_case(case_insensitive)

    # get the verbatim contents of "old" local config
    old_local_cfg = load_local_config()

    # make a temp copy of current global config
    cfgtmp = deepcopy(AppConfig.get_global_config())

    # process the "old" local config with the temp global copy to get
    # "old" expansions
    process_local_config(cfgtmp, app_path_keys, case)
    old_local_expanded = get_local_config(cfgtmp, case)

    # check if each key is present in old config.
    # If not, add it to the output.
    # If it is, check that the "expanded" values match.
    # If they match, keep the original unexpanded value.
    # Otherwise, use the new expanded value for lack of better guidance.
    pathkeys = get_path_keys(app_path_keys)
    local_cfg: dict = get_local_config(case_insensitive=case)
    out = old_local_cfg.copy()
    for k, v in local_cfg.items():
        if not casesafe_value_in_container(old_local_cfg, k, case):
            if casesafe_value_in_container(pathkeys, f'{LOCAL_CFG_KEY}.{k}'):
                v: Path
                v = v.as_posix()

            config_dict_set(out, k, v, case)
        else:
            v_old = config_dict_get(old_local_cfg, k, case_insensitive=case)
            v_test = v_old
            if casesafe_value_in_container(pathkeys, f'{LOCAL_CFG_KEY}.{k}'):
                v_test: Path = config_dict_get(old_local_expanded, k,
                                               case_insensitive=case)
                v_test = v_test.as_posix()
                v: Path
                v = v.as_posix()

            config_dict_set(out, k,
                            v if not casesafe_is_equal(v_test, v) else v_old,
                            case)

    # save the new output local config
    local_cfg_path: Path = AppConfig[LOCAL_CONFIG_FILE_KEY]
    save_json(local_cfg_path, jsonify(out))
    from ..logging import log_info
    log_info(f'local config saved to {local_cfg_path}')
