from pathlib import Path

from ....app import PyRandyOSApp
from ....logging import log_func_call
from ....utils.json import save_json, jsonify
from ...widgets import GuiWindowLikeParentType
from ...qt import QFileDialog
from .. import GuiDialog
from .view import ConfigTreeDialogView


class ConfigTreeDialog(GuiDialog[ConfigTreeDialogView]):
    @log_func_call
    def __init__(self, gui_parent: GuiWindowLikeParentType):
        super().__init__("Current Configuration", gui_parent)

    @log_func_call
    def get_config(self):
        return PyRandyOSApp.get_global_config()

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

    @log_func_call
    def click_save_config(self):
        qtwin = self.gui_view.qtobj
        workdir: Path = PyRandyOSApp['tmp_dir']
        if not workdir.exists():
            workdir = Path.cwd()

        new_fn, selected_filter = QFileDialog.getSaveFileName(
            qtwin, "Save Local Config", str(workdir),
            "Config Files (*.jsonc, *.json)",
        )
        if new_fn:
            save_json(Path(new_fn), jsonify(PyRandyOSApp.get_global_config()))

    @log_func_call
    def click_save_local_config(self):
        PyRandyOSApp.save_local_config()
