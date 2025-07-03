from typing import TYPE_CHECKING

from PySide2.QtWidgets import (
    QVBoxLayout, QTreeView, QDialogButtonBox, QAbstractItemView
)
from PySide2.QtGui import QStandardItemModel, QStandardItem

from ....logging import log_func_call, DEBUGLOW2
from ....app import PyApp
from ...abc import QtDialogWrapper
if TYPE_CHECKING:
    from .ctrl import ConfigTreeDialog


class ConfigTreeView(QtDialogWrapper):
    @log_func_call
    def __init__(self, controller: 'ConfigTreeDialog'):
        super().__init__("Current Configuration", controller)
        qtwin = self.qtroot
        qtwin.resize(*PyApp.get_default_win_size())
        self.layout = QVBoxLayout(qtwin)
        self.create_tree()

    @log_func_call
    def create_tree(self):
        qtwin = self.qtroot
        layout = self.layout
        ctrl: ConfigTreeDialog = self.controller

        itemmodel = QStandardItemModel()
        itemmodel.setHorizontalHeaderLabels(["Key", "Value"])
        self.itemmodel = itemmodel

        tree = QTreeView(qtwin)
        tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tree.setModel(itemmodel)
        layout.addWidget(tree)
        self.tree = tree

        header = tree.header()
        header.setStretchLastSection(True)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok, qtwin)
        buttons.accepted.connect(qtwin.accept)
        layout.addWidget(buttons)
        self.buttons = buttons

        self.populate_tree(itemmodel, ctrl.get_config())
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
