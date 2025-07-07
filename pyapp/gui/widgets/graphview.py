from PySide2.QtWidgets import QGraphicsView, QGraphicsScene

from ...logging import log_func_call
from ..abc import QtWidgetWrapper


class GraphViewWidget(QtWidgetWrapper):
    @log_func_call
    def __init__(self, parent: QtWidgetWrapper, scene: QGraphicsScene = None):
        super().__init__(parent)
        qtwin = parent.qtroot

        scene = scene or QGraphicsScene(qtwin)
        self.scene = scene

        view = QGraphicsView(scene, qtwin)
        self.view = view
        self.qtroot: QGraphicsView = view
