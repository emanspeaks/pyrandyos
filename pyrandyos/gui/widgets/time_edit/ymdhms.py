from .. import GuiWidgetParentType
from .base_edit import BaseTimeEditorWidget
from .fields import YearField, MonthField, DayOfMonthField, make_time_fields


class YmdhmsWidget(BaseTimeEditorWidget):
    "Custom YMDHMS widget with block cursor and overtype behavior"

    def __init__(self, gui_parent: GuiWidgetParentType = None,
                 y: int = 2000, mo: int = 1, d: int = 1,
                 h: int = 0, m: int = 0, s: float = 0.0,
                 *qtobj_args, **qtobj_kwargs):
        super().__init__(gui_parent, *qtobj_args, **qtobj_kwargs)
        self.set_fields(YearField(), '-', MonthField(), '-', DayOfMonthField(),
                        ' ', *make_time_fields())
        (self.y, _, self.mo, _, self.d, _,
         self.h, _, self.m, _, self.s, _, self.ms) = self.fields
        self.set_ymdhms(y, mo, d, h, m, s)

    def get_title(self):
        return 'YMDHMS'

    def get_tooltip(self):
        return (
            "Overtype mode for all fields\n"
            "Red highlighting — invalid value\n"
            "PgDn or Left — move cursor left\n"
            "PgUp or Right — move cursor right\n"
            "Up or Down — increment/decrement field\n"
            "Ctrl+Up or Ctrl+Down — increment/decrement digit"
        )

    def get_ymdhms(self):
        """Get current Y_DOY_HMS values"""
        return (
            self.y.value,
            self.mo.value,
            self.d.value,
            self.h.value,
            self.m.value,
            self.s.value + self.ms.value/1000,
        )

    def set_ymdhms(self, y: int, mo: int, d: int, h: int, m: int, s: float):
        """Set Y_DOY_HMS values"""
        s_int, ms = divmod(s, 1)
        self.y.set_value(y)
        self.mo.set_value(mo)
        self.d.set_value(d)
        self.h.set_value(h)
        self.m.set_value(m)
        self.s.set_value(int(s_int))
        self.ms.set_value(int(ms*1000))
