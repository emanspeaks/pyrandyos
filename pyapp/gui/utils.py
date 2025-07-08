from pathlib import Path
from collections.abc import Callable
from contextlib import contextmanager

from PySide2.QtGui import QIcon, QPainter
from PySide2.QtCore import QSize
from PySide2.QtWidgets import (
    QToolButton, QSlider, QWidget, QAction, QSizePolicy,
)

from .abc import QtWidgetWrapper
from ..logging import log_func_call


@log_func_call
def load_icon(icon_path: str | Path) -> QIcon:
    return QIcon(Path(icon_path).as_posix())


@log_func_call
def create_toolbtn(parent: QtWidgetWrapper | QWidget,
                   callback: Callable = None,
                   sustain: bool = False, sus_repeat_interval_ms: int = 33,
                   sus_delay_ms: int = 0, toggleable: bool = False,
                   toggle_depressed: bool = False, enabled: bool = True):
    button = QToolButton(parent if isinstance(parent, QWidget)
                         else parent.qtroot)
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
def create_icon_toolbtn(parent: QtWidgetWrapper | QWidget, size: QSize,
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
def create_text_toolbtn(parent: QtWidgetWrapper | QWidget, text: str,
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
def create_slider(parent: QtWidgetWrapper | QWidget, min_value: int,
                  max_value: int, value: int, callback: Callable = None):
    slide = QSlider(parent if isinstance(parent, QWidget) else parent.qtroot)
    slide.setMinimum(min_value)
    slide.setMaximum(max_value)
    slide.setValue(value)
    # slide.setOrientation(orientation)
    # slide.setEnabled(enabled)

    if callback:
        slide.valueChanged.connect(callback)

    return slide


@log_func_call
def create_action(parent: QtWidgetWrapper | QWidget, text: str = "",
                  icon: QIcon | str | Path = None,
                  callback: Callable = None, enabled: bool = True):
    action = QAction(parent if isinstance(parent, QWidget)
                     else parent.qtroot)
    if text:
        action.setText(text)

    if icon:
        if not isinstance(icon, QIcon):
            icon = load_icon(icon)

        action.setIcon(icon)

    if callback:
        action.triggered.connect(callback)

    action.setEnabled(enabled)
    return action


@log_func_call
def create_toolbar_expanding_spacer():
    spacer = QWidget()
    spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    return spacer


@contextmanager
def painter_context(painter: QPainter):
    painter.save()
    try:
        yield painter
    finally:
        painter.restore()
