"""
This module is intended for internal use only.  No user documentation is
provided at this time.  Use at your own discretion.
"""
from pathlib import Path
from shutil import chown
from datetime import datetime
from logging import (
    LogRecord, basicConfig, DEBUG, INFO, StreamHandler, Formatter, getLogger,
    CRITICAL, ERROR, WARNING, FileHandler, Logger, addLevelName,
    Handler,
)
from logging.handlers import MemoryHandler

from ..logging import (
    DEBUGLOW2, log_func_call, LOGSTDOUT, LOGSTDERR, LOGTQDM,
    APP_LOG_LEVEL_NAMES, get_loglevel_num_name
)
from .constants import DEFAULT_GROUP, DEFAULT_DIR_MODE
from .constants.cli import ConsoleText

_LOGCACHE: MemoryHandler = None


class MillisecondFormatter(Formatter):
    default_msec_format = '%s.%03d'


class LogMultiFormatter(Formatter):
    def __init__(self, fmtdict: dict[str | int, Formatter], **kwargs):
        super().__init__(**kwargs)
        self.fmtdict = fmtdict

    def format(self, record: LogRecord):
        return self.fmtdict.get(record.levelno,
                                self.fmtdict['DEFAULT']).format(record)


class LevelFilter:
    def __init__(self, level: int):
        self.__level = level

    def filter(self, record: LogRecord):
        return record.levelno >= self.__level


# debugfmtstr = '%(asctime)s::%(name)s::%(pathname)s::%(funcName)s(%(lineno)d)::%(levelname)s::%(message)s'  # noqa: E501
debugfmtstr = '%(asctime)s | %(levelname)s | %(pathname)s(%(lineno)d) | %(funcName)s | %(message)s'  # noqa: E501
debug_ms_fmt = MillisecondFormatter(debugfmtstr)
simple_color_fmt = LogMultiFormatter({
    INFO: MillisecondFormatter(ConsoleText.GreenText
                               + "%(message)s"
                               + ConsoleText.Reset),
    LOGSTDOUT: MillisecondFormatter(ConsoleText.WhiteText
                                    + "%(message)s"
                                    + ConsoleText.Reset),
    LOGSTDERR: MillisecondFormatter(ConsoleText.CyanText
                                    + "%(message)s"
                                    + ConsoleText.Reset),
    LOGTQDM: MillisecondFormatter(ConsoleText.BlueText
                                  + "%(message)s"
                                  + ConsoleText.Reset),
    WARNING: MillisecondFormatter(ConsoleText.YellowText
                                  + "%(asctime)s %(levelname)s: %(message)s"
                                  + ConsoleText.Reset),
    ERROR: MillisecondFormatter(ConsoleText.RedText
                                + "%(asctime)s %(levelname)s: %(message)s"
                                + ConsoleText.Reset),
    CRITICAL: MillisecondFormatter(ConsoleText.MagentaText
                                   + "%(asctime)s %(levelname)s: %(message)s"
                                   + ConsoleText.Reset),
    'DEFAULT': MillisecondFormatter("%(asctime)s %(levelname)s: %(message)s"),
})


@log_func_call
def create_cli_log_handler(level: int | str = INFO,
                           fmt: Formatter = simple_color_fmt):
    if isinstance(level, str):
        level = level.upper()

    clilog = StreamHandler()
    check_loglevel(level)
    clilog.setLevel(level)
    clilog.setFormatter(fmt)
    return clilog


@log_func_call
def create_file_log_handler(logfile: Path, level: int | str = DEBUG,
                            fmt: Formatter = debug_ms_fmt):
    if isinstance(level, str):
        level = level.upper()

    # filelog = FileHandler(logfile, errors='backslashreplace')
    filelog = FileHandler(logfile, encoding='utf-8', errors='backslashreplace')
    check_loglevel(level)
    filelog.setLevel(level)
    filelog.setFormatter(fmt)
    return filelog


