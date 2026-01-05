from ...logging import log_func_call
from ..qt import (
    QGroupBox, QHBoxLayout, QFrame, Qt, QObject, QEvent, QKeyEvent, QPainter,
    QPaintEvent, QMouseEvent, QFocusEvent, QLineEdit, QPalette, QFontMetrics,
)
from . import QtWidgetWrapper, GuiWidgetParentType


class TimeFieldDisplayWidget(QtWidgetWrapper[QFrame]):
    "Base class for time/date field display widgets with common functionality"

    def __init__(self, gui_parent: 'TimeFieldWidget',
                 *qtobj_args, **qtobj_kwargs):
        # Initialize cursor position (character index in display string)
        self.cursor_pos = 0
        super().__init__(gui_parent, *qtobj_args, **qtobj_kwargs)

    def create_qtobj(self, *args, parent_qtobj: QGroupBox, **kwargs):
        qtobj = QFrame(parent_qtobj)
        qtobj.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        qtobj.setFocusPolicy(Qt.StrongFocus)
        qtobj.setMinimumWidth(self.get_min_width())
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

        class TimeFieldEventFilter(QObject):
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

        event_filter = TimeFieldEventFilter()
        qtobj.installEventFilter(event_filter)
        self.event_filter = event_filter

        return qtobj

    def get_min_width(self):
        """Return minimum width for the widget"""
        raise NotImplementedError

    def get_display_string(self):
        """Build the display string from parent's values"""
        raise NotImplementedError

    def get_field_boundaries(self):
        """Return list of (start, end, field_type) tuples"""
        raise NotImplementedError

    def get_field_error_ranges(self):
        "Return list of (start, end) ranges that should be error highlighted"
        raise NotImplementedError

    def get_current_field(self):
        """Get the field type and boundaries that the cursor is in"""
        boundaries = self.get_field_boundaries()
        for start, end, field_type in boundaries:
            if start <= self.cursor_pos < end:
                return field_type, start, end
        # Default to first field if cursor is out of bounds
        return boundaries[0][2], boundaries[0][0], boundaries[0][1]

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

        # Get error ranges for highlighting
        error_ranges = self.get_field_error_ranges()

        # Draw each character
        x = 5  # Left margin
        y = (qtobj.height() + char_height) // 2 - fm.descent()

        for i, char in enumerate(display_str):
            # Check if this character is in an error range
            in_error_range = any(start <= i < end
                                 for start, end in error_ranges)

            # Determine colors for this character
            if i == self.cursor_pos and qtobj.hasFocus():
                # Block cursor
                char_bg_color = highlight_color
                char_text_color = highlight_text_color
                painter.fillRect(x, y - fm.ascent(), char_width,
                                 char_height, char_bg_color)
            elif in_error_range:
                # Error highlighting - hardcoded red/white for visibility
                from pyrandyos.gui.qt import QColor
                char_bg_color = QColor(255, 0, 0)  # Red background
                char_text_color = QColor(255, 255, 255)  # White text
                painter.fillRect(x, y - fm.ascent(), char_width,
                                 char_height, char_bg_color)
            else:
                # Normal colors
                char_text_color = text_color

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

        # Handle custom +/- keys for signed fields (can be overridden)
        if self.handle_sign_keys(event):
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

        # Handle backspace/delete (can be overridden for custom behavior)
        if self.handle_backspace_delete(event):
            return True

        # Handle special field navigation keys (can be overridden)
        if self.handle_field_navigation_keys(event):
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

    def handle_sign_keys(self, event: QKeyEvent):
        """Handle +/- keys for signed fields. Override for custom behavior."""
        return False  # Base implementation does nothing

    def handle_backspace_delete(self, event: QKeyEvent):
        """Handle backspace/delete keys. Override for custom behavior."""
        key = event.key()
        # Default: backspace/delete act like cursor movement
        if key == Qt.Key_Backspace:
            self.move_cursor_left()
            return True
        elif key == Qt.Key_Delete:
            self.move_cursor_right()
            return True
        return False

    def handle_field_navigation_keys(self, event: QKeyEvent):
        "Handle special field navigation keys. Override for custom behavior."
        return False  # Base implementation does nothing

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
        raise NotImplementedError

    def decrement_field(self):
        """Decrement the entire field under the cursor"""
        raise NotImplementedError

    def increment_single_digit(self):
        """Increment only the single digit under the cursor"""
        field_type, start, end = self.get_current_field()
        pos_in_field = self.cursor_pos - start

        # Get the field string
        field_str = self.get_field_string(field_type)
        if not field_str:
            return

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
        if not field_str:
            return

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

    def insert_digit(self, digit: str):
        """Insert a digit at the cursor position (overtype mode)"""
        field_type, start, end = self.get_current_field()
        pos_in_field = self.cursor_pos - start

        # Validate digit based on position and field type
        if not self.validate_digit(digit, field_type, pos_in_field):
            return

        # Get current field value as string
        field_str = self.get_field_string(field_type)
        if not field_str:
            return

        # Handle special insertion logic (can be overridden)
        if self.handle_special_insertion(digit, field_type, pos_in_field,
                                         field_str):
            return

        # Default: Replace character at position (overtype mode)
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

    def get_field_string(self, field_type):
        """Get the string representation of a field"""
        raise NotImplementedError

    def update_field_value(self, field_type, new_val: int):
        """Update a field value with validation"""
        raise NotImplementedError

    def handle_special_insertion(self, digit: str, field_type,
                                 pos_in_field: int, field_str: str):
        """
        Handle special insertion logic (e.g., days field).
        Return True if handled.
        """
        return False  # Base implementation does nothing

    def validate_digit(self, digit: str, field_type, pos_in_field: int):
        """Validate a digit based on field type and position within field"""
        raise NotImplementedError


class TimeFieldWidget(QtWidgetWrapper[QGroupBox]):
    """Base class for time/date field widgets"""

    @log_func_call
    def create_qtobj(self, *args, **kwargs):
        parent_qtobj: GuiWidgetParentType = self.gui_parent.qtobj

        frame = QGroupBox(parent_qtobj)
        frame.setTitle(self.get_title())
        frame.setMaximumWidth(self.get_max_width())
        frame.setMaximumHeight(60)
        self.frame = frame

        layout = QHBoxLayout()
        frame.setLayout(layout)
        self.layout = layout

        # Custom display widget
        display = self.create_display_widget(parent_qtobj=frame)
        layout.addWidget(display.qtobj)
        self.display = display

        return frame

    def get_title(self):
        """Return the title for the group box"""
        raise NotImplementedError

    def get_max_width(self):
        """Return maximum width for the widget"""
        raise NotImplementedError

    def create_display_widget(self, parent_qtobj):
        """Create the appropriate display widget"""
        raise NotImplementedError
