from enum import Enum, auto

from ...logging import log_func_call
from ...utils.time.gregorian import is_leap_year
from ..qt import (
    QGroupBox, QHBoxLayout, QFrame, Qt, QObject,
    QEvent, QKeyEvent, QPainter, QFont, QPaintEvent,
    QMouseEvent, QFocusEvent, QLineEdit, QPalette, QFontMetrics, QColor
)
from . import QtWidgetWrapper, GuiWidgetParentType


class YDoyHmsFieldType(Enum):
    YEAR = auto()
    DAY_OF_YEAR = auto()
    HOUR = auto()
    MINUTE = auto()
    SECOND = auto()
    MILLISECOND = auto()


class YDoyHmsDisplayWidget(QtWidgetWrapper[QFrame]):
    "Custom Y_DOY_HMS display widget with block cursor and overtype behavior"

    def __init__(self, gui_parent: 'YDoyHmsWidget',
                 *qtobj_args, **qtobj_kwargs):
        # Initialize cursor position (character index in display string)
        self.cursor_pos = 0
        super().__init__(gui_parent, *qtobj_args, **qtobj_kwargs)

    def create_qtobj(self, *args, parent_qtobj: QGroupBox, **kwargs):
        qtobj = QFrame(parent_qtobj)
        qtobj.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        qtobj.setFocusPolicy(Qt.StrongFocus)
        qtobj.setMinimumWidth(200)
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

        class YDoyHmsEventFilter(QObject):
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

        event_filter = YDoyHmsEventFilter()
        qtobj.installEventFilter(event_filter)
        self.event_filter = event_filter

        return qtobj

    def get_display_string(self):
        """Build the display string from the parent's Y_DOY_HMS values"""
        ydoy_widget: 'YDoyHmsWidget' = self.gui_parent
        y_str = str(ydoy_widget.year).zfill(4)
        doy_str = str(ydoy_widget.day_of_year).zfill(3)
        h_str = str(ydoy_widget.hour).zfill(2)
        mi_str = str(ydoy_widget.minute).zfill(2)
        s_int = int(ydoy_widget.second)
        s_frac = ydoy_widget.second - s_int
        ms = int(round(s_frac * 1000))
        s_str = str(s_int).zfill(2)
        ms_str = str(ms).zfill(3)

        return f"{y_str}:{doy_str}:{h_str}:{mi_str}:{s_str}.{ms_str}"

    def get_field_boundaries(self):
        """Return a list of (start, end, field_type) tuples for each
        field in the display string"""
        boundaries = []
        pos = 0

        # Year field (4 digits)
        boundaries.append((pos, pos + 4, YDoyHmsFieldType.YEAR))
        pos += 5  # Skip ":"

        # Day of year field (3 digits)
        boundaries.append((pos, pos + 3, YDoyHmsFieldType.DAY_OF_YEAR))
        pos += 4  # Skip ":"

        # Hour field (2 digits)
        boundaries.append((pos, pos + 2, YDoyHmsFieldType.HOUR))
        pos += 3  # Skip ":"

        # Minute field (2 digits)
        boundaries.append((pos, pos + 2, YDoyHmsFieldType.MINUTE))
        pos += 3  # Skip ":"

        # Second field (2 digits)
        boundaries.append((pos, pos + 2, YDoyHmsFieldType.SECOND))
        pos += 3  # Skip "."

        # Millisecond field (3 digits)
        boundaries.append((pos, pos + 3, YDoyHmsFieldType.MILLISECOND))

        return boundaries

    def get_current_field(self):
        """Get the field type and boundaries that the cursor is in"""
        boundaries = self.get_field_boundaries()
        for start, end, field_type in boundaries:
            if start <= self.cursor_pos < end:
                return field_type, start, end
        # Default to first field if cursor is out of bounds
        return boundaries[0][2], boundaries[0][0], boundaries[0][1]

    def is_leap_year(self, year: int):
        """Check if the given year is a leap year"""
        return is_leap_year(year)

    def is_date_valid(self):
        """Check if current year/day_of_year combination is valid"""
        ydoy_widget: 'YDoyHmsWidget' = self.gui_parent
        year = ydoy_widget.year
        day_of_year = ydoy_widget.day_of_year

        if day_of_year < 1:
            return False

        # Check max days in year
        if self.is_leap_year(year):
            max_days = 366
        else:
            max_days = 365

        return day_of_year <= max_days

    def handle_paint(self, event: QPaintEvent):
        """Custom paint handler to draw the text with block cursor"""
        qtobj = self.qtobj
        painter = QPainter(qtobj)

        # Get display string
        display_str = self.get_display_string()

        # Set up font
        font = QFont("Courier New", 10)
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

        # Get day of year field boundaries for error highlighting
        doy_start = doy_end = None
        if date_invalid:
            boundaries = self.get_field_boundaries()
            for start, end, field_type in boundaries:
                if field_type == YDoyHmsFieldType.DAY_OF_YEAR:
                    doy_start, doy_end = start, end
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
            elif date_invalid and doy_start <= i < doy_end:
                # Error highlighting for day of year field
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
            elif date_invalid and doy_start <= i < doy_end:
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
        font = QFont("Courier New", 10)
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
        ydoy_widget: 'YDoyHmsWidget' = self.gui_parent

        if field_type == YDoyHmsFieldType.YEAR:
            ydoy_widget.year = min(9999, ydoy_widget.year + 1)
        elif field_type == YDoyHmsFieldType.DAY_OF_YEAR:
            max_doy = 366 if self.is_leap_year(ydoy_widget.year) else 365
            ydoy_widget.day_of_year = (ydoy_widget.day_of_year % max_doy) + 1
        elif field_type == YDoyHmsFieldType.HOUR:
            ydoy_widget.hour = (ydoy_widget.hour + 1) % 24
        elif field_type == YDoyHmsFieldType.MINUTE:
            ydoy_widget.minute = (ydoy_widget.minute + 1) % 60
        elif field_type == YDoyHmsFieldType.SECOND:
            s_int = int(ydoy_widget.second)
            s_frac = ydoy_widget.second - s_int
            new_s_int = (s_int + 1) % 61  # Max 60 for integral seconds
            ydoy_widget.second = new_s_int + s_frac
        elif field_type == YDoyHmsFieldType.MILLISECOND:
            s_int = int(ydoy_widget.second)
            s_frac = ydoy_widget.second - s_int
            ms = int(round(s_frac * 1000))
            new_ms = (ms + 1) % 1000
            ydoy_widget.second = s_int + new_ms / 1000.0

        self.qtobj.update()

    def decrement_field(self):
        """Decrement the entire field under the cursor"""
        field_type, start, end = self.get_current_field()
        ydoy_widget: 'YDoyHmsWidget' = self.gui_parent

        if field_type == YDoyHmsFieldType.YEAR:
            ydoy_widget.year = max(1, ydoy_widget.year - 1)
        elif field_type == YDoyHmsFieldType.DAY_OF_YEAR:
            max_doy = 366 if self.is_leap_year(ydoy_widget.year) else 365
            doy = ydoy_widget.day_of_year
            ydoy_widget.day_of_year = ((doy - 2) % max_doy) + 1
        elif field_type == YDoyHmsFieldType.HOUR:
            ydoy_widget.hour = (ydoy_widget.hour - 1) % 24
        elif field_type == YDoyHmsFieldType.MINUTE:
            ydoy_widget.minute = (ydoy_widget.minute - 1) % 60
        elif field_type == YDoyHmsFieldType.SECOND:
            s_int = int(ydoy_widget.second)
            s_frac = ydoy_widget.second - s_int
            new_s_int = (s_int - 1) % 61  # Max 60 for integral seconds
            ydoy_widget.second = new_s_int + s_frac
        elif field_type == YDoyHmsFieldType.MILLISECOND:
            s_int = int(ydoy_widget.second)
            s_frac = ydoy_widget.second - s_int
            ms = int(round(s_frac * 1000))
            new_ms = (ms - 1) % 1000
            ydoy_widget.second = s_int + new_ms / 1000.0

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

    def get_field_string(self, field_type: YDoyHmsFieldType):
        """Get the string representation of a field"""
        ydoy_widget: 'YDoyHmsWidget' = self.gui_parent

        if field_type == YDoyHmsFieldType.YEAR:
            return str(ydoy_widget.year).zfill(4)
        elif field_type == YDoyHmsFieldType.DAY_OF_YEAR:
            return str(ydoy_widget.day_of_year).zfill(3)
        elif field_type == YDoyHmsFieldType.HOUR:
            return str(ydoy_widget.hour).zfill(2)
        elif field_type == YDoyHmsFieldType.MINUTE:
            return str(ydoy_widget.minute).zfill(2)
        elif field_type == YDoyHmsFieldType.SECOND:
            return str(int(ydoy_widget.second)).zfill(2)
        elif field_type == YDoyHmsFieldType.MILLISECOND:
            s_int = int(ydoy_widget.second)
            s_frac = ydoy_widget.second - s_int
            ms = int(round(s_frac * 1000))
            return str(ms).zfill(3)

    def update_field_value(self, field_type: YDoyHmsFieldType, new_val: int):
        """Update a field value with validation"""
        ydoy_widget: 'YDoyHmsWidget' = self.gui_parent

        if field_type == YDoyHmsFieldType.YEAR:
            if 1 <= new_val <= 9999:
                ydoy_widget.year = new_val
        elif field_type == YDoyHmsFieldType.DAY_OF_YEAR:
            max_doy = 366 if self.is_leap_year(ydoy_widget.year) else 365
            if 1 <= new_val <= max_doy:
                ydoy_widget.day_of_year = new_val
        elif field_type == YDoyHmsFieldType.HOUR:
            if new_val <= 23:
                ydoy_widget.hour = new_val
        elif field_type == YDoyHmsFieldType.MINUTE:
            if new_val <= 59:
                ydoy_widget.minute = new_val
        elif field_type == YDoyHmsFieldType.SECOND:
            if new_val <= 60:  # Max 60 for integral seconds
                s_frac = ydoy_widget.second - int(ydoy_widget.second)
                ydoy_widget.second = new_val + s_frac
        elif field_type == YDoyHmsFieldType.MILLISECOND:
            s_int = int(ydoy_widget.second)
            ydoy_widget.second = s_int + new_val / 1000.0

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

    def validate_digit(self, digit: str, field_type: YDoyHmsFieldType,
                       pos_in_field: int):
        """Validate a digit based on field type and position within field"""
        ydoy_widget: 'YDoyHmsWidget' = self.gui_parent
        d_val = int(digit)

        if field_type == YDoyHmsFieldType.YEAR:
            # Year: any digit is valid
            return True

        elif field_type == YDoyHmsFieldType.DAY_OF_YEAR:
            # Day of year: first digit 0-3, validation depends on position
            if pos_in_field == 0:
                return d_val <= 3
            elif pos_in_field == 1:
                first_digit = int(str(ydoy_widget.day_of_year).zfill(3)[0])
                if first_digit == 0:
                    return d_val >= 1  # 001-099
                elif first_digit == 3:
                    return d_val <= 6  # 300-366
                return True
            elif pos_in_field == 2:
                first_two = int(str(ydoy_widget.day_of_year).zfill(3)[:2])
                if first_two == 0:  # This shouldn't happen since day >= 1
                    return d_val >= 1
                elif first_two == 36:
                    return d_val <= 6  # 360-366
                return True

        elif field_type == YDoyHmsFieldType.HOUR:
            # Hour: first digit 0-2, second digit depends on first
            if pos_in_field == 0:
                return d_val <= 2
            elif pos_in_field == 1:
                first_digit = int(str(ydoy_widget.hour).zfill(2)[0])
                if first_digit == 2:
                    return d_val <= 3
                return True

        elif field_type == YDoyHmsFieldType.MINUTE:
            # Minute: first digit 0-5, second digit 0-9
            if pos_in_field == 0:
                return d_val <= 5
            return True

        elif field_type == YDoyHmsFieldType.SECOND:
            # Second: first digit 0-6 (max 60), second digit depends on first
            if pos_in_field == 0:
                return d_val <= 6
            elif pos_in_field == 1:
                first_digit = int(str(int(ydoy_widget.second)).zfill(2)[0])
                if first_digit == 6:
                    return d_val == 0  # Only 60 allowed, not 61-69
                return True

        elif field_type == YDoyHmsFieldType.MILLISECOND:
            # Millisecond: any digit 0-9 is valid
            return True

        return False


