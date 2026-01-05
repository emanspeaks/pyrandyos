import sys
from pathlib import Path
from copy import deepcopy

from .keys import (
    BASE_PATH_KEY, BASE_LOG_DIR_KEY, TMP_DIR_KEY, LOG_TIMESTAMP_KEY,
    APPEND_LOG_KEY, CLI_LOG_LEVEL_KEY, FILE_LOG_LEVEL_KEY,
    LOCAL_CONFIG_FILE_KEY, LOG_TRACE_ENABLED_KEY, LOCAL_CFG_KEY,
    CONFIG_PACKAGE_DIR_KEY, CONFIG_PACKAGE_VERSION_KEY,
    SHOW_TRACEBACK_LOCALS_KEY, QRC_FILE_KEY, LOG_FUNC_CALL_ENABLED_KEY,
    STATUSBAR_LOG_LEVEL_KEY, PYTHON_VERSION_KEY, PYTHON_EXE_PATH_KEY,
    MONOFONT_KEY,
)

# defaults
DEFAULTS = {
    BASE_PATH_KEY: Path('.').resolve(),
    BASE_LOG_DIR_KEY: "logs",
    TMP_DIR_KEY: "${base_path:abs}",
    LOG_TIMESTAMP_KEY: True,
    APPEND_LOG_KEY: False,
    CLI_LOG_LEVEL_KEY: "info",  # can also use the int values
    FILE_LOG_LEVEL_KEY: "info",  # can also use the int values
    STATUSBAR_LOG_LEVEL_KEY: "info",  # can also use the int values
    LOG_TRACE_ENABLED_KEY: False,
    LOG_FUNC_CALL_ENABLED_KEY: False,
    SHOW_TRACEBACK_LOCALS_KEY: False,
    QRC_FILE_KEY: f'${{{CONFIG_PACKAGE_DIR_KEY}}}/gui/styles/assets/vibedark.qrc',  # noqa: E501
    PYTHON_VERSION_KEY: sys.version,
    PYTHON_EXE_PATH_KEY: sys.executable,
    MONOFONT_KEY: "Consolas, Monaco, monospace",

    LOCAL_CFG_KEY: {
        "theme": "vibedark",
        "default_width": 1080,
        "default_height": 720,
    },
    LOCAL_CONFIG_FILE_KEY: "~/.pyrandyos_local_config.jsonc",
}


def get_defaults(cls: type, app_global_defaults: dict = {},
                 app_local_defaults: dict = {}):
    tmp = deepcopy(DEFAULTS)

    from ..utils.stack import top_package_dir_path
    cfgpkgdir = top_package_dir_path()
    tmp[CONFIG_PACKAGE_DIR_KEY] = cfgpkgdir

    from ..version import __version__
    tmp[CONFIG_PACKAGE_VERSION_KEY] = __version__

    tmp.update(app_global_defaults)
    local: dict = tmp.get(LOCAL_CFG_KEY, {})
    local.update(app_local_defaults)
    tmp[LOCAL_CFG_KEY] = local
    return tmp
