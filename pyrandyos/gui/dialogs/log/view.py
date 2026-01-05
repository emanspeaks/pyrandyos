from typing import TYPE_CHECKING

from ....logging import log_func_call
from ...qt import (
    QVBoxLayout, QDialogButtonBox, QTextEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, Qt,
)
from .. import GuiDialogView
from ...callback import qt_callback

if TYPE_CHECKING:
    from .pres import LogDialog

# Column definitions: (label, autofit)
LOG_COLS = [
    ("Timestamp", True),
    ("Level", True),
    ("File", True),
    ("Function", True),
    ("Message", False),
]

UserRole = Qt.UserRole

TABLE_TPAD = 2  # one sided
TABLE_LPAD = 4  # one sided
TABLE_VPAD = TABLE_TPAD*2  # two sided
TABLE_HPAD = TABLE_LPAD*2  # two sided
TABLE_CELL_STYLE = f"QTableWidget::item {{ padding: {TABLE_TPAD}px {TABLE_LPAD}px; }}"  # noqa: E501


class LogDialogView(GuiDialogView['LogDialog']):
    @log_func_call
    def __init__(self, basetitle: str, presenter: 'LogDialog' = None,
                 *qtobj_args, **qtobj_kwargs):
        GuiDialogView.__init__(self, basetitle, presenter, *qtobj_args,
                               **qtobj_kwargs)
        qtobj = self.qtobj
        qtobj.resize(1500, 600)
        self.layout = QVBoxLayout(qtobj)
        self.create_log_widget()

    @log_func_call
    def create_log_widget(self):
        __traceback_hide_locals__ = 'content'  # noqa: F841
        qtobj = self.qtobj
        layout = self.layout
        pres = self.gui_pres

        content = pres.parse_log_file()
        self.log_table = None
        if isinstance(content, str):
            # Create scrollable text widget for log content
            log_text = QTextEdit()
            log_text.setReadOnly(True)
            log_text.setLineWrapMode(QTextEdit.NoWrap)
            log_text.setPlainText(content)
            layout.addWidget(log_text)
            self.log_text = log_text

            # Scroll to bottom to show most recent entries
            cursor = log_text.textCursor()
            cursor.movePosition(cursor.End)
            log_text.setTextCursor(cursor)

        else:
            log_table = QTableWidget()
            layout.addWidget(log_table)
            self.log_table = log_table
            self.setup_log_table()
            # need to wait until after __init__ to update row heights
            self.populate_log_table(content, False)

        dlgbuttons = QDialogButtonBox(QDialogButtonBox.Ok, qtobj)
        dlgbuttons.accepted.connect(qtobj.accept)
        layout.addWidget(dlgbuttons)
        self.dlgbuttons = dlgbuttons

    @log_func_call
    def setup_log_table(self):
        pres = self.gui_pres
        table = self.log_table

        header = table.horizontalHeader()

        table.setColumnCount(len(LOG_COLS))
        for i, (label, autofit) in enumerate(LOG_COLS):
            item = QTableWidgetItem(label)
            table.setHorizontalHeaderItem(i, item)
            # if autofit:
            #     # Auto-resize to fit content for fixed columns
            #     header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
            # else:
            #     # Start with Stretch, will switch to Interactive
            #     header.setSectionResizeMode(i, QHeaderView.Stretch)

        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)
        # Add padding that works with stretch columns
        table.setStyleSheet(TABLE_CELL_STYLE)
        table.setSortingEnabled(False)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)  # Make readonly
        table.setWordWrap(True)
        table.setVerticalScrollMode(QTableWidget.ScrollPerPixel)
        table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)

        vheader = table.verticalHeader()
        # vheader.setDefaultSectionSize(20)
        # vheader.setMinimumSectionSize(20)
        # vheader.resizeSections(QHeaderView.ResizeToContents)
        vheader.setSectionResizeMode(QHeaderView.Fixed)
        vheader.sectionClicked.connect(qt_callback(pres.row_header_clicked))

        # don't do this yet because sorting later will trigger it
        # self.connect_column_resize_signal()

    @log_func_call
    def connect_column_resize_signal(self):
        header = self.log_table.horizontalHeader()
        cb = qt_callback(self.gui_pres.update_row_heights)
        header.sectionResized.connect(cb)

    @log_func_call
    def disconnect_column_resize_signal(self, raise_exc: bool = True):
        header = self.log_table.horizontalHeader()
        try:
            header.sectionResized.disconnect(self.gui_pres.update_row_heights)
        except RuntimeError:
            if raise_exc:
                raise

    @log_func_call
    def populate_log_table(self, content: tuple,
                           update_row_heights: bool = True):
        __traceback_hide_locals__ = ('content', 'col')  # noqa: F841
        # timestamps, levels, files, funcs, msgs = content
        table = self.log_table

        # disable resize signals while populating since sort will trigger
        self.disconnect_column_resize_signal(False)

        rowcount = len(content[0])
        table.setRowCount(rowcount)
        monofont = self.gui_app.get_monofont()
        for row in range(rowcount):
            # Create regular table items and store original text as user data
            for i, col in enumerate(content):
                x = col[row]
                item = QTableWidgetItem(x)
                item.setData(UserRole, x)
                # Apply monospace font to the message column (last column)
                if i == len(LOG_COLS) - 1:  # Message column
                    item.setFont(monofont)

                table.setItem(row, i, item)

        table.sortItems(0, Qt.DescendingOrder)

        # After populating data, ensure proper column sizing
        # header = table.horizontalHeader()
        # for i, (_, autofit) in enumerate(LOG_COLS):
        #     if not autofit:
        #         # For non-autofit columns (Message), ensure Interactive mode
        #         # and set a reasonable initial width if needed
        #         header.setSectionResizeMode(i, QHeaderView.Interactive)
        #         # if header.sectionSize(i) < 200:  # Min width for msg col
        #         #     header.resizeSection(i, 400)  # Set reasonable default

        # Update row heights after populating and setting up columns
        if update_row_heights:
            self.gui_pres.update_row_heights()

        # reconnect signal
        self.connect_column_resize_signal()
