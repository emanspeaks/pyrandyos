from typing import Generic

from ...logging import log_func_call
from ..qt import QLabel, QFrame, Qt, QGraphicsView, QStackedWidget
from .graphview import GraphViewWidget
from . import QtWidgetWrapper, QtWidgetType, GuiWidgetParentType


class GuiViewBaseWidget(Generic[QtWidgetType]):
    qtobj: QtWidgetType


class GuiViewBaseQtWidget(GuiViewBaseWidget[QtWidgetType],
                          QtWidgetWrapper[QtWidgetType],
                          Generic[QtWidgetType]):
    pass


class GuiViewBaseLabel(GuiViewBaseQtWidget[QLabel]):
    @log_func_call
    def __init__(self, gui_parent: GuiWidgetParentType, text: str = ""):
        super().__init__(gui_parent, text)

    @log_func_call
    def create_qtobj(self, text: str = ""):
        qtobj = QLabel(text, self.gui_parent.gui_view.qtobj)
        qtobj.setAlignment(Qt.AlignCenter)
        return qtobj


class GuiBaseGraphView(GuiViewBaseWidget[QGraphicsView], GraphViewWidget):
    pass


class GuiViewBaseFrame(GuiViewBaseQtWidget[QFrame]):
    @log_func_call
    def __init__(self, gui_parent: GuiWidgetParentType):
        super().__init__(gui_parent)

    @log_func_call
    def create_qtobj(self):
        return QFrame(self.gui_parent.gui_view.qtobj)


class GuiViewBaseStack(GuiViewBaseQtWidget[QStackedWidget]):
    @log_func_call
    def __init__(self, gui_parent: GuiWidgetParentType):
        super().__init__(gui_parent)

    @log_func_call
    def create_qtobj(self):
        return QStackedWidget(self.gui_parent.gui_view.qtobj)
