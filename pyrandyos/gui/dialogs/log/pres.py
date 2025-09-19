from pathlib import Path
from functools import partial

from ....logging import log_func_call, DEBUG
from ...widgets import GuiWindowLikeParentType
from ...qt import Qt, QHeaderView  # , QRect  # , QFontMetrics
from ...gui_app import get_gui_app
from ...utils import (
    wrap_text_to_width, get_table_item_text_bbox, get_table_item_usable_rect,
    # test_width_calc,  # get_styled_text_bbox,
)
from .. import GuiDialog
from .view import LogDialogView, TABLE_VPAD

LOG_DELIM = ' | '
UserRole = Qt.UserRole
Stretch = QHeaderView.Stretch
ResizeToContents = QHeaderView.ResizeToContents
TextWordWrap = Qt.TextWordWrap


class LogDialog(GuiDialog[LogDialogView]):
    @log_func_call
    def __init__(self, gui_parent: GuiWindowLikeParentType, log_path: Path):
        self.log_path = log_path  # set this before init so the view has it
        super().__init__(f"Log History - {log_path.as_posix()}", gui_parent)
        if self.gui_view.log_table:
            self.update_row_heights()

    @log_func_call
    def show(self):
        dialog = self.gui_view.qtobj

        # Show and raise the dialog
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    @log_func_call
    def create_gui_view(self, basetitle: str, *args,
                        **kwargs) -> LogDialogView:
        return LogDialogView(basetitle, self, *args, **kwargs)

    @log_func_call
    def parse_log_file(self):
        txt = self.log_path.read_text()
        lines = txt.splitlines()
        firstline = lines[0] if lines else ""
        parts = firstline.split(LOG_DELIM)
        if len(parts) == 5:
            timestamp = list()
            level = list()
            file = list()
            func = list()
            msg = list()

            for line in lines:
                parts = line.split(LOG_DELIM)
                if len(parts) == 5:
                    timestamp.append(parts[0])
                    level.append(parts[1])
                    file.append(parts[2])
                    func.append(parts[3])
                    msg.append(parts[4])
                else:
                    msg[-1] += "\n" + line

            return timestamp, level, file, func, msg
        return txt

    @log_func_call
    def row_header_clicked(self, row: int) -> None:
        """
        Called when a row header is clicked. Copies the reconstructed
        original log line to the clipboard.
        """
        table = self.gui_view.log_table
        log_line = LOG_DELIM.join(table.item(row, col).data(UserRole)
                                  for col in range(table.columnCount()))
        get_gui_app().qtobj.clipboard().setText(log_line)

    @log_func_call(DEBUG)
    def update_row_heights(self, logical_index: int = None,
                           old_width: int = None,
                           new_width: int = None):
        """
        Calculate and set appropriate row heights based on content and
        column widths.
        """
        table = self.gui_view.log_table
        header = table.horizontalHeader()
        vheader = table.verticalHeader()
        ncols = table.columnCount()
        modes = [header.sectionResizeMode(col) for col in range(ncols)]
        if header.stretchLastSection():
            modes[-1] = Stretch

        # widths = [table.columnWidth(col) for col in range(ncols)]
        # if logical_index is not None:
        #     widths[logical_index] = new_size

        for row in range(table.rowCount()):
            max_row_height = 0
            for col in range(ncols):
                item = table.item(row, col)
                text: str = item.data(UserRole)
                # font = item.font()
                # fmetrics = QFontMetrics(font, table)
                # bboxcalc = partial(get_styled_text_bbox, table, font)
                bboxcalc = partial(get_table_item_text_bbox, table, item)
                textrect = get_table_item_usable_rect(table, item)
                # usable_width = widths[col] - TABLE_HPAD
                usable_width = textrect.width()
                if logical_index is not None and col == logical_index:
                    margin = old_width - usable_width
                    usable_width = new_width - margin  # - TABLE_HPAD

                if modes[col] != ResizeToContents:
                    # lineWidth, widthUsed = test_width_calc(table, item,
                    #                                        widths[col], text)
                    text = wrap_text_to_width(text, bboxcalc, usable_width)

                item.setText(text)
                # nlines = 1 + text.count('\n')
                # lineheight = bboxcalc(text).height()
                # box = QRect(0, 0, usable_width, lineheight*nlines)
                box = bboxcalc(text)
                row_height = max(vheader.minimumHeight(),
                                 box.height() + TABLE_VPAD)
                max_row_height = max(max_row_height, row_height)

            table.setRowHeight(row, max_row_height)
