import sys
from types import TracebackType

from ..logging import log_func_call, log_exc, log_debug, log_info
from .._testing.debug import is_debug_enabled
from .log import setup_memory_logging
from .stack import exc_info


class MainContext:
    """
    Context manager for the main application context.
    It sets up logging and handles exceptions.
    """

    @log_func_call
    def __init__(self, appname: str):
        self.appname = appname

    @log_func_call
    def __enter__(self):
        try:
            setup_memory_logging()
            log_debug(f"starting {self.appname} main")
        except BaseException as e:
            self.__exit__(*exc_info(exc=e))

        return self

    @log_func_call
    def __exit__(self, exc_type: type = None, exc: BaseException = None,
                 traceback: TracebackType = None):
        exit_code = exc.code if isinstance(exc, SystemExit) else 0
        status_ok = True
        try:
            if exc:
                if not isinstance(exc, (SystemExit, KeyboardInterrupt)):
                    status_ok = False
                    exit_code = 1
                    log_exc(exc_type, exc, traceback)

                    # if there is a splash screen, kill it
                    try:
                        from ..gui.gui_app import get_gui_app
                        gui_app = get_gui_app()
                        if gui_app:
                            gui_app.splash.gui_view.qtobj.hide()

                    except BaseException:
                        pass

                if is_debug_enabled():
                    # this triggers the debugger to break on the exception
                    raise exc

        finally:
            appname = self.appname
            if exit_code:
                log_info(f'{appname} exited with code {exit_code}')

            if status_ok:
                log_info(f'{appname} exiting gracefully')
            else:
                pass

            if not is_debug_enabled():
                # if running in the debugger, we don't want to catch the
                # SystemExit so we can see the traceback in the console more
                # clearly. However, this means that the debugger will always
                # exit with code 1 if an unhandled exception, even if we
                # specify a different exit code above since we only call
                # sys.exit(exit_code) here in the case where the debugger is
                # not enabled.  Ideally, we would set the exit code in the
                # debugger as well, but that is not possible with the current
                # setup without modifying the launch configuration.  I prefer
                # to keep this simple and rely on the log messages below to
                # indicate the "true" exit code when running in the debugger.
                sys.exit(exit_code)
