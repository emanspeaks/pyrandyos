from typing import TYPE_CHECKING
from math import log10

from ....utils.time.gregorian import DAYSINMONTH, is_leap_year


if TYPE_CHECKING:
    from .base_edit import BaseTimeEditorWidget


class TimeField:
    def __init__(self, value: int | str = None):
        self.value = self.minval() if value is None else value
        self.parent: 'BaseTimeEditorWidget' = None
        self.prev: 'TimeField' = None
        self.nxt: 'TimeField' = None

    def start_rel_char(self):
        return 0

    def end_rel_char(self):
        return self.width()

    def start_char(self):
        return self.left() + self.start_rel_char()

    def end_char(self):
        return self.left() + self.end_rel_char()

    def left(self):
        prev = self.prev
        return prev.right() if prev else 0

    def right(self):
        return self.left() + self.width()

    def bounds(self):
        return self.left(), self.right()

    def width(self) -> int:
        return len(str(self))

    def format_value(self, value):
        return str(value)

    def __str__(self):
        return self.format_value(self.value)

    def valid(self):
        return not self.editable() or self.validate()

    def invalid_chars(self, abs: bool = False) -> list[int]:
        if self.valid():
            return []
        text = str(self)
        rel = list(range(len(text)))
        left = self.left()
        return [x + left for x in rel] if abs else rel

    def handle_backspace(self):
        self.parent.move_cursor_left()

    def handle_delete(self):
        # self.parent.move_cursor_right()
        self.set_value(self.minval())

    def maxval(self):
        return 0

    def minval(self):
        return 0

    def step(self):
        return 1

    def set_value(self, value: int | str):
        self.value = value
        self.parent.display.update()

    def incr(self):
        if not self.editable():
            raise NotImplementedError

        new = self.value + self.step()
        maxval = self.maxval()
        minval = self.minval()
        if maxval is not None and new > maxval:
            new = minval

        if new is not None:
            self.set_value(new)

    def decr(self):
        if not self.editable():
            raise NotImplementedError

        new = self.value - self.step()
        maxval = self.maxval()
        minval = self.minval()
        if minval is not None and new < minval:
            new = maxval

        if new is not None:
            self.set_value(new)

    def incr_digit(self, pos: int = None):
        if not self.editable():
            raise NotImplementedError

        if pos is None:
            pos = self.parent.cursor_pos - self.left()

        oldtext = str(self)
        newtextlist = list(oldtext)
        newtextlist[pos] = str((int(oldtext[pos]) + 1) % 10)
        newtext = ''.join(newtextlist)

        if not self.validate(newtext):
            return

        self.set_value(int(newtext))

    def decr_digit(self, pos: int = None):
        if not self.editable():
            raise NotImplementedError

        if pos is None:
            pos = self.parent.cursor_pos - self.left()

        oldtext = str(self)
        newtextlist = list(oldtext)
        newtextlist[pos] = str((int(oldtext[pos]) - 1) % 10)
        newtext = ''.join(newtextlist)

        if not self.validate(newtext):
            return

        self.set_value(int(newtext))

    def max_digit_for_pos(self, pos: int = None):
        if pos is None:
            pos = self.parent.cursor_pos - self.left()

        maxval = self.maxval()
        width = self.width()
        exp = width - 1 - pos
        maxexp = int(log10(maxval)) if maxval else 0

        if exp > maxexp:
            return 0
        if exp == maxexp:
            return int(self.format_value(maxval)[pos])
        return 9

    def min_digit_for_pos(self, pos: int = None):
        exp = self.width() - 1 - pos
        return 0 if exp or self.maxval() > 10 else self.minval()

    def write(self, char: str, pos: int = None):
        if not self.editable():
            raise NotImplementedError

        if pos is None:
            pos = self.parent.cursor_pos - self.left()

        # Default: Replace character at position (overtype mode)
        oldtext = str(self)
        newtextlist = list(oldtext)
        newtextlist[pos] = char
        newtext = ''.join(newtextlist)

        if not self.validate(newtext):
            width = self.width()
            exp = width - 1 - pos
            digit = int(char)

            # we need to allow overtype from left to right, so sometimes we
            # can let the illegal value slide.
            if (not exp  # it's the last digit
                    or digit > self.max_digit_for_pos(pos)
                    or digit < self.min_digit_for_pos(pos)):
                return

        self.value = int(newtext)
        self.parent.move_cursor_right()
        self.parent.display.update()

    def validate(self, value: str | int = None):
        if not self.editable():
            return True

        if value is None:
            value = self.value

        value = int(value)
        minval = self.minval()
        if minval is not None and value < minval:
            return False

        maxval = self.maxval()
        if maxval is not None and value > maxval:
            return False

        return True

    def editable(self):
        return True


class LabelField(TimeField):
    def editable(self):
        return False


class SignField(TimeField):
    def __init__(self, value: int = 1):
        super().__init__(value)

    def format_value(self, value):
        return '-' if value < 0 else '+'

    def minval(self):
        return -1

    def maxval(self):
        return 1

    def step(self):
        return 2

    def incr_digit(self, pos: int = None):
        super().incr()

    def decr_digit(self, pos: int = None):
        super().decr()

    def write(self, char: str, pos: int = None):
        if not char:
            return

        if char in ('+', '-'):
            self.set_value(-1 if char == '-' else 1)

        parent = self.parent
        parent.advance_to_next_field()

        if char.isdigit():
            parent.get_current_field().write(char)

    def handle_delete(self):
        pass

    def handle_backspace(self):
        pass


