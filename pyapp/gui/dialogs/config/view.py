# from __future__ import annotations
from typing import TYPE_CHECKING

from ....logging import log_func_call, DEBUGLOW2
from ....app import PyApp
from ...qt import (
    QVBoxLayout, QTreeView, QDialogButtonBox, QAbstractItemView,
    QStandardItemModel, QStandardItem,
)
from .. import GuiDialogView

if TYPE_CHECKING:
    from .pres import ConfigTreeDialog


class ConfigTreeDialogView(GuiDialogView['ConfigTreeDialog']):
    def __init__(self, basetitle: str, presenter: 'ConfigTreeDialog' = None,
                 *qtobj_args, **qtobj_kwargs):
        GuiDialogView.__init__(self, basetitle, presenter, *qtobj_args,
                               **qtobj_kwargs)
        qtobj = self.qtobj
        qtobj.resize(*PyApp.get_default_win_size())
        self.layout = QVBoxLayout(qtobj)
        self.create_tree()

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

        buttons = QDialogButtonBox(QDialogButtonBox.Ok, qtobj)
        buttons.accepted.connect(qtobj.accept)
        layout.addWidget(buttons)
        self.buttons = buttons

        self.populate_tree(itemmodel, pres.get_config())
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
