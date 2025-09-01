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

from typing import TYPE_CHECKING

from ....logging import log_func_call, DEBUGLOW2
from ...callback import qt_callback
from ....utils.hash import TupleHashMixin
from ...qt import QTimer, QRect, QRectF, QWidget, QPainter
if TYPE_CHECKING:
    from .icon import IconLayer


class IconAnimation(TupleHashMixin):
    """
    Base class for icon animations.
    This class provides a common interface for animations that can be applied
    to icons.
    """
    def __init__(self, parent_widget: QWidget):
        self.parent_widget = parent_widget

    def setup(self, icon_painter: 'IconLayer', painter: QPainter,
              rect: QRect | QRectF):
        raise NotImplementedError("Subclasses should implement this method")

    def start(self):
        raise NotImplementedError("Subclasses should implement this method")

    def stop(self):
        raise NotImplementedError("Subclasses should implement this method")

    def as_tuple(self):
        """
        Returns a tuple representation of the animation instance.
        This is used for hashing and equality checks.
        """
        return (self.__class__.__qualname__, self.parent_widget)


class IconSpin(IconAnimation):
    @log_func_call
    def __init__(self, parent_widget: QWidget, interval: int = 10,
                 step: int = 1, autostart: bool = True):
        super().__init__(parent_widget)
        self.interval = interval
        self.step = step
        self.autostart = autostart

        self.info = {}

    def as_tuple(self):
        return super().as_tuple() + (
            self.interval,
            self.step,
            self.autostart,
        )

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
    def setup(self, icon_painter: 'IconLayer', painter: QPainter,
              rect: QRect | QRectF):
        if self.parent_widget not in self.info:
            timer = QTimer(self.parent_widget)
            timer.timeout.connect(qt_callback(self._update))
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


class IconPulse(IconSpin):
    @log_func_call
    def __init__(self, parent_widget: QWidget, autostart: bool = True):
        super().__init__(parent_widget, interval=300, step=45,
                         autostart=autostart)

    def as_tuple(self):
        return super().as_tuple() + (
            self.autostart,
        )
