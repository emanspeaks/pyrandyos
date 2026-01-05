from enum import Enum, auto

from ...logging import log_func_call
from ..qt import (
    QGroupBox, QHBoxLayout, Qt, QKeyEvent, QPainter, QPaintEvent, QMouseEvent,
    QFocusEvent, QPalette, QFontMetrics,
)
# from ..callback import qt_callback
from . import QtWidgetWrapper, GuiWidgetParentType
from .time_field_base import TimeFieldDisplayWidget


class DhmsFieldType(Enum):
    SIGN = auto()
    DAYS = auto()
    HOURS = auto()
    MINUTES = auto()
    SECONDS = auto()
    MILLISECONDS = auto()


class DhmsDisplayWidget(TimeFieldDisplayWidget):
    """Custom single-widget DHMS display with block cursor and overtype
    behavior"""

    def get_min_width(self):
        return 170

    def get_field_error_ranges(self):
        """DHMS has no error highlighting"""
        return []

    def get_display_string(self):
        """Build the display string from the parent's DHMS values"""
        dhms_widget: 'DhmsWidget' = self.gui_parent
        sign_str = '-' if dhms_widget.sign < 0 else '+'
        d_str = str(dhms_widget.d).lstrip('0') or '0'
        h_str = str(dhms_widget.h).zfill(2)
        m_str = str(dhms_widget.m).zfill(2)
        s_int = int(dhms_widget.s)
        s_frac = dhms_widget.s - s_int
        ms = int(round(s_frac * 1000))
        s_str = str(s_int).zfill(2)
        ms_str = str(ms).zfill(3)

        return f"{sign_str} {d_str} / {h_str}:{m_str}:{s_str}.{ms_str}"

    def get_field_boundaries(self):
        dhms_widget: 'DhmsWidget' = self.gui_parent
        d_str = str(dhms_widget.d).lstrip('0') or '0'

        boundaries = []
        pos = 0

        # Sign field (1 character)
        boundaries.append((pos, pos + 1, DhmsFieldType.SIGN))
        pos += 1  # Move to space after sign

        # Days field (variable length)
        # Include space before first digit for insertion
        # Include one extra position after last digit for appending
        boundaries.append((pos, pos + 1 + len(d_str) + 1, DhmsFieldType.DAYS))
        pos += 1 + len(d_str) + 3  # Skip space, digits, and " / "

        # Hours field (2 digits)
        boundaries.append((pos, pos + 2, DhmsFieldType.HOURS))
        pos += 3  # Skip ":"

        # Minutes field (2 digits)
        boundaries.append((pos, pos + 2, DhmsFieldType.MINUTES))
        pos += 3  # Skip ":"

        # Seconds field (2 digits)
        boundaries.append((pos, pos + 2, DhmsFieldType.SECONDS))
        pos += 3  # Skip "."

        # Milliseconds field (3 digits)
        boundaries.append((pos, pos + 3, DhmsFieldType.MILLISECONDS))

        return boundaries

    def handle_sign_keys(self, event: QKeyEvent):
        """Handle +/- keys to set sign"""
        key = event.key()
        dhms_widget: 'DhmsWidget' = self.gui_parent

        if key == Qt.Key_Plus:
            dhms_widget.set_sign(False)
            return True
        elif key == Qt.Key_Minus:
            dhms_widget.set_sign(True)
            return True
        return False

    def handle_backspace_delete(self, event: QKeyEvent):
        """Handle backspace/delete with special days field behavior"""
        key = event.key()

        # Handle backspace - in days field, delete char before cursor
        # In time fields, just move cursor left
        if key == Qt.Key_Backspace:
            field_type, _, _ = self.get_current_field()
            if field_type == DhmsFieldType.DAYS:
                self.handle_backspace_in_days()
            else:
                # In time fields, backspace acts like left arrow
                self.move_cursor_left()
            return True

        # Handle delete - in days field, delete char at cursor
        # In time fields, just move cursor right
        if key == Qt.Key_Delete:
            field_type, _, _ = self.get_current_field()
            if field_type == DhmsFieldType.DAYS:
                self.handle_delete_in_days()
            else:
                # In time fields, delete acts like right arrow
                self.move_cursor_right()
            return True

        return False

    def handle_field_navigation_keys(self, event: QKeyEvent):
        """Handle field navigation with / or ."""
        key = event.key()

        # Handle field navigation with / or .
        # Only advance from days field with slash/period
        if key in (Qt.Key_Slash, Qt.Key_Period):
            field_type, _, _ = self.get_current_field()
            if field_type == DhmsFieldType.DAYS:
                self.advance_to_next_field()
            # In time fields, these keys do nothing
            return True

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

        # Draw background
        painter.fillRect(qtobj.rect(), bg_color)

        # Draw each character
        x = 5  # Left margin
        y = (qtobj.height() + char_height) // 2 - fm.descent()

        for i, char in enumerate(display_str):
            # Draw block cursor as background for current position
            if i == self.cursor_pos and qtobj.hasFocus():
                painter.fillRect(x, y - fm.ascent(), char_width,
                                 char_height,
                                 highlight_color)
                painter.setPen(highlight_text_color)
            else:
                painter.setPen(text_color)

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
        dhms_widget: 'DhmsWidget' = self.gui_parent

        # Handle +/- to set sign
        if key == Qt.Key_Plus:
            dhms_widget.set_sign(False)
            return True
        elif key == Qt.Key_Minus:
            dhms_widget.set_sign(True)
            return True

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

        # Handle backspace - in days field, delete char before cursor
        # In time fields, just move cursor left
        if key == Qt.Key_Backspace:
            field_type, _, _ = self.get_current_field()
            if field_type == DhmsFieldType.DAYS:
                self.handle_backspace_in_days()
            else:
                # In time fields, backspace acts like left arrow
                self.move_cursor_left()
            return True

        # Handle delete - in days field, delete char at cursor
        # In time fields, just move cursor right
        if key == Qt.Key_Delete:
            field_type, _, _ = self.get_current_field()
            if field_type == DhmsFieldType.DAYS:
                self.handle_delete_in_days()
            else:
                # In time fields, delete acts like right arrow
                self.move_cursor_right()
            return True

        # Handle field navigation with / or .
        # Only advance from days field with slash/period
        if key in (Qt.Key_Slash, Qt.Key_Period):
            field_type, _, _ = self.get_current_field()
            if field_type == DhmsFieldType.DAYS:
                self.advance_to_next_field()
            # In time fields, these keys do nothing
            return True

        # Handle Page Up/Down - behave like left/right arrows for
        # easy numpad navigation
        if key == Qt.Key_PageUp:
            self.move_cursor_right()
            return True
        elif key == Qt.Key_PageDown:
            self.move_cursor_left()
            return True

        # # Alternative: Page Up/Down to skip between fields
        # if key == Qt.Key_PageUp:
        #     self.advance_to_next_field()
        #     return True
        # elif key == Qt.Key_PageDown:
        #     self.advance_to_previous_field()
        #     return True

        # Handle up/down arrows to increment/decrement digit
        if key == Qt.Key_Up:
            if event.modifiers() & Qt.ControlModifier:
                self.increment_single_digit()
            else:
                self.increment_digit()
            return True
        elif key == Qt.Key_Down:
            if event.modifiers() & Qt.ControlModifier:
                self.decrement_single_digit()
            else:
                self.decrement_digit()
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

    def handle_backspace_in_days(self):
        """Handle backspace in days field - delete char before cursor"""
        dhms_widget: 'DhmsWidget' = self.gui_parent
        field_type, start, end = self.get_current_field()

        if field_type != DhmsFieldType.DAYS:
            return

        pos_in_field = self.cursor_pos - start

        # Can't delete if at start of field (position 0 is space)
        if pos_in_field <= 1:
            return

        # Get current days value as string
        d_str = str(dhms_widget.d).lstrip('0') or '0'

        # Adjust position for the space (subtract 1)
        digit_pos = pos_in_field - 1

        # Remove character before cursor
        new_d_str = d_str[:digit_pos - 1] + d_str[digit_pos:]

        # Update days value
        dhms_widget.d = int(new_d_str) if new_d_str else 0

        # Move cursor left
        self.cursor_pos = max(start + 1, self.cursor_pos - 1)
        self.qtobj.update()

    def handle_delete_in_days(self):
        """Handle delete in days field - delete char at cursor"""
        dhms_widget: 'DhmsWidget' = self.gui_parent
        field_type, start, end = self.get_current_field()

        if field_type != DhmsFieldType.DAYS:
            return

        pos_in_field = self.cursor_pos - start

        # Get current days value as string
        d_str = str(dhms_widget.d).lstrip('0') or '0'

        # If cursor is on space, don't delete
        if pos_in_field == 0:
            return

        # Adjust position for the space (subtract 1)
        digit_pos = pos_in_field - 1

        # Can't delete if at end of field
        if digit_pos >= len(d_str):
            return

        # Remove character at cursor
        new_d_str = d_str[:digit_pos] + d_str[digit_pos + 1:]

        # Update days value
        dhms_widget.d = int(new_d_str) if new_d_str else 0

        # Keep cursor at same position
        self.qtobj.update()

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

    def advance_to_previous_field(self):
        """Move cursor to the start of the previous field"""
        field_type, start, end = self.get_current_field()
        boundaries = self.get_field_boundaries()

        # Find current field index
        for i, (s, e, ft) in enumerate(boundaries):
            if ft == field_type:
                if i > 0:
                    # Move to start of previous field
                    self.cursor_pos = boundaries[i - 1][0]
                    self.qtobj.update()
                break

    def increment_digit(self):
        """Increment the digit under the cursor"""
        field_type, start, end = self.get_current_field()
        dhms_widget: 'DhmsWidget' = self.gui_parent

        # Get current field value
        if field_type == DhmsFieldType.SIGN:
            # Toggle sign: + becomes -, - becomes +
            dhms_widget.sign = -dhms_widget.sign
        elif field_type == DhmsFieldType.DAYS:
            new_val = dhms_widget.d + 1
            dhms_widget.d = new_val
        elif field_type == DhmsFieldType.HOURS:
            new_val = (dhms_widget.h + 1) % 24
            dhms_widget.h = new_val
        elif field_type == DhmsFieldType.MINUTES:
            new_val = (dhms_widget.m + 1) % 60
            dhms_widget.m = new_val
        elif field_type == DhmsFieldType.SECONDS:
            s_int = int(dhms_widget.s)
            s_frac = dhms_widget.s - s_int
            new_s_int = (s_int + 1) % 60
            dhms_widget.s = new_s_int + s_frac
        elif field_type == DhmsFieldType.MILLISECONDS:
            s_int = int(dhms_widget.s)
            s_frac = dhms_widget.s - s_int
            ms = int(round(s_frac * 1000))
            new_ms = (ms + 1) % 1000
            dhms_widget.s = s_int + new_ms / 1000.0

        self.qtobj.update()

    def decrement_digit(self):
        """Decrement the digit under the cursor"""
        field_type, start, end = self.get_current_field()
        dhms_widget: 'DhmsWidget' = self.gui_parent

        # Get current field value
        if field_type == DhmsFieldType.SIGN:
            # Toggle sign: + becomes -, - becomes +
            dhms_widget.sign = -dhms_widget.sign
        elif field_type == DhmsFieldType.DAYS:
            new_val = max(0, dhms_widget.d - 1)
            dhms_widget.d = new_val
        elif field_type == DhmsFieldType.HOURS:
            new_val = (dhms_widget.h - 1) % 24
            dhms_widget.h = new_val
        elif field_type == DhmsFieldType.MINUTES:
            new_val = (dhms_widget.m - 1) % 60
            dhms_widget.m = new_val
        elif field_type == DhmsFieldType.SECONDS:
            s_int = int(dhms_widget.s)
            s_frac = dhms_widget.s - s_int
            new_s_int = (s_int - 1) % 60
            dhms_widget.s = new_s_int + s_frac
        elif field_type == DhmsFieldType.MILLISECONDS:
            s_int = int(dhms_widget.s)
            s_frac = dhms_widget.s - s_int
            ms = int(round(s_frac * 1000))
            new_ms = (ms - 1) % 1000
            dhms_widget.s = s_int + new_ms / 1000.0

        self.qtobj.update()

    def increment_single_digit(self):
        """Increment only the single digit under the cursor"""
        field_type, start, end = self.get_current_field()
        pos_in_field = self.cursor_pos - start
        dhms_widget: 'DhmsWidget' = self.gui_parent

        if field_type == DhmsFieldType.SIGN:
            # Toggle sign
            dhms_widget.sign = -dhms_widget.sign
            self.qtobj.update()
            return

        if field_type == DhmsFieldType.DAYS:
            if pos_in_field == 0:  # On space, do nothing
                return
            # Get current field value
            field_str = str(dhms_widget.d).lstrip('0') or '0'
            digit_pos = pos_in_field - 1  # Adjust for space
            if digit_pos >= len(field_str):  # On trailing space
                return
        else:
            # For time fields, get the field string
            if field_type == DhmsFieldType.HOURS:
                field_str = str(dhms_widget.h).zfill(2)
                digit_pos = pos_in_field
            elif field_type == DhmsFieldType.MINUTES:
                field_str = str(dhms_widget.m).zfill(2)
                digit_pos = pos_in_field
            elif field_type == DhmsFieldType.SECONDS:
                field_str = str(int(dhms_widget.s)).zfill(2)
                digit_pos = pos_in_field
            elif field_type == DhmsFieldType.MILLISECONDS:
                s_int = int(dhms_widget.s)
                s_frac = dhms_widget.s - s_int
                ms = int(round(s_frac * 1000))
                field_str = str(ms).zfill(3)
                digit_pos = pos_in_field

        # Increment the specific digit
        if digit_pos < len(field_str):
            field_list = list(field_str)
            current_digit = int(field_list[digit_pos])
            new_digit = (current_digit + 1) % 10
            field_list[digit_pos] = str(new_digit)
            new_field_str = ''.join(field_list)

            # Apply validation and update
            new_val = int(new_field_str)
            if field_type == DhmsFieldType.DAYS:
                dhms_widget.d = new_val
            elif field_type == DhmsFieldType.HOURS:
                if new_val <= 23:
                    dhms_widget.h = new_val
            elif field_type == DhmsFieldType.MINUTES:
                if new_val <= 59:
                    dhms_widget.m = new_val
            elif field_type == DhmsFieldType.SECONDS:
                if new_val <= 59:
                    s_frac = dhms_widget.s - int(dhms_widget.s)
                    dhms_widget.s = new_val + s_frac
            elif field_type == DhmsFieldType.MILLISECONDS:
                s_int = int(dhms_widget.s)
                dhms_widget.s = s_int + new_val / 1000.0

        self.qtobj.update()

    def decrement_single_digit(self):
        """Decrement only the single digit under the cursor"""
        field_type, start, end = self.get_current_field()
        pos_in_field = self.cursor_pos - start
        dhms_widget: 'DhmsWidget' = self.gui_parent

        if field_type == DhmsFieldType.SIGN:
            # Toggle sign
            dhms_widget.sign = -dhms_widget.sign
            self.qtobj.update()
            return

        if field_type == DhmsFieldType.DAYS:
            if pos_in_field == 0:  # On space, do nothing
                return
            # Get current field value
            field_str = str(dhms_widget.d).lstrip('0') or '0'
            digit_pos = pos_in_field - 1  # Adjust for space
            if digit_pos >= len(field_str):  # On trailing space
                return
        else:
            # For time fields, get the field string
            if field_type == DhmsFieldType.HOURS:
                field_str = str(dhms_widget.h).zfill(2)
                digit_pos = pos_in_field
            elif field_type == DhmsFieldType.MINUTES:
                field_str = str(dhms_widget.m).zfill(2)
                digit_pos = pos_in_field
            elif field_type == DhmsFieldType.SECONDS:
                field_str = str(int(dhms_widget.s)).zfill(2)
                digit_pos = pos_in_field
            elif field_type == DhmsFieldType.MILLISECONDS:
                s_int = int(dhms_widget.s)
                s_frac = dhms_widget.s - s_int
                ms = int(round(s_frac * 1000))
                field_str = str(ms).zfill(3)
                digit_pos = pos_in_field

        # Decrement the specific digit
        if digit_pos < len(field_str):
            field_list = list(field_str)
            current_digit = int(field_list[digit_pos])
            new_digit = (current_digit - 1) % 10
            field_list[digit_pos] = str(new_digit)
            new_field_str = ''.join(field_list)

            # Apply validation and update
            new_val = int(new_field_str)
            if field_type == DhmsFieldType.DAYS:
                dhms_widget.d = new_val
            elif field_type == DhmsFieldType.HOURS:
                if new_val <= 23:
                    dhms_widget.h = new_val
            elif field_type == DhmsFieldType.MINUTES:
                if new_val <= 59:
                    dhms_widget.m = new_val
            elif field_type == DhmsFieldType.SECONDS:
                if new_val <= 59:
                    s_frac = dhms_widget.s - int(dhms_widget.s)
                    dhms_widget.s = new_val + s_frac
            elif field_type == DhmsFieldType.MILLISECONDS:
                s_int = int(dhms_widget.s)
                dhms_widget.s = s_int + new_val / 1000.0

        self.qtobj.update()

    def insert_digit(self, digit: str):
        """Insert a digit at the cursor position (overtype mode)"""
        field_type, start, end = self.get_current_field()
        pos_in_field = self.cursor_pos - start
        dhms_widget: 'DhmsWidget' = self.gui_parent

        # Validate digit based on position and field type
        if not self.validate_digit(digit, field_type, pos_in_field):
            return

        # Get current field value as string
        if field_type == DhmsFieldType.SIGN:
            field_str = '-' if dhms_widget.sign < 0 else '+'
        elif field_type == DhmsFieldType.DAYS:
            field_str = str(dhms_widget.d).lstrip('0') or '0'
        elif field_type == DhmsFieldType.HOURS:
            field_str = str(dhms_widget.h).zfill(2)
        elif field_type == DhmsFieldType.MINUTES:
            field_str = str(dhms_widget.m).zfill(2)
        elif field_type == DhmsFieldType.SECONDS:
            field_str = str(int(dhms_widget.s)).zfill(2)
        elif field_type == DhmsFieldType.MILLISECONDS:
            s_int = int(dhms_widget.s)
            s_frac = dhms_widget.s - s_int
            ms = int(round(s_frac * 1000))
            field_str = str(ms).zfill(3)

        # Replace character at position
        field_list = list(field_str)
        if field_type == DhmsFieldType.DAYS:
            # For days field:
            # pos_in_field 0 = space before first digit (INSERT)
            # pos_in_field 1-N = on actual digits (OVERTYPE)
            # pos_in_field N+1 = space after last digit (APPEND)
            if pos_in_field == 0:
                # Cursor on space before first digit: INSERT at beginning
                field_list.insert(0, digit)
            elif pos_in_field <= len(field_list):
                # Cursor on actual digit: OVERTYPE
                digit_pos = pos_in_field - 1  # Subtract 1 for the space
                field_list[digit_pos] = digit
            else:
                # Cursor on space after last digit: APPEND
                field_list.append(digit)
        else:
            # For other fields, use overtype mode
            if pos_in_field < len(field_list):
                field_list[pos_in_field] = digit
            else:
                # Should not happen for fixed-length fields
                field_list.append(digit)

        new_field_str = ''.join(field_list)

        # Update the field value
        if field_type == DhmsFieldType.SIGN:
            dhms_widget.sign = -1 if new_field_str == '-' else 1
        elif field_type == DhmsFieldType.DAYS:
            dhms_widget.d = int(new_field_str)
        elif field_type == DhmsFieldType.HOURS:
            dhms_widget.h = int(new_field_str)
        elif field_type == DhmsFieldType.MINUTES:
            dhms_widget.m = int(new_field_str)
        elif field_type == DhmsFieldType.SECONDS:
            s_frac = dhms_widget.s - int(dhms_widget.s)
            dhms_widget.s = int(new_field_str) + s_frac
        elif field_type == DhmsFieldType.MILLISECONDS:
            s_int = int(dhms_widget.s)
            dhms_widget.s = s_int + int(new_field_str) / 1000.0

        # Handle cursor movement after insert
        if field_type == DhmsFieldType.SIGN:
            # Sign field: stay in place after changing sign
            pass
        elif field_type == DhmsFieldType.DAYS:
            # In days field, cursor movement depends on insertion type
            if pos_in_field == 0:
                # Inserted at begin: move cursor right by 1 to stay on next
                self.move_cursor_right()
            else:
                # Overtyped or appended: move cursor right normally
                self.move_cursor_right()
        else:
            # In time fields, move cursor right or auto-advance
            if self.cursor_pos < end - 1:
                self.move_cursor_right()
            else:
                # At end of field, advance to next field
                self.advance_to_next_field()

        self.qtobj.update()

    def validate_digit(self, digit: str, field_type: DhmsFieldType,
                       pos_in_field: int):
        """Validate a digit based on field type and position within
        field"""
        dhms_widget: 'DhmsWidget' = self.gui_parent

        if field_type == DhmsFieldType.SIGN:
            # Sign field only accepts + or - characters
            return digit in ['+', '-']

        d_val = int(digit)

        if field_type == DhmsFieldType.DAYS:
            # Days: any digit is valid
            return True

        elif field_type == DhmsFieldType.HOURS:
            # Hours: first digit 0-2, second digit depends on first
            if pos_in_field == 0:
                return d_val <= 2
            elif pos_in_field == 1:
                first_digit = int(str(dhms_widget.h).zfill(2)[0])
                if first_digit == 2:
                    return d_val <= 3
                return True

        elif field_type == DhmsFieldType.MINUTES:
            # Minutes: first digit 0-5, second digit 0-9
            if pos_in_field == 0:
                return d_val <= 5
            return True

        elif field_type == DhmsFieldType.SECONDS:
            # Seconds: first digit 0-5, second digit 0-9 (max 59)
            if pos_in_field == 0:
                return d_val <= 5
            elif pos_in_field == 1:
                return True

        elif field_type == DhmsFieldType.MILLISECONDS:
            # Milliseconds: any digit 0-9 is valid
            return True

        return False