class YearField(TimeField):
    def __init__(self, value: int | str = 2000):
        super().__init__(value)

    def maxval(self):
        return 9999

    def format_value(self, value):
        return '{:04d}'.format(value)


class MonthField(TimeField):
    def maxval(self):
        return 12

    def minval(self):
        return 1

    def format_value(self, value):
        return '{:02d}'.format(value)


class DayOfMonthField(TimeField):
    def maxval(self):
        y = None
        mo = None
        for f in self.parent.fields:
            if isinstance(f, YearField):
                y = f.value

            elif isinstance(f, MonthField) and f.valid():
                mo = f.value

        if mo is None:
            return 0
        return DAYSINMONTH[mo - 1] + (mo == 2)*is_leap_year(y)

    def minval(self):
        return 1

    def format_value(self, value):
        return '{:02d}'.format(value)


class DayOfYearField(TimeField):
    def maxval(self):
        y = None
        for f in self.parent.fields:
            if isinstance(f, YearField):
                y = f.value

        return 365 + is_leap_year(y)

    def minval(self):
        return 1

    def format_value(self, value):
        return '{:03d}'.format(value)


class DaysField(TimeField):
    def __init__(self, value: int | str = None):
        super().__init__(value)
        self._width = len(self.format_value(self.value, 3))

    def width(self):
        return self._width

    def format_value(self, value, width: int = None):
        if width is None:
            width = self.width()

        return f' {{:0{width - 2}d}} '.format(value)

    def start_rel_char(self):
        return 1

    def end_rel_char(self):
        return self.width() - 1

    def maxval(self):
        return

    def handle_backspace(self):
        "Handle backspace in days field - delete char before cursor"
        parent = self.parent
        cursor = parent.cursor_pos
        pos_in_field = cursor - self.left()

        # Can't delete if at start of field (position 0 is space)
        if pos_in_field <= 1:
            return super().handle_backspace()

        # Get current days value as string
        d_str = str(self)

        # Can't delete if we only have one digit left, but will clear number
        dlen = len(d_str)
        if pos_in_field == dlen - 1 and dlen == 3:
            return super().handle_delete()

        # Remove character before cursor
        new_d_str = d_str[:pos_in_field - 1] + d_str[pos_in_field:]
        self._width = len(new_d_str)

        # Update days value
        self.value = int(new_d_str) if new_d_str else 0

        # Move cursor left
        parent.set_cursor_pos(cursor - 1)

    def handle_delete(self):
        "Handle delete in days field - delete char at cursor"
        parent = self.parent
        cursor = parent.cursor_pos
        pos_in_field = cursor - self.left()

        # If cursor is on front space, don't delete, just move cursor to start
        if pos_in_field == 0:
            return parent.move_cursor_right()

        # Get current days value as string
        d_str = str(self)
        dlen = len(d_str)

        # Can't delete if at end of field or only one digit left,
        # but we will clear number
        if pos_in_field == dlen - 1 or dlen == 3:
            return super().handle_delete()

        # Remove character at cursor
        new_d_str = d_str[:pos_in_field] + d_str[pos_in_field + 1:]

        # Update days value
        self.value = int(new_d_str) if new_d_str else 0
        self._width = len(new_d_str)

        # Keep cursor at same position
        # parent.set_cursor_pos(cursor - 1)
        parent.display.update()

    def write(self, char: str, pos: int = None):
        if not self.editable():
            raise NotImplementedError

        parent = self.parent
        cursor = parent.cursor_pos
        if pos is None:
            pos = cursor - self.left()

        # Default: Replace character at position (overtype mode)
        oldtext = str(self)
        newtextlist = list(oldtext)
        if not pos or pos == len(oldtext) - 1:
            # insert the char rather than overtype
            newtextlist.insert(-1 if pos else 1, char)
            self._width = len(newtextlist)

        else:
            newtextlist[pos] = char

        newtext = ''.join(newtextlist)
        self.value = int(newtext)

        # if cursor was at front, need to doubly advance due to the insert
        if not pos:
            self.parent.move_cursor_right()

        parent.move_cursor_right()

    def incr_digit(self, pos: int = None):
        rel_cursor = self.parent.cursor_pos - self.left()
        if pos is None:
            pos = rel_cursor

        width = self.width()
        parent = self.parent
        if pos == width - 1:
            if pos == rel_cursor:
                parent.move_cursor_left()

            pos -= 1

        elif not pos:
            if pos == rel_cursor:
                parent.move_cursor_right()

            pos += 1

        super().incr_digit(pos)

    def decr_digit(self, pos: int = None):
        rel_cursor = self.parent.cursor_pos - self.left()
        if pos is None:
            pos = rel_cursor

        width = self.width()
        parent = self.parent
        if pos == width - 1:
            if pos == rel_cursor:
                parent.move_cursor_left()

            pos -= 1

        elif not pos:
            if pos == rel_cursor:
                parent.move_cursor_right()

            pos += 1

        super().decr_digit(pos)


class HmsField(TimeField):
    def format_value(self, value):
        return '{:02d}'.format(value)


class HourField(HmsField):
    def maxval(self):
        return 23


class MinuteField(HmsField):
    def maxval(self):
        return 59


class SecondField(HmsField):
    def maxval(self):
        return 59


class LeapSecondField(SecondField):
    def maxval(self):
        return 60


class MillisecondField(TimeField):
    def maxval(self):
        return 999

    def format_value(self, value):
        return '{:03d}'.format(value)


def make_time_fields(leap: bool = True):
    return (
        HourField(),
        ':',
        MinuteField(),
        ':',
        LeapSecondField() if leap else SecondField(),
        '.',
        MillisecondField(),
    )
