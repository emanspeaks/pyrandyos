from ....logging import log_func_call
from ...qt import (
    QGroupBox, QHBoxLayout, QFrame, Qt, QObject, QEvent, QKeyEvent, QPainter,
    QPaintEvent, QMouseEvent, QFocusEvent, QLineEdit, QPalette, QFontMetrics,
    QColor,
)
from .. import QtWidgetWrapper, GuiWidgetParentType
from .fields import TimeField, LabelField


class BaseTimeEditorWidget(QtWidgetWrapper[QGroupBox]):
    """Base class for time/date field widgets"""

    def get_title(self) -> str:
        """Return the title for the group box"""
        raise NotImplementedError

    def get_tooltip(self):
        raise NotImplementedError

    def handle_sign_keys(self, event: QKeyEvent):
        """Handle +/- keys for signed fields. Override for custom behavior."""
        return False  # Base implementation does nothing

    def handle_field_navigation_keys(self, event: QKeyEvent):
        "Handle special field navigation keys. Override for custom behavior."
        return False  # Base implementation does nothing

    def left_margin(self):
        return 5

    def __init__(self, gui_parent: GuiWidgetParentType,
                 *qtobj_args, **qtobj_kwargs):
        # Initialize cursor position (character index in display string)
        self.cursor_pos = 0
        self.fields: list[TimeField] = []
        super().__init__(gui_parent, *qtobj_args, **qtobj_kwargs)

    @log_func_call
    def create_qtobj(self, *args, **kwargs):
        parent_qtobj: GuiWidgetParentType = self.gui_parent.qtobj

        frame = QGroupBox(parent_qtobj)
        frame.setTitle(self.get_title())
        frame.setFixedWidth(195)
        frame.setMaximumHeight(60)
        self.frame = frame

        layout = QHBoxLayout()
        frame.setLayout(layout)
        self.layout = layout

        self.create_display_widget()
        return frame

    def create_display_widget(self):
        """Create the appropriate display widget"""
        parent = self.frame
        layout = self.layout

        # Use QLineEdit palette colors for consistent theming
        line_edit_palette = QLineEdit().palette()

        display = QFrame(parent)
        display.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        display.setFocusPolicy(Qt.StrongFocus)
        display.setMinimumWidth(170)
        display.setMinimumHeight(25)
        display.setAutoFillBackground(True)
        display.setPalette(line_edit_palette)
        display.setToolTip(self.get_tooltip())
        layout.addWidget(display)
        self.display = display

        key_callback = self.handle_key_press
        paint_callback = self.handle_paint
        mouse_callback = self.handle_mouse_press
        focus_in_callback = self.handle_focus_in

        class TimeEditorEventFilter(QObject):
            def eventFilter(self, obj: QObject, event: QEvent,
                            qtobj=display, key_cb=key_callback,
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

        event_filter = TimeEditorEventFilter()
        display.installEventFilter(event_filter)
        self.event_filter = event_filter

    def get_display_string(self):
        """Build the display string from parent's values"""
        s = ''
        for x in self.fields:
            s += str(x)
        return s

    def get_field_error_chars(self):
        errors = list()
        for x in self.fields:
            errors += x.invalid_chars(True)

        return errors

    def all_valid_inputs(self):
        return all(f.valid() for f in self.fields)

    def handle_paint(self, event: QPaintEvent):
        """Custom paint handler to draw the text with block cursor"""
        qtobj = self.display
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
        # Error highlighting - hardcoded red/white for visibility
        error_bg_color = QColor(255, 0, 0)  # Red background
        error_bg_focus_color = QColor(255, 127, 0)  # Red background
        error_text_color = QColor(255, 255, 255)  # White text

        # Draw background
        painter.fillRect(qtobj.rect(), bg_color)

        # Get error chars for highlighting
        error_chars = self.get_field_error_chars()

        # Draw each character
        x = self.left_margin()
        y = (qtobj.height() + char_height) // 2 - fm.descent()

        for i, char in enumerate(display_str):
            char_bg_color = None
            char_text_color = text_color

            # Check if this character is in an error range
            in_error_range = i in error_chars
            if in_error_range:
                char_bg_color = error_bg_color
                char_text_color = error_text_color

            # Determine colors for this character
            if i == self.cursor_pos and qtobj.hasFocus():
                char_text_color = highlight_text_color
                char_bg_color = (error_bg_focus_color if in_error_range
                                 else highlight_color)

            if char_bg_color:
                painter.fillRect(x, y - fm.ascent(), char_width,
                                 char_height, char_bg_color)

            painter.setPen(char_text_color)
            painter.drawText(x, y, char)
            x += char_width

        painter.end()

    def get_editable_chars(self):
        valid_positions = []
        for f in self.fields:
            if f.editable():
                valid_positions.extend(range(*f.bounds()))

        return valid_positions

    def handle_mouse_press(self, event: QMouseEvent):
        """Handle mouse clicks to position cursor"""
        # Calculate which character was clicked
        # Use same font as painting to get accurate metrics
        font = self.gui_app.get_monofont()
        font.setPointSize(10)
        fm = QFontMetrics(font)
        char_width = fm.horizontalAdvance('0')

        click_x = event.x() - self.left_margin()
        char_index = max(0, click_x // char_width)

        # Clamp to valid positions (only on actual digits)
        valid_positions = self.get_editable_chars()

        # Find closest valid position
        if char_index < max(valid_positions):
            if char_index in valid_positions:
                self.set_cursor_pos(char_index)

            else:
                # Find closest valid position
                closest = min(valid_positions,
                              key=lambda p: abs(p - char_index))
                self.set_cursor_pos(closest)

        else:
            # Clicked past the end, go to last valid position
            self.set_cursor_pos(max(valid_positions))

        return True

    def handle_focus_in(self, event: QFocusEvent):
        """Handle focus in to ensure cursor is visible"""
        reason = event.reason()
        if reason == Qt.TabFocusReason:
            self.set_cursor_pos(min(self.get_editable_chars()))

        elif reason == Qt.BacktabFocusReason:
            self.set_cursor_pos(max(self.get_editable_chars()))
            self.set_cursor_pos(self.get_current_field().start_char())

        self.display.update()

    def handle_tab(self, event: QKeyEvent):
        f = self.get_current_field()
        key = event.key()
        if key == Qt.Key_Backtab and f.prev:
            self.advance_to_prev_field()
            return True
        if key == Qt.Key_Tab and f.nxt:
            self.advance_to_next_field()
            return True

        # Allow Tab for normal focus navigation
        return False

    def handle_key_press(self, event: QKeyEvent):
        """Handle key press events"""
        key = event.key()
        text = event.text()

        # Handle navigation keys
        if key == Qt.Key_Left:
            self.move_cursor_left()
            return True
        if key == Qt.Key_Right:
            self.move_cursor_right()
            return True
        if key == Qt.Key_Home:
            self.set_cursor_pos(min(self.get_editable_chars()))
            return True
        if key == Qt.Key_End:
            self.set_cursor_pos(max(self.get_editable_chars()))
            return True

        # Handle Page Up/Down - behave like left/right arrows for
        # easy numpad navigation
        if key == Qt.Key_PageUp:
            self.move_cursor_right()
            return True
        elif key == Qt.Key_PageDown:
            self.move_cursor_left()
            return True

        # Handle special field navigation keys (can be overridden)
        if self.handle_field_navigation_keys(event):
            return True

        # Handle backspace/delete (can be overridden for custom behavior)
        if self.handle_backspace_delete(event):
            return True

        # Handle custom +/- keys for signed fields (can be overridden)
        if self.handle_sign_keys(event):
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
            self.write_text(text)
            return True

        # Handle tab
        if key in (Qt.Key_Tab, Qt.Key_Backtab):
            # Allow Tab for focus navigation
            return self.handle_tab(event)

        # Filter out all other keys
        return True

    def get_current_field(self):
        """Get the field type and boundaries that the cursor is in"""
        for f in self.fields:
            start, end = f.bounds()
            if start <= self.cursor_pos < end:
                return f

        # Default to first field if cursor is out of bounds
        return self.fields[0]

    def handle_backspace_delete(self, event: QKeyEvent):
        """Handle backspace/delete keys. Override for custom behavior."""
        key = event.key()
        if key == Qt.Key_Backspace:
            self.get_current_field().handle_backspace()
            return True
        if key == Qt.Key_Delete:
            self.get_current_field().handle_delete()
            return True
        return False

    def set_cursor_pos(self, pos: int):
        self.cursor_pos = pos
        self.display.update()

    def move_cursor_left(self):
        """Move cursor one position left, skipping separators"""
        valid_positions = self.get_editable_chars()
        cursor = self.cursor_pos
        if cursor in valid_positions:
            current_idx = valid_positions.index(cursor)

        else:
            current_idx = 0

        if current_idx > 0:
            self.set_cursor_pos(valid_positions[current_idx - 1])

    def move_cursor_right(self):
        """Move cursor one position right, skipping separators"""
        valid_positions = self.get_editable_chars()
        cursor = self.cursor_pos
        if cursor in valid_positions:
            current_idx = valid_positions.index(cursor)

        else:
            current_idx = 0

        if current_idx < len(valid_positions) - 1:
            self.set_cursor_pos(valid_positions[current_idx + 1])

    def advance_to_next_field(self):
        """Move cursor to the start of the next field"""
        f = self.get_current_field()
        nxt = f.nxt
        while nxt and not nxt.editable():
            f = nxt
            nxt = f.nxt

        if nxt:
            # Move to start of next field
            self.set_cursor_pos(nxt.start_char())

    def advance_to_prev_field(self):
        """Move cursor to the start of the prev field"""
        f = self.get_current_field()
        prev = f.prev
        while prev and not prev.editable():
            f = prev
            prev = f.prev

        if prev:
            # Move to start of prev field
            self.set_cursor_pos(prev.start_char())

    def increment_field(self):
        """Increment the entire field under the cursor"""
        self.get_current_field().incr()

    def decrement_field(self):
        """Decrement the entire field under the cursor"""
        self.get_current_field().decr()

    def increment_single_digit(self):
        """Increment only the single digit under the cursor"""
        self.get_current_field().incr_digit()

    def decrement_single_digit(self):
        """Decrement only the single digit under the cursor"""
        self.get_current_field().decr_digit()

    def write_text(self, text: str):
        """Insert a digit at the cursor position (overtype mode)"""
        self.get_current_field().write(text)

    def set_fields(self, *args: TimeField):
        fields = self.fields
        lastf: TimeField = None
        for f in args:
            if isinstance(f, str):
                f = LabelField(f)

            fields.append(f)
            f.parent = self
            f.prev = lastf
            if lastf:
                lastf.nxt = f

            lastf = f
