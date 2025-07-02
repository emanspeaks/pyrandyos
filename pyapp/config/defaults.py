from pathlib import Path
from copy import deepcopy

############
# FIXED KEYS
#
# What is ironic is that I titled this section in all caps, but this note is
# here to say that all fixed keys should always be lowercase.

# bootstrap keys
BASE_PATH_KEY = 'base_path'  # not included in PATH_KEYS, handle manually
ABS_BASE_PATH_KEY = 'base_path:abs'  # not included in PATH_KEYS
BASE_LOG_DIR_KEY = 'log_dir'
LOG_TIMESTAMP_KEY = 'log_timestamp_name'
APPEND_LOG_KEY = 'append_log'
CLI_LOG_LEVEL_KEY = 'cli_log_level'
FILE_LOG_LEVEL_KEY = 'file_log_level'
# not included in PATH_KEYS since this is internal only
BASE_LOG_PATH_KEY = '__log_path'

# other fixed keys
APP_NAME_KEY = 'app_name'
APP_PKG_DIR_KEY = 'package_dir'
APP_ASSETS_DIR_KEY = 'assets_dir'

PATH_KEYS = (
    "log_dir",
    "tmp_dir",
    # "output_dir",
    "package_dir",
    "assets_dir",

    # "local.delivery_config_dir",
    "local_config_file",
)
LOGDIRKEYS = (
    "log_dir",
)

# END FIXED KEYS
################

# defaults
DEFAULTS = {
    "base_path": Path('.').resolve(),
    "log_dir": "logs",
    "tmp_dir": "${base_path:abs}",
    "log_timestamp_name": True,
    "append_log": False,
    "cli_log_level": "info",  # can also use the int values
    "file_log_level": "info",  # can also use the int values

    "local": {
        "theme": "Dark",
        "default_width": 850,
        "default_height": 660,
    },
    "local_config_file": "~/.pyapp_local_config.jsonc",
}


def get_defaults(cls, app_global_defaults: dict = {},
                 app_local_defaults: dict = {}):
    tmp = deepcopy(DEFAULTS)

    from ..utils.system import get_path_to_top_package_dir
    cfgpkgdir = get_path_to_top_package_dir()
    tmp['config_package_dir'] = cfgpkgdir

    from ..utils.system import get_top_package_dir_for_obj
    pkgdir = get_top_package_dir_for_obj(cls)
    tmp[APP_PKG_DIR_KEY] = pkgdir

    # tmp['config_assets_dir'] = pkgdir/'assets'
    tmp.update(app_global_defaults)
    local: dict = tmp.get('local', {})
    local.update(app_local_defaults)
    tmp['local'] = local
    return tmp


def get_path_keys(app_path_keys: tuple[str] = ()):
    return PATH_KEYS + app_path_keys


def get_log_dir_keys(app_log_dir_keys: tuple[str] = ()):
    return LOGDIRKEYS + app_log_dir_keys
