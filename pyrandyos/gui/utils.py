from pathlib import Path
from collections.abc import Callable
from contextlib import contextmanager
from base64 import b64encode

from ..logging import log_func_call  # , log_info
from .callback import qt_callback
from .widgets import GuiWidget, GuiWidgetView
from .qt import (
    QWidget, QToolButton, QSize, QIcon, QAction, QSizePolicy, QPainter,
    QBuffer, QByteArray, QSlider, Qt, QPushButton, QAbstractButton,
    QFontMetrics, QStyleOptionViewItem, QFont, QRect,
)
# from .gui_app import get_gui_app

GuiWidgetParent = QWidget | GuiWidget | GuiWidgetView
TEXTWORDWRAP = Qt.TextWordWrap
ALIGNLEFT = Qt.AlignLeft


def get_widget_parent_qtobj(parent: GuiWidgetParent) -> QWidget:
    """Get the Qt object of the parent widget."""
    if isinstance(parent, QWidget):
        return parent
    elif isinstance(parent, GuiWidget):
        return parent.gui_parent.qtobj
    elif isinstance(parent, GuiWidgetView):
        return parent.qtobj
    else:
        raise TypeError(f"Unsupported parent type: {type(parent)}")


@log_func_call
def load_icon(icon_path: str | Path) -> QIcon:
    return QIcon(Path(icon_path).as_posix())


# @log_func_call
# def create_toolbtn(parent: GuiWidgetParent,
#                    callback: Callable = None,
#                    sustain: bool = False, sus_repeat_interval_ms: int = 33,
#                    sus_delay_ms: int = 0, toggleable: bool = False,
#                    toggle_depressed: bool = False, enabled: bool = True):
#     button = QToolButton(get_widget_parent_qtobj(parent))
#     button.setEnabled(enabled)
#     if sustain:
#         button.setAutoRepeat(True)
#         button.setAutoRepeatInterval(sus_repeat_interval_ms)
#         button.setAutoRepeatDelay(sus_delay_ms)

#     if toggleable:
#         button.setCheckable(True)
#         button.setChecked(toggle_depressed)

#     if callback:
#         signal = button.toggled if toggleable else button.clicked
#         signal.connect(callback)

#     return button


# @log_func_call
# def create_icon_toolbtn(parent: GuiWidgetParent, size: QSize,
#                         icon: QIcon | str | Path,
#                         callback: Callable = None,
#                         sustain: bool = False,
#                         sus_repeat_interval_ms: int = 33,
#                         sus_delay_ms: int = 0, toggleable: bool = False,
#                         toggle_depressed: bool = False,
#                         enabled: bool = True):
#     if not isinstance(icon, QIcon):
#         icon = load_icon(icon)

#     button = create_toolbtn(parent, callback, sustain,
#                             sus_repeat_interval_ms,
#                             sus_delay_ms, toggleable, toggle_depressed,
#                             enabled)
#     button.setIcon(icon)
#     button.setIconSize(size)
#     button.setMinimumHeight(calculate_min_height(button, size))
#     _debug_dump_icon(icon, size, name=f"toolbtn_{icon}")
#     return button


# @log_func_call
# def create_text_toolbtn(parent: GuiWidgetParent, text: str,
#                         callback: Callable = None,
#                         sustain: bool = False,
#                         sus_repeat_interval_ms: int = 33,
#                         sus_delay_ms: int = 0, toggleable: bool = False,
#                         toggle_depressed: bool = False,
#                         enabled: bool = True):
#     button = create_toolbtn(parent, callback, sustain,
#                             sus_repeat_interval_ms,
#                             sus_delay_ms, toggleable, toggle_depressed,
#                             enabled)
#     button.setText(text)
#     return button


@log_func_call
def create_slider(parent: GuiWidgetParent, min_value: int,
                  max_value: int, value: int, callback: Callable = None):
    slide = QSlider(get_widget_parent_qtobj(parent))
    slide.setMinimum(min_value)
    slide.setMaximum(max_value)
    slide.setValue(value)
    # slide.setOrientation(orientation)
    # slide.setEnabled(enabled)

    if callback:
        slide.valueChanged.connect(qt_callback(callback))

    return slide


@log_func_call
def show_toolbtn_icon_and_text(btn: QToolButton):
    btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)


@log_func_call
def create_action(parent: GuiWidgetParent, text: str = "",
                  icon: QIcon | str | Path = None,
                  callback: Callable = None, enabled: bool = True,
                  tooltip: str = None, checkable: bool = False):
    action = QAction(get_widget_parent_qtobj(parent))
    if text:
        action.setIconText(text)

    if tooltip:
        action.setToolTip(tooltip)

    if icon:
        if not isinstance(icon, QIcon):
            icon = load_icon(icon)

        action.setIcon(icon)

    if callback:
        action.triggered.connect(qt_callback(callback))

    if checkable:
        action.setCheckable(True)

    action.setEnabled(enabled)
    return action


@log_func_call
def set_widget_sizepolicy_h_expanding(w: QWidget):
    w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)


@log_func_call
def set_widget_sizepolicy_v_expanding(w: QWidget):
    w.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)


@log_func_call
def set_widget_sizepolicy_hv_expanding(w: QWidget):
    w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


@log_func_call
def create_toolbar_expanding_spacer():
    spacer = QWidget()
    set_widget_sizepolicy_hv_expanding(spacer)
    return spacer


@contextmanager
def painter_context(painter: QPainter):
    painter.save()
    try:
        yield painter
    finally:
        painter.restore()


