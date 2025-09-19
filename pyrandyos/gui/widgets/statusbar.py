from pathlib import Path
from logging import Handler, Formatter, LogRecord
from collections.abc import Callable
from functools import partial

from ...app import PyRandyOSApp
from ...logging import (
    INFO, LOGSTDERR, LOGSTDOUT, LOGTQDM, WARNING, ERROR, CRITICAL, DEBUG,
    log_func_call, get_logger, get_loglevel_num_name, make_log_record,
    log_debuglow2, log_debug,
)
from ...utils.log import (
    check_loglevel, MillisecondFormatter, LogMultiFormatter,
)
from ...config.keys import BASE_LOG_PATH_KEY
from ..qt import (
    QStatusBar, QLabel, QMainWindow, Qt, QMouseEvent, QPoint, QMenu,
)
from ..callback import qt_callback
from ..gui_app import get_gui_app
from ..dialogs.log import LogDialog
from . import QtWidgetWrapper, GuiWindowLikeParentType

StatusMsgStyleDict = dict[str | int, str]
StatusMsgClearDict = dict[str | int, bool]

DEFAULT_STATUSMSG_STYLES: StatusMsgStyleDict = {
    DEBUG: "background-color: blue; color: white;",
    # INFO: "background-color: green; color: white;",
    WARNING: "background-color: yellow; color: black;",
    ERROR: "background-color: red; color: white;",
    CRITICAL: "background-color: magenta; color: black; font-weight: bold;",
}

DEFAULT_STATUSMSG_CLEAR: StatusMsgClearDict = {
    DEBUG: False,
    INFO: True,
    WARNING: True,
    ERROR: True,
    CRITICAL: True,
}

DEFAULT_STATUSMSG_FMT = LogMultiFormatter({
    INFO: MillisecondFormatter("%(message)s"),
    'DEFAULT': MillisecondFormatter("%(levelname)s: %(message)s"),
})


class StatusMsgLogFilter:
    def filter(self, record: LogRecord):
        return record.levelno not in (LOGSTDERR, LOGSTDOUT, LOGTQDM)


class StatusMsgLogHandler(Handler):
    def __init__(self, lbl: QLabel, level: int = 0,
                 style_dict: StatusMsgStyleDict = DEFAULT_STATUSMSG_STYLES,
                 clear_prev_message_callback: callable = None,
                 clear_dict: StatusMsgClearDict = DEFAULT_STATUSMSG_CLEAR,
                 reset_style_callback: Callable = None,
                 max_lines: int = 3):
        super().__init__(level)
        self.lbl = lbl
        self.reset_style_callback = reset_style_callback
        self.style_dict = style_dict
        self.clear_prev_message_callback = clear_prev_message_callback
        self.clear_dict = clear_dict
        self.max_lines = max_lines
        self.last_msg = None

    # def flush(self):
    #     """
    #     Flushes the stream.
    #     """
    #     self.acquire()
    #     try:
    #         if self.stream and hasattr(self.stream, "flush"):
    #             self.stream.flush()
    #     finally:
    #         self.release()

    def update_label(self, msg_or_record: str | LogRecord = None,
                     level: int | str = INFO, clear: bool = False,
                     get_last: bool = False):
        last_msg = self.last_msg
        get_last_only = get_last and not msg_or_record and not clear
        if get_last_only:
            return last_msg

        if msg_or_record:
            record = (msg_or_record if isinstance(msg_or_record, LogRecord)
                      else make_log_record(level, msg_or_record))
            msg = self.format(record)
        else:
            clear = clear or not get_last
            record = None
            msg = ""

        clearcb = self.clear_prev_message_callback
        if clearcb and clear or (record and self.check_level_clear(record)):
            clearcb()

        self.update_status_style(record)
        if msg:
            lines = msg.splitlines()
            self.lbl.setText('\n'.join(lines[:self.max_lines]))
        else:
            self.lbl.clear()

        get_gui_app().process_events()
        self.last_msg = msg
        if get_last:
            return last_msg

    def emit(self, record: LogRecord):
        """
        Emit a record.

        If a formatter is specified, it is used to format the record.
        The record is then written to the stream with a trailing newline.  If
        exception information is present, it is formatted using
        traceback.print_exception and appended to the stream.  If the stream
        has an 'encoding' attribute, it is used to determine how to do the
        output to the stream.
        """
        try:
            self.update_label(record)
        except RecursionError:  # See issue 36272
            raise
        except Exception:
            self.handleError(record)

    def check_level_clear(self, record: LogRecord):
        return (self.clear_dict.get(record.levelno, False) if self.clear_dict
                else False)

    def update_status_style(self, record: LogRecord = None):
        style = self.style_dict.get(record.levelno, None) if record else None
        lbl = self.lbl
        ss = f"QLabel {{ {style} }}" if style else ""
        cb = self.reset_style_callback
        if style or not cb:
            lbl.setStyleSheet(ss)
        else:
            cb()


