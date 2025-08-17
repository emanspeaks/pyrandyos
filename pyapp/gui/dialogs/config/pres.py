from ....app import PyApp
from ....logging import log_func_call
from ...widgets import GuiWindowLikeParentType
from .. import GuiDialog
from .view import ConfigTreeDialogView


class ConfigTreeDialog(GuiDialog[ConfigTreeDialogView]):
    @log_func_call
    def __init__(self, gui_parent: GuiWindowLikeParentType):
        super().__init__("Current Configuration", gui_parent)

    @log_func_call
    def get_config(self):
        return PyApp.get_global_config()

    @log_func_call
    def show(self):
        # Set dialog as child of parent window to prevent focus issues
        # parent_window = self.gui_parent.gui_view.qtobj
        dialog = self.gui_view.qtobj
        # dialog.setParent(parent_window, dialog.windowFlags())

        # # Ensure proper window attributes
        # dialog.setAttribute(Qt.WA_ShowWithoutActivating, False)
        # dialog.setAttribute(Qt.WA_DeleteOnClose, False)

        # Show and raise the dialog
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    @log_func_call
    def create_gui_view(self, basetitle: str, *args,
                        **kwargs) -> ConfigTreeDialogView:
        return ConfigTreeDialogView(basetitle, self, *args, **kwargs)
