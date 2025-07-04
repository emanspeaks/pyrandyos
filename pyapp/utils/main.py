import sys
from contextlib import contextmanager

from ..logging import log_func_call, get_logger, log_exc
from .._testing.debug import is_debug_enabled
from .log import setup_memory_logging


@contextmanager
@log_func_call
def main_context(appname: str):
    status_ok = True
    log = get_logger()
    exit_code = 0
    try:
        setup_memory_logging()
        log.debug(f"starting {appname} main")
        yield
    except SystemExit as e:
        exit_code = e.code
        if not is_debug_enabled():
            raise e
    except KeyboardInterrupt:
        pass
    except BaseException as e:
        status_ok = False
        exit_code = 1
        log_exc(value=e)
        if is_debug_enabled():
            raise e

    finally:
        if exit_code:
            log.info(f'{appname} exited with code {exit_code}')

        if status_ok:
            log.info(f'{appname} exiting gracefully')
        else:
            pass

        if not is_debug_enabled():
            # if running in the debugger, we don't want to catch the SystemExit
            # so we can see the traceback in the console more clearly.
            # However, this means that the debugger will always exit with
            # code 1 if an unhandled exception, even if we specify a different
            # exit code above since we only call sys.exit(exit_code) here
            # in the case where the debugger is not enabled.
            # Ideally, we would set the exit code in the debugger as well,
            # but that is not possible with the current setup without modifying
            # the launch configuration.  I prefer to keep this simple and rely
            # on the log messages below to indicate the "true" exit code when
            # running in the debugger.
            sys.exit(exit_code)
