"""
QT MODERN

MIT License

Copyright (c) 2017 Gerard Marull-Paretas <gerardmarull@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ....logging import log_func_call
from ...qt import QPalette, QColor
if TYPE_CHECKING:
    from ...gui_app import QtApp


@log_func_call
def light(app: QtApp):
    """
    Apply light theme to the Qt application instance.

    Args:
        app (QApplication): QApplication instance.
    """

    light_palette = QPalette()

    # base
    light_palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
    light_palette.setColor(QPalette.Button, QColor(240, 240, 240))
    light_palette.setColor(QPalette.Light, QColor(180, 180, 180))
    light_palette.setColor(QPalette.Midlight, QColor(200, 200, 200))
    light_palette.setColor(QPalette.Dark, QColor(225, 225, 225))
    light_palette.setColor(QPalette.Text, QColor(0, 0, 0))
    light_palette.setColor(QPalette.BrightText, QColor(0, 0, 0))
    light_palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
    light_palette.setColor(QPalette.Base, QColor(237, 237, 237))
    light_palette.setColor(QPalette.Window, QColor(240, 240, 240))
    light_palette.setColor(QPalette.Shadow, QColor(20, 20, 20))
    light_palette.setColor(QPalette.Highlight, QColor(76, 163, 224))
    light_palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
    light_palette.setColor(QPalette.Link, QColor(0, 162, 232))
    light_palette.setColor(QPalette.AlternateBase, QColor(225, 225, 225))
    light_palette.setColor(QPalette.ToolTipBase, QColor(240, 240, 240))
    light_palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
    light_palette.setColor(QPalette.LinkVisited, QColor(222, 222, 222))

    # disabled
    light_palette.setColor(
        QPalette.Disabled, QPalette.WindowText, QColor(115, 115, 115)
    )
    light_palette.setColor(QPalette.Disabled, QPalette.Text, QColor(115, 115, 115))  # noqa: E501
    light_palette.setColor(
        QPalette.Disabled, QPalette.ButtonText, QColor(115, 115, 115)
    )
    light_palette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(190, 190, 190))  # noqa: E501
    light_palette.setColor(
        QPalette.Disabled, QPalette.HighlightedText, QColor(115, 115, 115)
    )

    app.style().unpolish(app)
    app.setPalette(light_palette)
    app.setStyle("Fusion")
    app.setStyleSheet('')
