from pathlib import Path

from ....app import PyRandyOSApp
from ....config.keys import BASE_LOG_PATH_KEY
from ....logging import log_func_call

from .pres import LogDialog


class LogDialogMainWindowMixin:
    @log_func_call
    def show_log_dialog(self, log_path: Path = None):
        log_path = log_path or self.get_log_path()
        if log_path:
            # Close existing dialog if open
            dialog: LogDialog = self._log_dialog
            if dialog:
                try:
                    dialog.gui_view.qtobj.close()
                except RuntimeError:
                    # Dialog was already closed/destroyed
                    pass

            # Create and show new dialog
            dialog = LogDialog(self, log_path)
            self._log_dialog = dialog
            dialog.show()

    @log_func_call
    def get_log_path(self):
        logpath = PyRandyOSApp.get(BASE_LOG_PATH_KEY, None)
        return Path(logpath) if logpath else None
