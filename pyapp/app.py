import sys
from pathlib import Path

from .logging import get_logger, Logger, log_func_call
from .config import AppConfig
from .config.defaults import (
    BASE_LOG_PATH_KEY, APP_NAME_KEY, get_log_dir_keys, APP_PKG_DIR_KEY,
    APP_ASSETS_DIR_KEY,
)
from .config.local import process_local_config

from .utils.constants import DEFAULT_GROUP, DEFAULT_DIR_MODE
from .utils.logging import setup_logging, create_log_file
from .utils.main import main_context
from .utils.system import (
    mkdir_chgrp, get_top_package_dir_for_obj
)


class PyApp(AppConfig):
    # abstract class attributes
    APP_NAME: str
    APP_LOG_PREFIX: str
    APP_PATH_KEYS: tuple[str]
    APP_LOG_DIR_KEYS: tuple[str]

    # class attributes with fallback defaults
    APP_GLOBAL_DEFAULTS = {}
    APP_LOCAL_DEFAULTS = {}
    APP_ASSETS_DIR: Path = None
    APP_PKG_DIR: Path = None

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
        log = logger or get_logger()
        cls.set_logger(log)
        cls.init_parse_config(config, kwargs)

        # setup logging first if necessary:
        if setup_log:
            if not logfile:
                logcfg = cls.expand_log_config()
                logdir, ts_name, append, cli_log_level, file_log_level = logcfg
                logfile = create_log_file(logdir, ts_name, append,
                                          cls.APP_LOG_PREFIX)

            setup_logging(logfile, cli_log_level, file_log_level)

        # start logging and process the rest of the configuration data
        cls.set(BASE_LOG_PATH_KEY, logfile)
        pkgdir = cls.get_package_dir()
        cls.set(APP_PKG_DIR_KEY, pkgdir)
        assets_dir = cls.get_assets_dir()
        if assets_dir:
            cls.set(APP_ASSETS_DIR_KEY, assets_dir)

        appname = cls.APP_NAME
        cls.set(APP_NAME_KEY, appname)
        log.info(f"Starting {appname}")
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
                          overrides: dict = None, defaults: dict = None):
        global_defaults = dict()
        global_defaults.update(cls.APP_GLOBAL_DEFAULTS)
        return super().init_parse_config(indata, overrides, defaults,
                                         global_defaults,
                                         cls.APP_LOCAL_DEFAULTS)

    @classmethod
    @log_func_call
    def run_cmdline(cls, args: list[str] = None):
        if args is None:
            args = sys.argv[1:]

        with main_context(cls.APP_NAME):
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
        # log = get_logger()
        # log.debug('in create_log_dirs')
        for key in get_log_dir_keys(cls.APP_LOG_DIR_KEYS):
            p: Path = cls.get(key)
            mkdir_chgrp(p, group, mode)

    @classmethod
    @log_func_call
    def mkdir_temp(cls, name: str = None, group: str = DEFAULT_GROUP,
                   mode: int = DEFAULT_DIR_MODE):
        # log = get_logger()
        # log.debug('in mkdir_temp')
        tmp_dir: Path = cls.get('tmp_dir')
        if name:
            tmp_dir = tmp_dir/name

        mkdir_chgrp(tmp_dir, group, mode)
        return tmp_dir

    @classmethod
    @log_func_call
    def get_package_dir(cls):
        return (cls.APP_PKG_DIR
                or get_top_package_dir_for_obj(cls))

    @classmethod
    @log_func_call
    def get_assets_dir(cls):
        return cls.APP_ASSETS_DIR
