import sys
from pathlib import Path
from tempfile import gettempdir

from .logging import (
    log_info, Logger, log_func_call, DEBUGLOW2, set_trace_logging,
    set_func_call_logging,
)
from .config import AppConfig
from .config.keys import (
    BASE_LOG_PATH_KEY, APP_NAME_KEY, get_log_dir_keys, APP_PKG_DIR_KEY,
    APP_ASSETS_DIR_KEY, APP_PKG_VERSION_KEY, TMP_DIR_KEY, LOCAL_CFG_KEY
)
from .config.local import process_local_config

from .utils.constants import DEFAULT_GROUP, DEFAULT_DIR_MODE
from .utils.log import setup_logging, create_log_file
from .utils.main import MainContext
from .utils.system import mkdir_chgrp
from .utils.stack import (
    top_package_dir_path, top_module_and_name, set_show_traceback_locals
)
from .utils.windows.funcs import set_windows_process_app_id


class PyRandyOSApp(AppConfig):
    # abstract class attributes
    APP_NAME: str
    APP_LOG_PREFIX: str

    # class attributes with fallback defaults
    APP_PATH_KEYS: tuple[str] = ()
    APP_LOG_DIR_KEYS: tuple[str] = ()
    APP_GLOBAL_DEFAULTS = {}
    APP_LOCAL_DEFAULTS = {}
    APP_ASSETS_DIR: str | Path = None
    "path to be resolved when config is processed; may use variable expansion"

    use_local_config: bool = None

    @classmethod
    @log_func_call
    def main(cls, *args, **kwargs):
        raise NotImplementedError

    @classmethod
    @log_func_call
    def init_main(cls, config: dict | str | Path = None,
                  setup_log: bool = False, logfile: Path = None,
                  logger: Logger = None, **kwargs):
        "returns True if a local config is present and loaded, else False"
        # log = logger or get_logger()
        cls.set_logger(logger)
        cls.init_parse_config(config, kwargs)

        # setup logging first if necessary:
        (
            logdir,
            ts_name,
            append,
            cli_log_level,
            file_log_level,
            log_trace_enabled,
            tb_locals_enabled,
            log_func_call_enabled,
        ) = cls.expand_log_config()
        set_trace_logging(log_trace_enabled)
        set_func_call_logging(log_func_call_enabled)
        set_show_traceback_locals(tb_locals_enabled)
        if setup_log:
            logfile = logfile or create_log_file(logdir, ts_name, append,
                                                 cls.APP_LOG_PREFIX)
            setup_logging(logfile, cli_log_level, file_log_level)

        # start logging and process the rest of the configuration data
        cls.set(BASE_LOG_PATH_KEY, logfile)
        cls.set(APP_PKG_VERSION_KEY, cls.get_package_version())
        pkgdir = cls.get_package_dir()
        cls.set(APP_PKG_DIR_KEY, pkgdir)
        assets_dir = cls.get_assets_dir()
        if assets_dir:
            cls.set(APP_ASSETS_DIR_KEY, assets_dir)

        appname = getattr(cls, 'APP_NAME', 'PyRandyOSApp')
        cls.set(APP_NAME_KEY, appname)
        log_info(f"Starting {appname}")
        set_windows_process_app_id(appname)
        cls.process_config()

        use_local_config = process_local_config(app_path_keys=cls.APP_PATH_KEYS)  # noqa: E501
        cls.use_local_config = use_local_config
        return use_local_config

    @classmethod
    @log_func_call
    def process_config(cls, skip_expansion: str | list[str] = 'skip_expand',
                       config: dict = None):
        return super().process_config(skip_expansion, config,
                                      app_path_keys=cls.APP_PATH_KEYS)

    @classmethod
    @log_func_call
    def init_parse_config(cls, indata: dict | str | Path = None,
                          overrides: dict = None, defaults: dict = None,
                          app_global_defaults: dict = {},
                          app_local_defaults: dict = {},
                          case_insensitive: bool = None):
        global_defaults = dict()
        global_defaults.update(app_global_defaults or cls.APP_GLOBAL_DEFAULTS)
        app_local_defaults = app_local_defaults or cls.APP_LOCAL_DEFAULTS
        return super().init_parse_config(indata, overrides, defaults,
                                         global_defaults,
                                         app_local_defaults,
                                         case_insensitive)

    @classmethod
    @log_func_call
    def run_cmdline(cls, args: list[str] = None):
        if args is None:
            args = sys.argv[1:]

        with MainContext(cls.APP_NAME):
            sys.exit(cls.main(*cls.preprocess_args(args)))

    @classmethod
    @log_func_call
    def preprocess_args(cls, args: list[str]):
        if len(args) > 0:
            raise ValueError('too many command line arguments')

        return args

    @classmethod
    @log_func_call
    def create_log_dirs(cls, group: str = DEFAULT_GROUP,
                        mode: int = DEFAULT_DIR_MODE):
        for key in get_log_dir_keys(cls.APP_LOG_DIR_KEYS):
            p: Path = cls.get(key)
            mkdir_chgrp(p, group, mode)

    @classmethod
    @log_func_call(DEBUGLOW2, trace_only=True)
    def mkdir_temp(cls, name: str = None, group: str = DEFAULT_GROUP,
                   mode: int = DEFAULT_DIR_MODE):
        tmp_dir: Path | None = cls.get(TMP_DIR_KEY)
        if not tmp_dir:
            try:
                appname = cls.APP_NAME
            except AttributeError:
                appname = 'PyRandyOSApp'

            tmp_dir = Path(gettempdir())/appname
            if cls.global_config:
                cls.set(TMP_DIR_KEY, tmp_dir)

        if name:
            tmp_dir = tmp_dir/name

        mkdir_chgrp(tmp_dir, group, mode)
        return tmp_dir

    @classmethod
    @log_func_call
    def get_package_version(cls):
        return getattr(top_module_and_name(cls)[0], '__version__')

    @classmethod
    @log_func_call
    def get_package_dir(cls):
        return top_package_dir_path(cls)

    @classmethod
    @log_func_call
    def get_assets_dir(cls):
        assetsdir = cls.get(APP_ASSETS_DIR_KEY, cls.APP_ASSETS_DIR)
        if assetsdir:
            return Path(assetsdir)

    @classmethod
    @log_func_call(DEBUGLOW2)
    def get_default_win_size(cls):
        return (cls[f'{LOCAL_CFG_KEY}.default_width'],
                cls[f'{LOCAL_CFG_KEY}.default_height'])

    @classmethod
    @log_func_call(DEBUGLOW2)
    def get_local_config(cls, case_insensitive: bool = None):
        return super().get_local_config(case_insensitive=case_insensitive)

    @classmethod
    @log_func_call
    def save_local_config(cls, case_insensitive: bool = None):
        return super().save_local_config(cls.APP_PATH_KEYS, case_insensitive)