class DhmsWidget(QtWidgetWrapper[QGroupBox]):
    """New DHMS widget with single custom display"""

    def __init__(self, gui_parent: GuiWidgetParentType = None,
                 d: int = 0, h: int = 0, m: int = 0, s: int = 0,
                 sign: int = 1,
                 *qtobj_args, **qtobj_kwargs):
        self.set_dhms(d, h, m, s, sign, False)
        super().__init__(gui_parent, *qtobj_args, **qtobj_kwargs)

    @log_func_call
    def create_qtobj(self, *args, **kwargs):
        parent_qtobj: GuiWidgetParentType = self.gui_parent.qtobj

        frame = QGroupBox(parent_qtobj)
        frame.setTitle('DHMS')
        frame.setFixedWidth(195)
        frame.setMaximumHeight(60)
        self.frame = frame

        layout = QHBoxLayout()
        frame.setLayout(layout)
        self.layout = layout

        # Custom display widget
        display = DhmsDisplayWidget(self, parent_qtobj=frame)
        layout.addWidget(display.qtobj)
        self.display = display

        # Set tooltip with keyboard shortcuts
        tooltip = ("Overtype mode except spaces before/after days\n"
                   "PgUp/Right — move cursor right\n"
                   "PgDn/Left — move cursor left\n"
                   "/ or . — advance from days to time\n"
                   "Up/Down — increment/decrement field\n"
                   "Ctrl+Up/Down — increment/decrement digit\n"
                   "+/- — set sign")
        display.qtobj.setToolTip(tooltip)

        return frame

    def get_dhms(self):
        """Get current DHMS values"""
        return [self.d, self.h, self.m, self.s, self.sign]

    def set_dhms(self, d: int, h: int, m: int, s: float, sign: int,
                 update_text: bool = True):
        """Set DHMS values"""
        self.d = d
        self.h = h
        self.m = m
        self.s = s
        self.sign = sign
        if update_text and hasattr(self, 'display'):
            self.display.qtobj.update()

    def set_sign(self, minus: bool):
        """Set sign (True for negative, False for positive)"""
        self.sign = 1 - 2*minus
        if hasattr(self, 'display'):
            self.display.qtobj.update()
