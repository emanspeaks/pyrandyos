from __future__ import annotations
from typing import TypeVar, Generic

from ...logging import log_func_call
from ..widgets import GuiWindowLikeView, GuiWindowLike, GuiWindowLikeParentType
from ..qt import QDialog


GuiDialogPresType = TypeVar('GuiDialogPresType', bound='GuiDialog')
GuiDialogViewType = TypeVar('GuiDialogViewType', bound='GuiDialogView')


class GuiDialog(GuiWindowLike[GuiDialogViewType], Generic[GuiDialogViewType]):
    @log_func_call
    def __init__(self, basetitle: str,
                 gui_parent: GuiWindowLikeParentType | None = None,
                 *view_args, **view_kwargs):
        super().__init__(basetitle, gui_parent, *view_args, **view_kwargs)


class GuiDialogView(GuiWindowLikeView[GuiDialogPresType, QDialog],
                    Generic[GuiDialogPresType]):
    @log_func_call
    def create_qtobj(self, *args, **kwargs):
        return QDialog(*args, **kwargs)