def qicon_to_data_uri(icon: QIcon, size: QSize) -> str:
    """Convert QIcon to data URI"""
    # Get pixmap from icon
    pixmap = icon.pixmap(size)

    # Convert to PNG bytes
    byte_array = QByteArray()
    buffer = QBuffer(byte_array)
    buffer.open(QBuffer.WriteOnly)
    pixmap.save(buffer, "PNG")

    # Encode as base64 data URI
    png_data = b64encode(byte_array.data()).decode('ascii')
    return f"data:image/png;base64,{png_data}"


@log_func_call
def create_button(parent: GuiWidgetParent,
                  callback: Callable = None,
                  sustain: bool = False, sus_repeat_interval_ms: int = 33,
                  sus_delay_ms: int = 0, toggleable: bool = False,
                  toggle_depressed: bool = False, enabled: bool = True):
    button = QPushButton(get_widget_parent_qtobj(parent))
    button.setEnabled(enabled)
    if sustain:
        button.setAutoRepeat(True)
        button.setAutoRepeatInterval(sus_repeat_interval_ms)
        button.setAutoRepeatDelay(sus_delay_ms)

    if toggleable:
        button.setCheckable(True)
        button.setChecked(toggle_depressed)

    if callback:
        signal = button.toggled if toggleable else button.clicked
        signal.connect(qt_callback(callback))

    return button


@log_func_call
def create_icon_button(parent: GuiWidgetParent, size: QSize,
                       icon: QIcon | str | Path,
                       callback: Callable = None,
                       caption: str = None,
                       sustain: bool = False,
                       sus_repeat_interval_ms: int = 33,
                       sus_delay_ms: int = 0, toggleable: bool = False,
                       toggle_depressed: bool = False, enabled: bool = True):
    if not isinstance(icon, QIcon):
        icon = load_icon(icon)

    button = create_button(parent, callback, sustain, sus_repeat_interval_ms,
                           sus_delay_ms, toggleable, toggle_depressed,
                           enabled)
    button.setIcon(icon)
    button.setIconSize(size)
    button.setMinimumHeight(calculate_min_height(button, size))
    # optional debug dump
    _debug_dump_icon(icon, size, name=caption)
    if caption:
        button.setText(caption)
    return button


def calculate_min_height(button: QAbstractButton, icon_size: QSize):
    """Calculate the minimum height for a button to accommodate its icon."""
    # Ensure the button is tall enough to vertically center the icon.
    # If the icon size is set explicitly in code (e.g. 32x32), the
    # QPushButton can be shorter than the icon which makes the icon
    # appear visually off-center. Set a sensible minimum height that
    # respects the icon height plus a small vertical padding.
    return max(button.sizeHint().height(), icon_size.height() + 6)


def _debug_dump_icon(icon: QIcon, size: QSize, name: str = None) -> None:
    from ..app import PyRandyOSApp
    if PyRandyOSApp.get('debug_dump_icons', False):
        tmpdir = PyRandyOSApp.mkdir_temp('icons')
        fname = f"icon_dump_{name or 'icon'}.png"
        pix = icon.pixmap(size)
        pix.save(str(tmpdir/fname), "PNG")


def wrap_text_to_width(text: str, bbox_callback: Callable[[str], QRect],
                       width: int):
    "Wrap text to fit within a specified width using the given font metrics."
    # gui = get_gui_app()
    # log_info(f"DPI: {gui.get_dpi()}")
    # log_info(f"DPI Scale: {gui.get_dpi_scale()}")
    # log_info(f"Window DPI: {gui.windows[0].gui_view.get_dpi()}")

    # compute column width
    if not text or width <= 0:
        return text

    def calc_width(s: str) -> int:
        return bbox_callback(s).width()

    # as-is original width
    test_width = calc_width(text)
    if test_width <= width:
        return text

    # Split text by existing newlines first, then wrap each line
    original_lines = text.splitlines()
    wrapped = []
    append_wrapped = wrapped.append
    for origline in original_lines:
        if not origline.strip():
            # Empty line - preserve it
            append_wrapped("")
            continue

        # Check if this line fits without wrapping
        test_width = calc_width(origline)
        if test_width <= width:
            append_wrapped(origline)
            continue

        # Apply word wrapping to this line
        curline = ""
        words = origline.split()

        def popword():
            return words.pop(0) if words else None

        w = popword()  # we already handled blank line, so should work
        while w:
            # Calculate width of current line + new word
            test_line = curline + (" " if curline else "") + w
            test_width = calc_width(test_line)
            # if it fits, i sits...try adding another word
            if test_width <= width:
                curline = test_line
                w = popword()
                continue
            # w pushed us over the limit, so break the line and start over
            if curline:
                append_wrapped(curline)
                curline = ""
                continue
            # we got a long single word, break by character
            w2 = ""
            for c in w:
                test_line = w2 + c
                test_width = calc_width(test_line)
                if test_width > width:
                    # c put us over the limit, flush w2
                    if w2:
                        append_wrapped(w2)
                        w2 = c
                    else:
                        # single char is too much, but we need at least 1
                        append_wrapped(c)
                        w2 = ""
                else:
                    w2 = test_line

            # curline is still blank if we got here because we are in
            # single word mode
            w = w2 if w2 else popword()

        if curline:
            append_wrapped(curline)

    return "\n".join(wrapped)


def calc_fontmetrics_bbox(font_metrics: QFontMetrics, s: str) -> QRect:
    return font_metrics.boundingRect(s)


def get_styled_text_bbox(widget: QWidget, font: QFont, text: str):
    style_option = QStyleOptionViewItem()
    style_option.font = font
    style_option.fontMetrics = QFontMetrics(font)
    # Get the style from your table widget
    style = widget.style()
    rect = style.itemTextRect(style_option.fontMetrics, QRect(), ALIGNLEFT,
                              True, text)
    return rect
