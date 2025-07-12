from pathlib import Path
from collections.abc import Callable
from contextlib import contextmanager
from base64 import b64encode

from ..logging import log_func_call
from .widgets import GuiWidget, GuiWidgetView
from .qt import (
    QWidget, QToolButton, QSize, QIcon, QAction, QSizePolicy, QPainter,
    QBuffer, QByteArray, QSlider, Qt,
)

GuiWidgetParent = QWidget | GuiWidget | GuiWidgetView


def get_widget_parent_qtobj(parent: GuiWidgetParent) -> QWidget:
    """Get the Qt object of the parent widget."""
    if isinstance(parent, QWidget):
        return parent
    elif isinstance(parent, GuiWidget):
        return parent.view.qtobj
    elif isinstance(parent, GuiWidgetView):
        return parent.qtobj
    else:
        raise TypeError(f"Unsupported parent type: {type(parent)}")


@log_func_call
def load_icon(icon_path: str | Path) -> QIcon:
    return QIcon(Path(icon_path).as_posix())


@log_func_call
def create_toolbtn(parent: GuiWidgetParent,
                   callback: Callable = None,
                   sustain: bool = False, sus_repeat_interval_ms: int = 33,
                   sus_delay_ms: int = 0, toggleable: bool = False,
                   toggle_depressed: bool = False, enabled: bool = True):
    button = QToolButton(get_widget_parent_qtobj(parent))
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
        signal.connect(callback)

    return button


@log_func_call
def create_icon_toolbtn(parent: GuiWidgetParent, size: QSize,
                        icon: QIcon | str | Path,
                        callback: Callable = None,
                        sustain: bool = False,
                        sus_repeat_interval_ms: int = 33,
                        sus_delay_ms: int = 0, toggleable: bool = False,
                        toggle_depressed: bool = False, enabled: bool = True):
    if not isinstance(icon, QIcon):
        icon = load_icon(icon)

    button = create_toolbtn(parent, callback, sustain, sus_repeat_interval_ms,
                            sus_delay_ms, toggleable, toggle_depressed,
                            enabled)
    button.setIcon(icon)
    button.setIconSize(size)
    return button


@log_func_call
def create_text_toolbtn(parent: GuiWidgetParent, text: str,
                        callback: Callable = None,
                        sustain: bool = False,
                        sus_repeat_interval_ms: int = 33,
                        sus_delay_ms: int = 0, toggleable: bool = False,
                        toggle_depressed: bool = False, enabled: bool = True):
    button = create_toolbtn(parent, callback, sustain, sus_repeat_interval_ms,
                            sus_delay_ms, toggleable, toggle_depressed,
                            enabled)
    button.setText(text)
    return button


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
        slide.valueChanged.connect(callback)

    return slide


@log_func_call
def show_toolbtn_icon_and_text(btn: QToolButton):
    btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)


@log_func_call
def create_action(parent: GuiWidgetParent, text: str = "",
                  icon: QIcon | str | Path = None,
                  callback: Callable = None, enabled: bool = True,
                  tooltip: str = None):
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
        action.triggered.connect(callback)

    action.setEnabled(enabled)
    return action


@log_func_call
def set_widget_sizepolicy_expanding(w: QWidget):
    w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)


@log_func_call
def create_toolbar_expanding_spacer():
    spacer = QWidget()
    set_widget_sizepolicy_expanding(spacer)
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
