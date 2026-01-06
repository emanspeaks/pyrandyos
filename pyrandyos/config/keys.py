############
# FIXED KEYS
#
# What is ironic is that I titled this section in all caps, but this note is
# here to say that all fixed keys should always be lowercase.

# bootstrap keys
BASE_PATH_KEY = 'base_path'  # not included in PATH_KEYS, handle manually
ABS_BASE_PATH_KEY = 'base_path:abs'  # not included in PATH_KEYS
BASE_LOG_DIR_KEY = 'log_dir'
TMP_DIR_KEY = 'tmp_dir'
LOG_TIMESTAMP_KEY = 'log_timestamp_name'
APPEND_LOG_KEY = 'append_log'
CLI_LOG_LEVEL_KEY = 'cli_log_level'
FILE_LOG_LEVEL_KEY = 'file_log_level'
STATUSBAR_LOG_LEVEL_KEY = 'statusbar_log_level'
LOCAL_CONFIG_FILE_KEY = 'local_config_file'
LOG_TRACE_ENABLED_KEY = 'log_trace_enabled'
LOG_FUNC_CALL_ENABLED_KEY = 'log_func_call_enabled'
SHOW_TRACEBACK_LOCALS_KEY = 'show_traceback_locals'
LOCAL_CFG_KEY = 'local'
QRC_FILE_KEY = 'qrc_file'
QRC_PYFILE_KEY = 'qrc_pyfile'
# not included in PATH_KEYS since this is internal only
BASE_LOG_PATH_KEY = '__log_path'

# other fixed keys
APP_NAME_KEY = 'app_name'
APP_PKG_DIR_KEY = 'package_dir'
APP_PKG_VERSION_KEY = 'package_version'
APP_ASSETS_DIR_KEY = 'assets_dir'
CONFIG_PACKAGE_DIR_KEY = 'config_package_dir'
CONFIG_PACKAGE_VERSION_KEY = 'config_package_version'
PYTHON_VERSION_KEY = 'python_version'
PYTHON_EXE_PATH_KEY = 'python_exe_path'
MONOFONT_KEY = 'monofont'

PATH_KEYS = (
    BASE_LOG_DIR_KEY,
    TMP_DIR_KEY,
    APP_PKG_DIR_KEY,
    APP_ASSETS_DIR_KEY,
    QRC_PYFILE_KEY,
    QRC_FILE_KEY,
    PYTHON_EXE_PATH_KEY,

    # "local.delivery_config_dir",
    LOCAL_CONFIG_FILE_KEY,
)
LOGDIRKEYS = (
    BASE_LOG_DIR_KEY,
)

# END FIXED KEYS
################


def get_path_keys(app_path_keys: tuple[str] = ()):
    return PATH_KEYS + app_path_keys


def get_log_dir_keys(app_log_dir_keys: tuple[str] = ()):
    return LOGDIRKEYS + app_log_dir_keys