class YDoyHmsWidget(QtWidgetWrapper[QGroupBox]):
    """Y_DOY_HMS widget for year/day-of-year/time input"""

    def __init__(self, gui_parent: GuiWidgetParentType = None,
                 year: int = 2000, day_of_year: int = 1,
                 hour: int = 0, minute: int = 0, second: float = 0.0,
                 *qtobj_args, **qtobj_kwargs):
        self.set_ydoy_hms(year, day_of_year, hour, minute, second, False)
        super().__init__(gui_parent, *qtobj_args, **qtobj_kwargs)

    @log_func_call
    def create_qtobj(self, *args, **kwargs):
        parent_qtobj: GuiWidgetParentType = self.gui_parent.qtobj

        frame = QGroupBox(parent_qtobj)
        frame.setTitle('Y_DOY_HMS')
        frame.setMaximumWidth(220)
        frame.setMaximumHeight(60)
        self.frame = frame

        layout = QHBoxLayout()
        frame.setLayout(layout)
        self.layout = layout

        # Custom display widget
        display = YDoyHmsDisplayWidget(self, parent_qtobj=frame)
        layout.addWidget(display.qtobj)
        self.display = display

        # Set tooltip with keyboard shortcuts
        tooltip = ("Overtype mode for all fields\n"
                   "PgUp/Right — move cursor right\n"
                   "PgDn/Left — move cursor left\n"
                   "Up/Down — increment/decrement field\n"
                   "Ctrl+Up/Down — increment/decrement digit\n"
                   "Red highlighting — invalid day of year")
        display.qtobj.setToolTip(tooltip)

        return frame

    def get_ydoy_hms(self):
        """Get current Y_DOY_HMS values"""
        return [self.year, self.day_of_year, self.hour, self.minute,
                self.second]

    def set_ydoy_hms(self, year: int, day_of_year: int, hour: int, minute: int,
                     second: float,
                     update_display: bool = True):
        """Set Y_DOY_HMS values"""
        self.year = year
        self.day_of_year = day_of_year
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
            if self.day_of_year < 1:
                return False
            # Use placeholder leap year function
            if self.display.is_leap_year(self.year):
                max_days = 366
            else:
                max_days = 365
            return self.day_of_year <= max_days
