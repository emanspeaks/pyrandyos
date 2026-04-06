from ...logging import log_func_call, DEBUGLOW2
from ..callback import qt_callback
from ..qt import (
    QSyntaxHighlighter, QTextCharFormat, QColor, QFont, QRegularExpression,
    QPlainTextEdit, QShortcut, QKeySequence, Qt, QInputDialog, QTextCursor,
)
from . import QtWidgetWrapper, GuiWidgetParentType


class JsonHighlighter(QSyntaxHighlighter):
    @log_func_call(DEBUGLOW2)
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.rules = list()  # this causes Qt to crash
        self.__dict__['rules'] = list()
        self.rules: list[tuple[QRegularExpression, QTextCharFormat]]

        # Define styles
        key_format = QTextCharFormat()
        key_format.setForeground(QColor("#ce9178"))
        key_format.setFontWeight(QFont.Bold)
        key_regex = QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"\s*(?=:)')

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#9cdcfe"))
        string_regex = QRegularExpression(r'(?<=:)\s*"[^"\\]*(\\.[^"\\]*)*"')

        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8"))
        number_regex = QRegularExpression(r'\b-?\d+(\.\d+)?([eE][+-]?\d+)?\b')

        boolean_format = QTextCharFormat()
        boolean_format.setForeground(QColor("#569cd6"))
        boolean_regex = QRegularExpression(r'\b(true|false|null)\b')

        self.rules.append((key_regex, key_format))
        self.rules.append((string_regex, string_format))
        self.rules.append((number_regex, number_format))
        self.rules.append((boolean_regex, boolean_format))

    @log_func_call(DEBUGLOW2)
    def highlightBlock(self, text):
        for pattern, format in self.rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(),
                               match.capturedLength(), format)


class JsonEditorWidget(QtWidgetWrapper[QPlainTextEdit]):
    @log_func_call
    def create_qtobj(self):
        parent_qtobj: GuiWidgetParentType = self.gui_parent.qtobj

        editor = QPlainTextEdit(parent_qtobj)
        font = self.gui_app.get_monofont()
        font.setPointSize(10)
        editor.setFont(font)
        self.editor = editor

        highlighter = JsonHighlighter(editor.document())
        self.highlighter = highlighter

        # Add Ctrl+F shortcut for find
        find_shortcut = QShortcut(QKeySequence(Qt.CTRL + Qt.Key_F), editor)
        find_shortcut.activated.connect(qt_callback(self.show_find_dialog))
        self.find_shortcut = find_shortcut

        # Add F3 shortcut for find next
        find_next_shortcut = QShortcut(QKeySequence(Qt.Key_F3), editor)
        find_next_shortcut.activated.connect(qt_callback(self.find_next))
        self.find_next_shortcut = find_next_shortcut

        # Track last search term for "Find Next"
        self.last_search_term = ""

        return editor

    @log_func_call
    def set_text(self, txt: str):
        self.qtobj.setPlainText(txt)

    @log_func_call
    def get_text(self):
        return self.qtobj.toPlainText()

    @log_func_call
    def show_find_dialog(self):
        """Show a find dialog and search for text in the editor."""
        editor = self.qtobj

        # Get search text from user
        text, ok = QInputDialog.getText(
            editor,
            "Find",
            "Search for:",
            text=self.last_search_term
        )

        if ok and text:
            self.last_search_term = text
            # Move cursor to start of document for fresh search
            cursor = editor.textCursor()
            cursor.movePosition(QTextCursor.Start)
            editor.setTextCursor(cursor)

            # Search for the text
            if not editor.find(text):
                # If not found from current position, try from beginning
                cursor.movePosition(QTextCursor.Start)
                editor.setTextCursor(cursor)
                if not editor.find(text):
                    # Still not found - could show a message here
                    pass

    @log_func_call
    def find_next(self):
        """Find the next occurrence of the last search term."""
        if self.last_search_term:
            editor = self.qtobj
            if not editor.find(self.last_search_term):
                # Wrap around to beginning if not found
                cursor = editor.textCursor()
                cursor.movePosition(QTextCursor.Start)
                editor.setTextCursor(cursor)
                editor.find(self.last_search_term)
        else:
            # No previous search, show the find dialog
            self.show_find_dialog()
