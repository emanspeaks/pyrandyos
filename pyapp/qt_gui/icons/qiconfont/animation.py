# The MIT License
#
# Copyright (c) 2015 The Spyder development team
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


from PySide2.QtCore import QTimer, QRect, QRectF
from PySide2.QtWidgets import QWidget
from PySide2.QtGui import QPainter

from ....logging import log_func_call, DEBUGLOW2


class Spin:
    @log_func_call
    def __init__(self, parent_widget: QWidget, interval: int = 10,
                 step: int = 1, autostart: bool = True):
        self.parent_widget = parent_widget
        self.interval = interval
        self.step = step
        self.autostart = autostart

        self.info = {}

    @log_func_call(DEBUGLOW2, trace_only=True)
    def _update(self):
        if self.parent_widget in self.info:
            timer, angle, step = self.info[self.parent_widget]

            if angle >= 360:
                angle = 0

            angle += step
            self.info[self.parent_widget] = timer, angle, step
            self.parent_widget.update()

    @log_func_call
    def setup(self, icon_painter: QPainter, painter: QPainter,
              rect: QRect | QRectF):
        if self.parent_widget not in self.info:
            timer = QTimer(self.parent_widget)
            timer.timeout.connect(self._update)
            self.info[self.parent_widget] = [timer, 0, self.step]
            if self.autostart:
                timer.start(self.interval)
        else:
            timer, angle, self.step = self.info[self.parent_widget]
            x_center = rect.width() * 0.5
            y_center = rect.height() * 0.5
            painter.translate(x_center, y_center)
            painter.rotate(angle)
            painter.translate(-x_center, -y_center)

    @log_func_call
    def start(self):
        if self.parent_widget in self.info:
            timer: QTimer = self.info[self.parent_widget][0]
            timer.start(self.interval)

    @log_func_call
    def stop(self):
        if self.parent_widget in self.info:
            timer: QTimer = self.info[self.parent_widget][0]
            timer.stop()


class Pulse(Spin):
    @log_func_call
    def __init__(self, parent_widget: QWidget, autostart: bool = True):
        super().__init__(parent_widget, interval=300, step=45,
                         autostart=autostart)
