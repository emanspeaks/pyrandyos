from ....utils.time.gregorian import (
    sec_to_y_doy_hms, ymdhms_to_sec, doy2md,
)
from .. import GuiWidgetParentType
from .base_edit import BaseTimeEditorWidget, EditCallbackType
from .fields import YearField, DayOfYearField, make_time_fields


class YDoyHmsWidget(BaseTimeEditorWidget):
    "Custom Y_DOY_HMS widget with block cursor and overtype behavior"

    def __init__(self, gui_parent: GuiWidgetParentType = None,
                 y: int = 2000, doy: int = 1, h: int = 0, m: int = 0,
                 s: float = 0.0, edit_callback: EditCallbackType = None,
                 *qtobj_args, **qtobj_kwargs):
        super().__init__(gui_parent, edit_callback, *qtobj_args,
                         **qtobj_kwargs)
        self.set_fields(YearField(), ':', DayOfYearField(), ':',
                        *make_time_fields())
        (self.y, _, self.doy, _,
         self.h, _, self.m, _, self.s, _, self.ms) = self.fields
        self.set_y_doy_hms(y, doy, h, m, s)

    def get_title(self):
        return 'Y:DOY:HMS'

    def get_tooltip(self):
        return (
            "Overtype mode for all fields\n"
            "Red highlighting — invalid value\n"
            "PgDn or Left — move cursor left\n"
            "PgUp or Right — move cursor right\n"
            "Up or Down — increment/decrement field\n"
            "Ctrl+Up or Ctrl+Down — increment/decrement digit"
        )

    def get_y_doy_hms(self):
        """Get current Y_DOY_HMS values"""
        return (
            self.y.value,
            self.doy.value,
            self.h.value,
            self.m.value,
            self.s.value + self.ms.value/1000,
        )

    def set_y_doy_hms(self, y: int, doy: int, h: int, m: int, s: float):
        """Set Y_DOY_HMS values"""
        s_int, ms = divmod(s, 1)
        self.y.set_value(y)
        self.doy.set_value(doy)
        self.h.set_value(h)
        self.m.set_value(m)
        self.s.set_value(int(s_int))
        self.ms.set_value(int(ms*1000))

    def get_sec(self) -> float:
        y, doy, h, m, s = self.get_y_doy_hms()
        mo, d = doy2md(y, doy)
        return ymdhms_to_sec(y, mo, d, h, m, s)

    def set_from_sec(self, sec: float):
        self.set_y_doy_hms(*sec_to_y_doy_hms(sec))
