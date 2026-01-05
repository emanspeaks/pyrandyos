import sys
# from __future__ import annotations
from typing import TYPE_CHECKING
from pathlib import Path

from ....logging import log_func_call, DEBUGLOW2
from ....app import PyRandyOSApp
from ...qt import (
    QVBoxLayout, QTreeView, QDialogButtonBox, QAbstractItemView,
    QStandardItemModel, QStandardItem, QSize, QHBoxLayout,
)
from ...utils import create_icon_button
from .. import GuiDialogView
from .icons import SaveLocalConfigIcon, SaveConfigIcon

if TYPE_CHECKING:
    from .pres import ConfigTreeDialog


class ConfigTreeDialogView(GuiDialogView['ConfigTreeDialog']):
    @log_func_call
    def __init__(self, basetitle: str, presenter: 'ConfigTreeDialog' = None,
                 *qtobj_args, **qtobj_kwargs):
        GuiDialogView.__init__(self, basetitle, presenter, *qtobj_args,
                               **qtobj_kwargs)
        qtobj = self.qtobj
        qtobj.resize(*PyRandyOSApp.get_default_win_size())
        self.layout = QVBoxLayout(qtobj)
        self.create_tree()

    @log_func_call
    def create_tree(self):
        qtobj = self.qtobj
        layout = self.layout
        pres: 'ConfigTreeDialog' = self.gui_pres

        itemmodel = QStandardItemModel()
        itemmodel.setHorizontalHeaderLabels(["Key", "Value"])
        self.itemmodel = itemmodel

        tree = QTreeView(qtobj)
        tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tree.setModel(itemmodel)
        layout.addWidget(tree)
        self.tree = tree

        header = tree.header()
        header.setStretchLastSection(True)

        hbox = QHBoxLayout()
        layout.addLayout(hbox)

        savelocalbtn = create_icon_button(qtobj, QSize(32, 32),
                                          SaveLocalConfigIcon.icon(),
                                          pres.click_save_local_config,
                                          "Save Local Config")
        hbox.addWidget(savelocalbtn)
        self.savelocalbtn = savelocalbtn

        savecfgbtn = create_icon_button(qtobj, QSize(32, 32),
                                        SaveConfigIcon.icon(),
                                        pres.click_save_config,
                                        "Export Full Config")
        hbox.addWidget(savecfgbtn)
        self.savecfgbtn = savecfgbtn

        dlgbuttons = QDialogButtonBox(QDialogButtonBox.Ok, qtobj)
        dlgbuttons.accepted.connect(qtobj.accept)
        hbox.addStretch()
        hbox.addWidget(dlgbuttons)
        self.dlgbuttons = dlgbuttons

        self.populate_tree(itemmodel, pres.get_config())

        not_in_cfg_item = QStandardItem("(Not in Config dict)")
        itemmodel.appendRow([not_in_cfg_item, QStandardItem("")])
        syspath = {'Python sys.path': [Path(p) for p in sys.path]}
        self.populate_tree(not_in_cfg_item, syspath)

        tree.expandAll()
        tree.resizeColumnToContents(0)

    @log_func_call(DEBUGLOW2)
    def populate_tree(self, parent_item: QStandardItemModel | QStandardItem,
                      value: dict | list):
        pairs = (sorted(value.items(), key=lambda x: x[0])
                 if isinstance(value, dict)
                 else enumerate(value) if isinstance(value, list)
                 else ())
        for k, v in pairs:
            key_item = QStandardItem(f"[{k}]" if isinstance(value, list)
                                     else str(k))
            key_item.setEditable(False)

            value_item = QStandardItem("" if isinstance(v, (dict, list))
                                       else str(v))
            value_item.setEditable(False)

            parent_item.appendRow([key_item, value_item])
            self.populate_tree(key_item, v)
