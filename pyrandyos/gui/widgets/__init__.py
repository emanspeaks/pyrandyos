from __future__ import annotations
from typing import TypeVar, Generic, TypeAlias

from ..qt import QCursor, QTimer
from .. import GuiQtView, GuiPresenter, QtWidgetType, GuiView
from ...logging import log_func_call

GuiWidgetPresType = TypeVar('GuiWidgetType', bound='GuiWidget')
GuiWidgetViewType = TypeVar('GuiWidgetViewType', bound='GuiWidgetView')
GuiWindowLikePresType = TypeVar('GuiWindowLikeType', bound='GuiWindowLike')
GuiWindowLikeViewType = TypeVar('GuiWindowLikeViewType',
                                bound='GuiWindowLikeView')

GuiWidgetParentType: TypeAlias = 'GuiWidget | GuiWidgetView | QtWidgetWrapper'
GuiWindowLikeParentType: TypeAlias = 'GuiWindowLike | GuiWindowLikeView'


class GuiWidget(GuiPresenter[GuiWidgetViewType], Generic[GuiWidgetViewType]):
    @log_func_call
    def __init__(self, gui_parent: GuiWidgetParentType | None = None,
                 *view_args, **view_kwargs):
        GuiPresenter.__init__(self, gui_parent, *view_args, **view_kwargs)

    @log_func_call
    def create_gui_view(self, *args, **kwargs) -> 'GuiWidgetViewType':
        return GuiWidgetView(self, *args, **kwargs)


class GuiSimpleWidgetPresenter(GuiWidget[None]):
    @log_func_call
    def create_gui_view(self, *args, **kwargs):
        pass


class GuiSimpleWidget(GuiSimpleWidgetPresenter, GuiView[None]):
    @log_func_call
    def __init__(self, gui_parent: GuiWidgetParentType | None = None,
                 *view_args, **view_kwargs):
        GuiSimpleWidgetPresenter.__init__(self, gui_parent, *view_args,
                                          **view_kwargs)
        GuiView.__init__(self, self)

    @log_func_call
    def create_gui_view(self, *args, **kwargs) -> None:
        raise NotImplementedError('Abstract method not implemented')


class GuiWidgetView(GuiQtView[GuiWidgetPresType, QtWidgetType],
                    Generic[GuiWidgetPresType, QtWidgetType]):
    @log_func_call
    def __init__(self, presenter: GuiWidgetPresType | None, *qtobj_args,
                 **qtobj_kwargs):
        GuiQtView.__init__(self, presenter, *qtobj_args, **qtobj_kwargs)


class QtWidgetWrapper(GuiSimpleWidgetPresenter,
                      GuiWidgetView[None, QtWidgetType],
                      Generic[QtWidgetType]):
    @log_func_call
    def __init__(self, gui_parent: GuiWidgetParentType | None = None,
                 *qtobj_args, **qtobj_kwargs):
        GuiSimpleWidgetPresenter.__init__(self, gui_parent)
        GuiWidgetView.__init__(self, self, *qtobj_args, **qtobj_kwargs)


class GuiWindowLike(GuiWidget[GuiWindowLikeViewType],
                    Generic[GuiWindowLikeViewType]):
    @log_func_call
    def __init__(self, basetitle: str,
                 gui_parent: GuiWidgetParentType | None = None,
                 *view_args, **view_kwargs):
        super().__init__(gui_parent, basetitle, *view_args, **view_kwargs)
        # self.gui_view: GuiWindowLikeView

    @log_func_call
    def show(self):
        self.gui_view.show()

    @log_func_call
    def create_gui_view(self, basetitle: str, *args,
                        **kwargs) -> GuiWindowLikeViewType:
        raise NotImplementedError('Abstract method not implemented')

    @log_func_call
    def post_show_init(self):
        "Any initialization that should be executed after the window is shown"
        pass


class GuiWindowLikeView(GuiWidgetView[GuiWindowLikePresType, QtWidgetType],
                        Generic[GuiWindowLikePresType, QtWidgetType]):
    @log_func_call
    def __init__(self, basetitle: str, presenter: GuiWindowLikePresType = None,
                 *qtobj_args, **qtobj_kwargs):
        super().__init__(presenter, *qtobj_args, **qtobj_kwargs)
        self.basetitle = basetitle
        self.set_title()
        QTimer.singleShot(0, presenter.post_show_init)

    @log_func_call
    def show(self):
        self.qtobj.show()

    @property
    def hwnd(self):
        return self.qtobj.winId()

    @log_func_call
    def bring_to_front(self):
        qtobj = self.qtobj
        qtobj.raise_()
        qtobj.activateWindow()
        qtobj.showNormal()

    @log_func_call
    def center_window_in_current_screen(self):
        qtobj = self.qtobj
        qtapp = self.qt_app
        centerPoint = qtapp.screenAt(QCursor.pos()).geometry().center()
        geo = qtobj.geometry()
        geo.moveCenter(centerPoint)
        qtobj.setGeometry(geo)

    @log_func_call
    def set_title(self, subtitle: str = None):
        title = self.basetitle
        if subtitle:
            title += ' - ' + subtitle

        self.qtobj.setWindowTitle(title)

    @log_func_call
    def get_dpi(self):
        return self.qtobj.devicePixelRatio()
