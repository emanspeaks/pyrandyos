from enum import Enum, auto

from ...logging import log_func_call
from ...utils.time.gregorian import DAYSINMONTH, is_leap_year
from ..qt import (
    QGroupBox, QHBoxLayout, QFrame, Qt, QObject, QEvent, QKeyEvent, QPainter,
    QPaintEvent, QMouseEvent, QFocusEvent, QLineEdit, QPalette, QFontMetrics,
    QColor,
)
from . import QtWidgetWrapper, GuiWidgetParentType


class YmdhmsFieldType(Enum):
    YEAR = auto()
    MONTH = auto()
    DAY = auto()
    HOUR = auto()
    MINUTE = auto()
    SECOND = auto()
    MILLISECOND = auto()


class YmdhmsDisplayWidget(QtWidgetWrapper[QFrame]):
    """Custom YMDHMS display widget with block cursor and overtype behavior"""

    def __init__(self, gui_parent: 'YmdhmsWidget',
                 *qtobj_args, **qtobj_kwargs):
        # Initialize cursor position (character index in display string)
        self.cursor_pos = 0
        super().__init__(gui_parent, *qtobj_args, **qtobj_kwargs)

    def create_qtobj(self, *args, parent_qtobj: QGroupBox, **kwargs):
        qtobj = QFrame(parent_qtobj)
        qtobj.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        qtobj.setFocusPolicy(Qt.StrongFocus)
        qtobj.setMinimumWidth(170)
        qtobj.setMinimumHeight(25)

        # Use QLineEdit palette colors for consistent theming
        qtobj.setAutoFillBackground(True)
        line_edit_palette = QLineEdit().palette()
        qtobj.setPalette(line_edit_palette)

        # Install event filter for key/mouse/paint events
        callback = self.handle_key_press
        paint_callback = self.handle_paint
        mouse_callback = self.handle_mouse_press
        focus_in_callback = self.handle_focus_in

        class YmdhmsEventFilter(QObject):
            def eventFilter(self, obj: QObject, event: QEvent,
                            qtobj=qtobj, key_cb=callback,
                            paint_cb=paint_callback,
                            mouse_cb=mouse_callback,
                            focus_cb=focus_in_callback):
                """Event filter to handle events"""
                if obj == qtobj:
                    if event.type() == QEvent.KeyPress:
                        return key_cb(event)
                    elif event.type() == QEvent.Paint:
                        paint_cb(event)
                        return False  # Let Qt do default paint too
                    elif event.type() == QEvent.MouseButtonPress:
                        return mouse_cb(event)
                    elif event.type() == QEvent.FocusIn:
                        focus_cb(event)
                        return False
                return False

        event_filter = YmdhmsEventFilter()
        qtobj.installEventFilter(event_filter)
        self.event_filter = event_filter

        return qtobj

    def get_display_string(self):
        """Build the display string from the parent's YMDHMS values"""
        ymdhms_widget: 'YmdhmsWidget' = self.gui_parent
        y_str = str(ymdhms_widget.year).zfill(4)
        mo_str = str(ymdhms_widget.month).zfill(2)
        d_str = str(ymdhms_widget.day).zfill(2)
        h_str = str(ymdhms_widget.hour).zfill(2)
        mi_str = str(ymdhms_widget.minute).zfill(2)
        s_int = int(ymdhms_widget.second)
        s_frac = ymdhms_widget.second - s_int
        ms = int(round(s_frac * 1000))
        s_str = str(s_int).zfill(2)
        ms_str = str(ms).zfill(3)

        return f"{y_str}-{mo_str}-{d_str} {h_str}:{mi_str}:{s_str}.{ms_str}"

    def get_field_boundaries(self):
        """Return a list of (start, end, field_type) tuples for each
        field in the display string"""
        boundaries = []
        pos = 0

        # Year field (4 digits)
        boundaries.append((pos, pos + 4, YmdhmsFieldType.YEAR))
        pos += 5  # Skip "-"

        # Month field (2 digits)
        boundaries.append((pos, pos + 2, YmdhmsFieldType.MONTH))
        pos += 3  # Skip "-"

        # Day field (2 digits)
        boundaries.append((pos, pos + 2, YmdhmsFieldType.DAY))
        pos += 3  # Skip " "

        # Hour field (2 digits)
        boundaries.append((pos, pos + 2, YmdhmsFieldType.HOUR))
        pos += 3  # Skip ":"

        # Minute field (2 digits)
        boundaries.append((pos, pos + 2, YmdhmsFieldType.MINUTE))
        pos += 3  # Skip ":"

        # Second field (2 digits)
        boundaries.append((pos, pos + 2, YmdhmsFieldType.SECOND))
        pos += 3  # Skip "."

        # Millisecond field (3 digits)
        boundaries.append((pos, pos + 3, YmdhmsFieldType.MILLISECOND))

        return boundaries

    def get_current_field(self):
        """Get the field type and boundaries that the cursor is in"""
        boundaries = self.get_field_boundaries()
        for start, end, field_type in boundaries:
            if start <= self.cursor_pos < end:
                return field_type, start, end
        # Default to first field if cursor is out of bounds
        return boundaries[0][2], boundaries[0][0], boundaries[0][1]

    def is_date_valid(self):
        """Check if current year/month/day combination is valid"""
        ymdhms_widget: 'YmdhmsWidget' = self.gui_parent
        year = ymdhms_widget.year
        month = ymdhms_widget.month
        day = ymdhms_widget.day

        if month < 1 or month > 12:
            return False

        # Get the number of days in this month/year
        try:
            max_days = DAYSINMONTH[month - 1] + is_leap_year(year)*(month == 2)
            return 1 <= day <= max_days
        except ValueError:
            return False

    def handle_paint(self, event: QPaintEvent):
        """Custom paint handler to draw the text with block cursor"""
        qtobj = self.qtobj
        painter = QPainter(qtobj)

        # Get display string
        display_str = self.get_display_string()

        # Set up font
        font = self.gui_app.get_monofont()
        font.setPointSize(10)
        painter.setFont(font)

        # Calculate character width for monospace font
        fm = painter.fontMetrics()
        char_width = fm.horizontalAdvance('0')
        char_height = fm.height()

        # Get palette colors
        palette = qtobj.palette()
        bg_color = palette.color(QPalette.Base)
        text_color = palette.color(QPalette.Text)
        highlight_color = palette.color(QPalette.Highlight)
        highlight_text_color = palette.color(QPalette.HighlightedText)

        # Error colors for invalid date
        error_bg_color = QColor(255, 0, 0)  # Red background
        error_text_color = QColor(255, 255, 255)  # White text

        # Draw background
        painter.fillRect(qtobj.rect(), bg_color)

        # Check if date is invalid
        date_invalid = not self.is_date_valid()

        # Get day field boundaries for error highlighting
        day_start = day_end = None
        if date_invalid:
            boundaries = self.get_field_boundaries()
            for start, end, field_type in boundaries:
                if field_type == YmdhmsFieldType.DAY:
                    day_start, day_end = start, end
                    break

        # Draw each character
        x = 5  # Left margin
        y = (qtobj.height() + char_height) // 2 - fm.descent()

        for i, char in enumerate(display_str):
            # Determine colors for this character
            if i == self.cursor_pos and qtobj.hasFocus():
                # Block cursor
                char_bg_color = highlight_color
                char_text_color = highlight_text_color
            elif date_invalid and day_start <= i < day_end:
                # Error highlighting for day field
                char_bg_color = error_bg_color
                char_text_color = error_text_color
            else:
                # Normal colors
                char_bg_color = bg_color
                char_text_color = text_color

            # Draw character background if needed
            if i == self.cursor_pos and qtobj.hasFocus():
                painter.fillRect(x, y - fm.ascent(), char_width,
                                 char_height, char_bg_color)
            elif date_invalid and day_start <= i < day_end:
                painter.fillRect(x, y - fm.ascent(), char_width,
                                 char_height, char_bg_color)

            painter.setPen(char_text_color)
            painter.drawText(x, y, char)
            x += char_width

        painter.end()

    def handle_mouse_press(self, event: QMouseEvent):
        """Handle mouse clicks to position cursor"""
        qtobj = self.qtobj

        # Calculate which character was clicked
        # Use same font as painting to get accurate metrics
        font = self.gui_app.get_monofont()
        font.setPointSize(10)
        fm = QFontMetrics(font)
        char_width = fm.horizontalAdvance('0')

        click_x = event.x() - 5  # Account for left margin
        char_index = max(0, click_x // char_width)

        # Clamp to valid positions (only on actual digits)
        display_str = self.get_display_string()
        boundaries = self.get_field_boundaries()

        # Find the closest valid cursor position
        valid_positions = []
        for start, end, _ in boundaries:
            valid_positions.extend(range(start, end))

        # Find closest valid position
        if char_index < len(display_str):
            if char_index in valid_positions:
                self.cursor_pos = char_index
            else:
                # Find closest valid position
                closest = min(valid_positions,
                              key=lambda p: abs(p - char_index))
                self.cursor_pos = closest
        else:
            # Clicked past the end, go to last valid position
            self.cursor_pos = max(valid_positions)

        qtobj.update()
        return True

    def handle_focus_in(self, event: QFocusEvent):
        """Handle focus in to ensure cursor is visible"""
        self.qtobj.update()

    def handle_key_press(self, event: QKeyEvent):
        """Handle key press events"""
        key = event.key()
        text = event.text()

        # Handle navigation keys
        if key == Qt.Key_Left:
            self.move_cursor_left()
            return True
        elif key == Qt.Key_Right:
            self.move_cursor_right()
            return True
        elif key == Qt.Key_Home:
            self.cursor_pos = 0
            self.qtobj.update()
            return True
        elif key == Qt.Key_End:
            boundaries = self.get_field_boundaries()
            self.cursor_pos = boundaries[-1][1] - 1  # Last position
            self.qtobj.update()
            return True

        # Handle backspace/delete as cursor movement (no actual deletion)
        if key == Qt.Key_Backspace:
            self.move_cursor_left()
            return True
        elif key == Qt.Key_Delete:
            self.move_cursor_right()
            return True

        # Handle Page Up/Down - behave like left/right arrows for
        # easy numpad navigation
        if key == Qt.Key_PageUp:
            self.move_cursor_right()
            return True
        elif key == Qt.Key_PageDown:
            self.move_cursor_left()
            return True

        # Handle up/down arrows to increment/decrement
        if key == Qt.Key_Up:
            if event.modifiers() & Qt.ControlModifier:
                self.increment_single_digit()
            else:
                self.increment_field()
            return True
        elif key == Qt.Key_Down:
            if event.modifiers() & Qt.ControlModifier:
                self.decrement_single_digit()
            else:
                self.decrement_field()
            return True

        # Handle digit input
        if text and text.isdigit():
            self.insert_digit(text)
            return True

        # Allow Tab for focus navigation
        if key in (Qt.Key_Tab, Qt.Key_Backtab):
            return False

        # Filter out all other keys
        return True

    def move_cursor_left(self):
        """Move cursor one position left, skipping separators"""
        boundaries = self.get_field_boundaries()
        valid_positions = []
        for start, end, _ in boundaries:
            valid_positions.extend(range(start, end))

        if self.cursor_pos in valid_positions:
            current_idx = valid_positions.index(self.cursor_pos)
        else:
            current_idx = 0
        if current_idx > 0:
            self.cursor_pos = valid_positions[current_idx - 1]
            self.qtobj.update()

    def move_cursor_right(self):
        """Move cursor one position right, skipping separators"""
        boundaries = self.get_field_boundaries()
        valid_positions = []
        for start, end, _ in boundaries:
            valid_positions.extend(range(start, end))

        if self.cursor_pos in valid_positions:
            current_idx = valid_positions.index(self.cursor_pos)
        else:
            current_idx = 0
        if current_idx < len(valid_positions) - 1:
            self.cursor_pos = valid_positions[current_idx + 1]
            self.qtobj.update()

    def advance_to_next_field(self):
        """Move cursor to the start of the next field"""
        field_type, start, end = self.get_current_field()
        boundaries = self.get_field_boundaries()

        # Find current field index
        for i, (s, e, ft) in enumerate(boundaries):
            if ft == field_type:
                if i < len(boundaries) - 1:
                    # Move to start of next field
                    self.cursor_pos = boundaries[i + 1][0]
                    self.qtobj.update()
                break

    def increment_field(self):
        """Increment the entire field under the cursor"""
        field_type, start, end = self.get_current_field()
        ymdhms_widget: 'YmdhmsWidget' = self.gui_parent
        year = ymdhms_widget.year
        month = ymdhms_widget.month
        day = ymdhms_widget.day
        sec = ymdhms_widget.second

        if field_type == YmdhmsFieldType.YEAR:
            ymdhms_widget.year = min(9999, year + 1)
        elif field_type == YmdhmsFieldType.MONTH:
            ymdhms_widget.month = (month % 12) + 1
        elif field_type == YmdhmsFieldType.DAY:
            try:
                max_days = (DAYSINMONTH[month - 1]
                            + is_leap_year(year)*(month == 2))
                ymdhms_widget.day = (day % max_days) + 1
            except ValueError:
                # Invalid month, just increment day
                ymdhms_widget.day = (day % 31) + 1
        elif field_type == YmdhmsFieldType.HOUR:
            ymdhms_widget.hour = (ymdhms_widget.hour + 1) % 24
        elif field_type == YmdhmsFieldType.MINUTE:
            ymdhms_widget.minute = (ymdhms_widget.minute + 1) % 60
        elif field_type == YmdhmsFieldType.SECOND:
            s_int = int(sec)
            s_frac = sec - s_int
            new_s_int = (s_int + 1) % 61  # Max 60 for integral seconds
            ymdhms_widget.second = new_s_int + s_frac
        elif field_type == YmdhmsFieldType.MILLISECOND:
            s_int = int(sec)
            s_frac = sec - s_int
            ms = int(round(s_frac * 1000))
            new_ms = (ms + 1) % 1000
            ymdhms_widget.second = s_int + new_ms / 1000.0

        self.qtobj.update()

    def decrement_field(self):
        """Decrement the entire field under the cursor"""
        field_type, start, end = self.get_current_field()
        ymdhms_widget: 'YmdhmsWidget' = self.gui_parent
        year = ymdhms_widget.year
        month = ymdhms_widget.month
        day = ymdhms_widget.day
        sec = ymdhms_widget.second

        if field_type == YmdhmsFieldType.YEAR:
            ymdhms_widget.year = max(1, year - 1)
        elif field_type == YmdhmsFieldType.MONTH:
            ymdhms_widget.month = ((month - 2) % 12) + 1
        elif field_type == YmdhmsFieldType.DAY:
            try:
                max_days = (DAYSINMONTH[month - 1]
                            + is_leap_year(year)*(month == 2))
                ymdhms_widget.day = ((day - 2) % max_days) + 1
            except ValueError:
                # Invalid month, just decrement day
                ymdhms_widget.day = ((day - 2) % 31) + 1
        elif field_type == YmdhmsFieldType.HOUR:
            ymdhms_widget.hour = (ymdhms_widget.hour - 1) % 24
        elif field_type == YmdhmsFieldType.MINUTE:
            ymdhms_widget.minute = (ymdhms_widget.minute - 1) % 60
        elif field_type == YmdhmsFieldType.SECOND:
            s_int = int(sec)
            s_frac = sec - s_int
            new_s_int = (s_int - 1) % 61  # Max 60 for integral seconds
            ymdhms_widget.second = new_s_int + s_frac
        elif field_type == YmdhmsFieldType.MILLISECOND:
            s_int = int(sec)
            s_frac = sec - s_int
            ms = int(round(s_frac * 1000))
            new_ms = (ms - 1) % 1000
            ymdhms_widget.second = s_int + new_ms / 1000.0

        self.qtobj.update()

    def increment_single_digit(self):
        """Increment only the single digit under the cursor"""
        field_type, start, end = self.get_current_field()
        pos_in_field = self.cursor_pos - start

        # Get the field string
        field_str = self.get_field_string(field_type)

        # Increment the specific digit
        if pos_in_field < len(field_str):
            field_list = list(field_str)
            current_digit = int(field_list[pos_in_field])
            new_digit = (current_digit + 1) % 10
            field_list[pos_in_field] = str(new_digit)
            new_field_str = ''.join(field_list)

            # Apply validation and update
            self.update_field_value(field_type, int(new_field_str))

        self.qtobj.update()

    def decrement_single_digit(self):
        """Decrement only the single digit under the cursor"""
        field_type, start, end = self.get_current_field()
        pos_in_field = self.cursor_pos - start

        # Get the field string
        field_str = self.get_field_string(field_type)

        # Decrement the specific digit
        if pos_in_field < len(field_str):
            field_list = list(field_str)
            current_digit = int(field_list[pos_in_field])
            new_digit = (current_digit - 1) % 10
            field_list[pos_in_field] = str(new_digit)
            new_field_str = ''.join(field_list)

            # Apply validation and update
            self.update_field_value(field_type, int(new_field_str))

        self.qtobj.update()

    def get_field_string(self, field_type: YmdhmsFieldType):
        """Get the string representation of a field"""
        ymdhms_widget: 'YmdhmsWidget' = self.gui_parent

        if field_type == YmdhmsFieldType.YEAR:
            return str(ymdhms_widget.year).zfill(4)
        elif field_type == YmdhmsFieldType.MONTH:
            return str(ymdhms_widget.month).zfill(2)
        elif field_type == YmdhmsFieldType.DAY:
            return str(ymdhms_widget.day).zfill(2)
        elif field_type == YmdhmsFieldType.HOUR:
            return str(ymdhms_widget.hour).zfill(2)
        elif field_type == YmdhmsFieldType.MINUTE:
            return str(ymdhms_widget.minute).zfill(2)
        elif field_type == YmdhmsFieldType.SECOND:
            return str(int(ymdhms_widget.second)).zfill(2)
        elif field_type == YmdhmsFieldType.MILLISECOND:
            s_int = int(ymdhms_widget.second)
            s_frac = ymdhms_widget.second - s_int
            ms = int(round(s_frac * 1000))
            return str(ms).zfill(3)

    def update_field_value(self, field_type: YmdhmsFieldType, new_val: int):
        """Update a field value with validation"""
        ymdhms_widget: 'YmdhmsWidget' = self.gui_parent

        if field_type == YmdhmsFieldType.YEAR:
            if 1 <= new_val <= 9999:
                ymdhms_widget.year = new_val
        elif field_type == YmdhmsFieldType.MONTH:
            if 1 <= new_val <= 12:
                ymdhms_widget.month = new_val
        elif field_type == YmdhmsFieldType.DAY:
            if 1 <= new_val <= 31:  # Will be validated by date checker
                ymdhms_widget.day = new_val
        elif field_type == YmdhmsFieldType.HOUR:
            if new_val <= 23:
                ymdhms_widget.hour = new_val
        elif field_type == YmdhmsFieldType.MINUTE:
            if new_val <= 59:
                ymdhms_widget.minute = new_val
        elif field_type == YmdhmsFieldType.SECOND:
            if new_val <= 60:  # Max 60 for integral seconds
                s_frac = ymdhms_widget.second - int(ymdhms_widget.second)
                ymdhms_widget.second = new_val + s_frac
        elif field_type == YmdhmsFieldType.MILLISECOND:
            s_int = int(ymdhms_widget.second)
            ymdhms_widget.second = s_int + new_val / 1000.0

    def insert_digit(self, digit: str):
        """Insert a digit at the cursor position (overtype mode)"""
        field_type, start, end = self.get_current_field()
        pos_in_field = self.cursor_pos - start

        # Validate digit based on position and field type
        if not self.validate_digit(digit, field_type, pos_in_field):
            return

        # Get current field value as string
        field_str = self.get_field_string(field_type)

        # Replace character at position (overtype mode for all fields)
        field_list = list(field_str)
        if pos_in_field < len(field_list):
            field_list[pos_in_field] = digit
            new_field_str = ''.join(field_list)

            # Update the field value
            self.update_field_value(field_type, int(new_field_str))

            # Move cursor right or auto-advance
            if self.cursor_pos < end - 1:
                self.move_cursor_right()
            else:
                # At end of field, advance to next field
                self.advance_to_next_field()

        self.qtobj.update()

    def validate_digit(self, digit: str, field_type: YmdhmsFieldType,
                       pos_in_field: int):
        """Validate a digit based on field type and position within field"""
        ymdhms_widget: 'YmdhmsWidget' = self.gui_parent
        d_val = int(digit)

        if field_type == YmdhmsFieldType.YEAR:
            # Year: any digit is valid
            return True

        elif field_type == YmdhmsFieldType.MONTH:
            # Month: first digit 0-1, second digit depends on first
            if pos_in_field == 0:
                return d_val <= 1
            elif pos_in_field == 1:
                first_digit = int(str(ymdhms_widget.month).zfill(2)[0])
                if first_digit == 0:
                    return d_val >= 1  # 01-09
                elif first_digit == 1:
                    return d_val <= 2  # 10-12
                return True

        elif field_type == YmdhmsFieldType.DAY:
            # Day: first digit 0-3, second digit depends on first
            # Allow any valid combination, will be checked by date validator
            if pos_in_field == 0:
                return d_val <= 3
            elif pos_in_field == 1:
                first_digit = int(str(ymdhms_widget.day).zfill(2)[0])
                if first_digit == 0:
                    return d_val >= 1  # 01-09
                elif first_digit == 3:
                    return d_val <= 1  # 30-31
                return True

        elif field_type == YmdhmsFieldType.HOUR:
            # Hour: first digit 0-2, second digit depends on first
            if pos_in_field == 0:
                return d_val <= 2
            elif pos_in_field == 1:
                first_digit = int(str(ymdhms_widget.hour).zfill(2)[0])
                if first_digit == 2:
                    return d_val <= 3
                return True

        elif field_type == YmdhmsFieldType.MINUTE:
            # Minute: first digit 0-5, second digit 0-9
            if pos_in_field == 0:
                return d_val <= 5
            return True

        elif field_type == YmdhmsFieldType.SECOND:
            # Second: first digit 0-6 (max 60), second digit depends on first
            if pos_in_field == 0:
                return d_val <= 6
            elif pos_in_field == 1:
                first_digit = int(str(int(ymdhms_widget.second)).zfill(2)[0])
                if first_digit == 6:
                    return d_val == 0  # Only 60 allowed, not 61-69
                return True

        elif field_type == YmdhmsFieldType.MILLISECOND:
            # Millisecond: any digit 0-9 is valid
            return True

        return False


class YmdhmsWidget(QtWidgetWrapper[QGroupBox]):
    """YMDHMS widget for date and time input"""

    def __init__(self, gui_parent=None,
                 year=2000, month=1, day=1,
                 hour=0, minute=0, second=0.0,
                 *qtobj_args, **qtobj_kwargs):
        self.set_ymdhms(year, month, day, hour, minute, second, False)
        super().__init__(gui_parent, *qtobj_args, **qtobj_kwargs)

    @log_func_call
    def create_qtobj(self, *args, **kwargs):
        parent_qtobj: GuiWidgetParentType = self.gui_parent.qtobj

        frame = QGroupBox(parent_qtobj)
        frame.setTitle('YMDHMS')
        frame.setFixedWidth(195)
        frame.setMaximumHeight(60)
        self.frame = frame

        layout = QHBoxLayout()
        frame.setLayout(layout)
        self.layout = layout

        # Custom display widget
        display = YmdhmsDisplayWidget(self, parent_qtobj=frame)
        layout.addWidget(display.qtobj)
        self.display = display

        # Set tooltip with keyboard shortcuts
        tooltip = (
            "Overtype mode for all fields\n"
            "Red highlighting — invalid day for month\n"
            "PgDn or Left — move cursor left\n"
            "PgUp or Right — move cursor right\n"
            "Up or Down — increment/decrement field\n"
            "Ctrl+Up or Ctrl+Down — increment/decrement digit"
        )
        display.qtobj.setToolTip(tooltip)

        return frame

    def get_ymdhms(self):
        """Get current YMDHMS values"""
        return [self.year, self.month, self.day, self.hour,
                self.minute, self.second]

    def set_ymdhms(self, year: int, month: int, day: int, hour: int,
                   minute: int, second: float,
                   update_display: bool = True):
        """Set YMDHMS values"""
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second
        if update_display and hasattr(self, 'display'):
            self.display.qtobj.update()

    def is_valid_date(self):
        """Check if the current date is valid"""
        if hasattr(self, 'display'):
            return self.display.is_date_valid()
        else:
            # Fallback validation if display not created yet
            month = self.month
            if month < 1 or month > 12:
                return False
            try:
                year = self.year
                max_days = (DAYSINMONTH[month - 1]
                            + is_leap_year(year)*(month == 2))
                return 1 <= self.day <= max_days
            except ValueError:
                return False
