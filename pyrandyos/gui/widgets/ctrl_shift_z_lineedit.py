from ..qt import (
    QLineEdit, QKeyEvent, Qt, QEvent, QShortcut, QKeySequence,
)


class CtrlShiftZLineEdit(QLineEdit):
    def __init__(self, block_ctrl_y: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__['block_ctrl_y'] = block_ctrl_y

    def event(self, event: QEvent):
        if event.type() == QEvent.KeyPress:
            key_event = event
            key = key_event.key()
            mods = key_event.modifiers()
            ctrl = Qt.ControlModifier

            if self.block_ctrl_y and mods == ctrl and key == Qt.Key_Y:
                for shortcut in self.window().findChildren(QShortcut):
                    if shortcut.key() == QKeySequence("Ctrl+Y"):
                        shortcut.activated.emit()
                        return True
                return False

        return super().event(event)

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        mods = event.modifiers()
        ctrl = Qt.ControlModifier
        ctrlshift = ctrl | Qt.ShiftModifier
        is_ctrlshift = mods == ctrlshift

        if is_ctrlshift and key == Qt.Key_Z:
            # Handle Ctrl+Shift+Z here
            self.redo()
            return

        return super().keyPressEvent(event)
