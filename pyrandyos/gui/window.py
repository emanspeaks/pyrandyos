from __future__ import annotations
from typing import TypeVar, Generic

from ..logging import log_func_call
from .widgets import GuiWindowLikeView, GuiWindowLike, GuiWindowLikeParentType
from .widgets.viewbase import GuiViewBaseWidget
from .qt import QMainWindow

GuiWindowPresType = TypeVar('GuiWindowPresType', bound='GuiWindow')
GuiWindowViewType = TypeVar('GuiWindowViewType', bound='GuiWindowView')
GuiViewBaseWidgetType = TypeVar('GuiViewBaseWidgetType',
                                bound=GuiViewBaseWidget)


class GuiWindow(GuiWindowLike[GuiWindowViewType], Generic[GuiWindowViewType]):
    @log_func_call
    def __init__(self, basetitle: str,
                 gui_parent: GuiWindowLikeParentType | None = None,
                 *view_args, **view_kwargs):
        super().__init__(basetitle, gui_parent, *view_args, **view_kwargs)


class GuiWindowView(GuiWindowLikeView[GuiWindowPresType, QMainWindow],
                    Generic[GuiWindowPresType, GuiViewBaseWidgetType]):
    @log_func_call
    def __init__(self, basetitle: str, presenter: GuiWindowPresType | None,
                 *qtobj_args, **qtobj_kwargs):
        GuiWindowLikeView.__init__(self, basetitle, presenter, *qtobj_args,
                                   **qtobj_kwargs)
        qtobj = self.qtobj
        basewidget = self.create_basewidget()
        self._basewidget = basewidget
        qtobj.setCentralWidget(basewidget.qtobj)

    @log_func_call
    def create_qtobj(self, *args, **kwargs):
        return QMainWindow(*args, **kwargs)

    @log_func_call
    def create_basewidget(self) -> GuiViewBaseWidgetType:
        raise NotImplementedError('Abstract method not implemented')

    @property
    def basewidget(self) -> GuiViewBaseWidgetType:
        return self._basewidget

    # @property
    # def qtbasewidget(self):
    #     return self.basewidget.qtobj
