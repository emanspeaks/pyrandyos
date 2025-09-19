# Nomenclature, Model-View-Presenter, and Qt concepts/hierarchy
# --------------------------------------------------------------
# * Qt terminology:
#   * Qt widget: any components of a GUI a user can see or interact with
#     * Qt window: a top-level widget with no parent other than the application
#       * Qt dialog: a transient window that is intended to be dismissed
#       * Qt *main* window: a window intended to persist and not be dismissed,
#         also dedicated structure for menus, toolbars, status bars, and docks
#   * Qt object: any object in the Qt framework, including non-widgets.
#     * note that PySide classes cannot add new attributes or they will crash
#       the Python interpreter as soon as you try to add a new attribute not
#       part of the base class.  PySide classes should only be subclassed to
#       override methods, not to add new attributes.  If you need to store
#       additional data outside of stack variables, use a wrapper class around
#       the Qt object
#
# * Model: data interface and application state.  These are concepts in the
#   general application library that are GUI-agnostic.
#
# * View: code to construct a visible GUI component (widget OR window).
#   * Qt widget/window wrappers are generally "views".
#   * generally only stores Qt objects and data about the structure/layout of
#     the GUI.  Other data should be stored in the Model.
#   * owned by a Presenter and considered internal to it.
# * Presenter: contains callbacks for user interaction with the View.
#   * owns and creates a View.
#   * this is the object that should be passed around and interacted with
#     by the models or other parts of the application.
#   * It need not have "presenter" in the name, and GUI components lacking any
#     qualifier should be assumed to be a Presenter.
#
# * PyRandyOS-specific nomenclature:
#   * PyRandyOS implements a hierarchical MVP structure.
#
#   * GUI Component: an abstract concept that encapsulates a View and
#     its Presenter.
#
#   * A "window", with no other qualifiers in the name, is assumed to correlate
#     to a Qt main window, i.e. not a dialog or orphaned widget.  This differs
#     from the Qt nomenclature, where a "window" is any top-level widget.
#     This is merely a convention to shorten names and avoid confusion.
#   * Top View: a window, dialog, or top-level widget.
#   * Top Pres: the Presenter of a Top View.
#
#   * GUI App: analogous to a Presenter, this is the object that wraps a
#     Qt QApplication and is the main entry point for the GUI.
#     * Is a GUI Container for Top Views spawned by the main entry point.

from typing import TypeVar, TYPE_CHECKING, Generic

from ..logging import log_func_call
from .qt import QWidget, QApplication

if TYPE_CHECKING:
    from .gui_app import QtApp, GuiApp
    from .widgets import GuiWidgetParentType


QtObject = TypeVar('QtObject', bound=QWidget | QApplication)
QtWidgetType = TypeVar('QtWidgetType', bound=QWidget)
GuiViewType = TypeVar('GuiViewType', bound='GuiView')
GuiPresType = TypeVar('GuiPresType', bound='GuiPresenter')


class GuiQtWrapper(Generic[QtObject]):
    @log_func_call
    def __init__(self, qtobj: QtObject):
        self._qtobj = qtobj

    @property
    def qtobj(self) -> QtObject:
        return self._qtobj


class CreateQtObjMixin(GuiQtWrapper[QtWidgetType], Generic[QtWidgetType]):
    @log_func_call
    def __init__(self, *qtobj_args, **qtobj_kwargs):
        super().__init__(self.create_qtobj(*qtobj_args, **qtobj_kwargs))

    @log_func_call
    def create_qtobj(self, *args, **kwargs) -> QtWidgetType:
        raise NotImplementedError('Abstract method not implemented')


class GuiComponent:
    @property
    def gui_app(self) -> 'GuiApp':
        from .gui_app import get_gui_app
        return get_gui_app()

    @property
    def qt_app(self) -> 'QtApp':
        app = self.gui_app
        if app:
            return app.qtobj

    @property
    def gui_view(self) -> 'GuiView':
        return getattr(self, '_gui_view', None)

    @property
    def gui_pres(self) -> 'GuiPresenter':
        return getattr(self, '_gui_pres', None)


class GuiPresenter(GuiComponent, Generic[GuiViewType]):
    @log_func_call
    def __init__(self, gui_parent: 'GuiWidgetParentType | None' = None,
                 *view_args, **view_kwargs):
        GuiComponent.__init__(self)
        self._gui_parent = gui_parent
        self._gui_view = self.create_gui_view(*view_args, **view_kwargs)

    @log_func_call
    def create_gui_view(self, *args, **kwargs) -> GuiViewType:
        raise NotImplementedError('Abstract method not implemented')

    @property
    def gui_parent(self):
        return self._gui_parent

    @property
    def gui_pres(self):
        return self

    @property
    def gui_view(self) -> GuiViewType:
        return self._gui_view


class GuiView(GuiComponent, Generic[GuiPresType]):
    @log_func_call
    def __init__(self, presenter: GuiPresType = None):
        GuiComponent.__init__(self)
        self._gui_pres = presenter

    @property
    def gui_pres(self) -> GuiPresType:
        return self._gui_pres

    @property
    def gui_view(self):
        return self


class GuiQtView(GuiView[GuiPresType], CreateQtObjMixin[QtWidgetType],
                Generic[GuiPresType, QtWidgetType]):
    @log_func_call
    def __init__(self, presenter: GuiPresType = None, *qtobj_args,
                 **qtobj_kwargs):
        GuiView.__init__(self, presenter)
        CreateQtObjMixin.__init__(self, *qtobj_args, **qtobj_kwargs)
