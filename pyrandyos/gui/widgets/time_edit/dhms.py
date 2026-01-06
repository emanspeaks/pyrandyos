from ...qt import Qt, QKeyEvent
from .. import GuiWidgetParentType
from .base_edit import BaseTimeEditorWidget
from .fields import DaysField, SignField, make_time_fields


class DhmsWidget(BaseTimeEditorWidget):
    "Custom DHMS widget with block cursor and overtype behavior"

    def __init__(self, gui_parent: GuiWidgetParentType = None,
                 d: int = 0, h: int = 0, m: int = 0, s: int = 0,
                 sign: int = 1, *qtobj_args, **qtobj_kwargs):
        super().__init__(gui_parent, *qtobj_args, **qtobj_kwargs)
        self.set_fields(SignField(), DaysField(), '/ ',
                        *make_time_fields(False))
        (self.sign, self.d, _,
         self.h, _, self.m, _, self.s, _, self.ms) = self.fields
        self.set_dhms(d, h, m, s, sign)

    def get_dhms(self):
        """Get current DHMS values"""
        return (
            self.d.value,
            self.h.value,
            self.m.value,
            self.s.value + self.ms.value/1000,
            self.sign.value
        )

    def set_dhms(self, d: int, h: int, m: int, s: float, sign: int):
        """Set DHMS values"""
        s_int, ms = divmod(s, 1)
        self.d.set_value(d)
        self.h.set_value(h)
        self.m.set_value(m)
        self.s.set_value(int(s_int))
        self.ms.set_value(int(ms*1000))
        self.sign.set_value(sign)

    def set_sign(self, minus: bool):
        """Set sign (True for negative, False for positive)"""
        self.sign.set_value(1 - 2*minus)

    def get_title(self):
        return 'DHMS'

    def get_tooltip(self):
        return (
            "Overtype mode for all fields except spaces before/after days.\n"
            "+ or - — set sign\n"
            "Days: cursor in blank spaces insert/append more digits.\n"
            "/ or . — advance from days to time\n"
            "Red highlighting — invalid value\n"
            "PgDn or Left — move cursor left\n"
            "PgUp or Right — move cursor right\n"
            "Up or Down — increment/decrement field\n"
            "Ctrl+Up or Ctrl+Down — increment/decrement digit"
        )

    def handle_sign_keys(self, event: QKeyEvent):
        """Handle +/- keys to set sign"""
        key = event.key()

        if key == Qt.Key_Plus:
            f = self.get_current_field()
            if f is self.sign:
                f.write('+')

            else:
                self.set_sign(False)

            return True
        elif key == Qt.Key_Minus:
            f = self.get_current_field()
            if f is self.sign:
                f.write('-')

            else:
                self.set_sign(True)
            return True
        return False

    def handle_field_navigation_keys(self, event: QKeyEvent):
        """Handle field navigation with / or ."""
        key = event.key()

        # Handle field navigation with / or .
        # Only advance from days field with slash/period
        if key in (Qt.Key_Slash, Qt.Key_Period):
            f = self.get_current_field()
            if f is self.d:
                self.advance_to_next_field()

            # In time fields, these keys do nothing
            return True

        return False
