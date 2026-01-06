from ...logging import log_func_call, DEBUGLOW2
from ..qt import (
    QSyntaxHighlighter, QTextCharFormat, QColor, QFont, QRegularExpression,
    QPlainTextEdit,
)
from . import QtWidgetWrapper, GuiWidgetParentType


class JsonHighlighter(QSyntaxHighlighter):
    @log_func_call(DEBUGLOW2)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rules: list[tuple[QRegularExpression, QTextCharFormat]] = list()

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

        return editor

    @log_func_call
    def set_text(self, txt: str):
        self.qtobj.setPlainText(txt)

    @log_func_call
    def get_text(self):
        return self.qtobj.toPlainText()