@log_func_call
def create_memory_log_handler(buffer: int = 1024, level: int | str = 0,
                              fmt: Formatter = debug_ms_fmt):
    if isinstance(level, str):
        level = level.upper()

    memlog = MemoryHandler(buffer)
    check_loglevel(level)
    memlog.setLevel(level)
    memlog.setFormatter(fmt)
    return memlog


@log_func_call
def setup_memory_logging(cli_log_level: int | str = INFO,
                         force: bool = False, cli: bool = True,
                         logger: Logger = None):
    global _LOGCACHE
    _LOGCACHE = create_memory_log_handler()
    handlers = [_LOGCACHE]
    if cli:
        handlers.append(create_cli_log_handler(cli_log_level))
    basicConfig(force=force, level=0, handlers=handlers)
    log = logger or getLogger(__name__)
    log.debug('setup_memory_logging complete')


@log_func_call
def setup_logging(logfile: Path = None, cli_log_level: int | str = INFO,
                  file_log_level: int | str = DEBUG,
                  force: bool = True, cli: bool = True,
                  logger: Logger = None):
    global _LOGCACHE
    handlers: list[Handler] = list()
    filt = None
    if logger:
        if _LOGCACHE:
            for h in logger.handlers:
                if isinstance(h, FileHandler):
                    _LOGCACHE.setTarget(h)
                    filt = LevelFilter(h.level)
                    h.addFilter(filt)
                    _LOGCACHE.flush()
                    # h.removeFilter(filt)
                    break
    elif logfile:
        filelog: FileHandler = create_file_log_handler(logfile, file_log_level)
        handlers.append(filelog)
        if _LOGCACHE:
            _LOGCACHE.setTarget(filelog)
            filt = LevelFilter(filelog.level)
            filelog.addFilter(filt)
            _LOGCACHE.flush()
            # filelog.removeFilter(filt)

    if cli:
        handlers.append(create_cli_log_handler(cli_log_level))

    if handlers:
        basicConfig(force=force, level=0, handlers=handlers)

    if _LOGCACHE:
        _LOGCACHE.flush()
        if filt:
            for h in handlers:
                h.removeFilter(filt)

        _LOGCACHE = None

    log = logger or getLogger(__name__)
    log.debug('setup_logging complete')


@log_func_call(DEBUGLOW2)
def is_valid_loglevel(level: str | int):
    if isinstance(level, int):
        return True
    try:
        _, name = get_loglevel_num_name(level)
    except ValueError:
        return False
    return name is not None


@log_func_call(DEBUGLOW2)
def add_loglevel_name(logname: str, loglevel: str | int):
    num, name = get_loglevel_num_name(loglevel)
    if name is None:
        addLevelName(num, logname)


@log_func_call(DEBUGLOW2)
def check_loglevel(level: str | int):
    if is_valid_loglevel(level):
        return
    level = level.upper()
    if level not in APP_LOG_LEVEL_NAMES:
        raise ValueError(f'unknown loglevel string {level} given')
    add_loglevel_name(level, APP_LOG_LEVEL_NAMES[level])


for k in APP_LOG_LEVEL_NAMES.keys():
    check_loglevel(k)


@log_func_call
def create_log_file(logdir: Path, timestamp_name: bool = True,
                    append: bool = False, prefix: str = 'log',
                    group: str = DEFAULT_GROUP, mode: int = DEFAULT_DIR_MODE,
                    suffix: str = '.log'):
    logdir.mkdir(exist_ok=True, parents=True, mode=mode)
    if group:
        chown(logdir, group=group)

    stem = prefix
    if timestamp_name:
        now_ymdhms = datetime.now().timetuple()[:6]
        y = f"{now_ymdhms[0]:04}"
        mon = f"{now_ymdhms[1]:02}"
        d = f"{now_ymdhms[2]:02}"
        h = f"{now_ymdhms[3]:02}"
        m = f"{now_ymdhms[4]:02}"
        s = f"{now_ymdhms[5]:02.0f}"
        stem = f'{stem}_{y}{mon}{d}T{h}{m}{s}'

    logfile = logdir/f'{stem}{suffix}'
    if not append:
        logfile.write_text('')

    return logfile