class LoggingStatusBarWidget(QtWidgetWrapper[QStatusBar]):
    @log_func_call
    def __init__(self, parent: GuiWindowLikeParentType):  # , *qtobj_args):
        self._log_dialog: LogDialog = None
        super().__init__(parent)  # , *qtobj_args)

    @log_func_call
    def create_qtobj(self):  # , *qtobj_args):
        qtwin: QMainWindow = self.gui_parent.qtobj

        statusbar = QStatusBar(qtwin)
        qtwin.setStatusBar(statusbar)
        self.status_bar = statusbar

        status_msg_lbl = QLabel(statusbar)
        status_msg_lbl.mousePressEvent = self.click_status_msg
        statusbar.addWidget(status_msg_lbl, 1)
        self.status_msg_lbl = status_msg_lbl

        # Set up context menu for right-click
        status_msg_lbl.setContextMenuPolicy(Qt.CustomContextMenu)
        status_context_signal = status_msg_lbl.customContextMenuRequested
        status_context_signal.connect(
            qt_callback(self.show_status_context_menu))

        level = PyRandyOSApp.get('statusbar_log_level', INFO)
        msglog = self.add_statusmsg_log_handler(level, statusbar.clearMessage)
        updater = msglog.update_label
        self.status_msg_updater = updater
        updater('Ready')

        return statusbar

    @log_func_call
    def add_statusmsg_log_handler(
        self,
        level: int | str = INFO,
        clear_prev_message_callback: Callable = None,
        fmt: Formatter = DEFAULT_STATUSMSG_FMT,
        style_dict: StatusMsgStyleDict = DEFAULT_STATUSMSG_STYLES,
        reset_style_callback: Callable = None,
        clear_dict: StatusMsgClearDict = DEFAULT_STATUSMSG_CLEAR,
    ):
        lbl = self.status_msg_lbl
        check_loglevel(level)
        lnum, _ = get_loglevel_num_name(level)
        msglog = StatusMsgLogHandler(lbl, lnum, style_dict,
                                     clear_prev_message_callback, clear_dict,
                                     reset_style_callback)
        msglog.setFormatter(fmt)
        msglog.addFilter(StatusMsgLogFilter())
        get_logger().root.addHandler(msglog)
        return msglog

    @log_func_call
    def update_status_bar_msg(self, msg: str, level: int | str = INFO,
                              temp: bool = False, timeout_ms: int = 0):
        if temp:
            bar = self.status_bar
            bar.showMessage(msg, timeout_ms)
        else:
            self.status_msg_updater(msg, level)

    @log_func_call
    def clear_status_message(self):
        """Clear the status bar message."""
        self.status_bar.clearMessage()
        self.status_msg_updater()
        log_debuglow2("Status message cleared")

    @log_func_call
    def copy_status_message(self, msg: str):
        """Copy the current status message to clipboard."""
        if msg:
            get_gui_app().qtobj.clipboard().setText(msg)
            log_debug(f"Status message copied: {msg}")

    @log_func_call
    def click_status_msg(self, event: QMouseEvent = None):
        if not event or event.button() == Qt.LeftButton:
            self.show_log_dialog()

    @log_func_call
    def get_log_path(self):
        logpath = PyRandyOSApp.get(BASE_LOG_PATH_KEY, None)
        return Path(logpath) if logpath else None

    @log_func_call
    def show_log_dialog(self, log_path: Path = None):
        log_path = log_path or self.get_log_path()
        if log_path:
            # Close existing dialog if open
            dialog = self._log_dialog
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
    def get_current_status_msg(self):
        return (self.status_bar.currentMessage()
                or self.status_msg_updater(get_last=True))

    @log_func_call
    def show_status_context_menu(self, position: QPoint):
        """Show context menu for status bar message label."""
        pres = self.gui_pres
        msg = pres.get_current_status_msg()

        menu = QMenu()
        if msg:
            clear = menu.addAction("Clear Message")
            clear.triggered.connect(qt_callback(pres.clear_status_message))
            copy = menu.addAction("Copy Message")
            copy.triggered.connect(
                qt_callback(partial(pres.copy_status_message, msg)))
            menu.addSeparator()

        logpath = pres.get_log_path()
        logexists = logpath and logpath.exists()
        status_dialog = menu.addAction("Show Log History Dialog")
        status_dialog.triggered.connect(
            qt_callback(partial(pres.show_log_dialog, logpath)))
        status_dialog.setEnabled(logexists)

        # Show menu at the requested position
        menu.exec_(self.status_msg_lbl.mapToGlobal(position))
