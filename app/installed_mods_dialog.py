"""Fenêtre secondaire listant les mods déjà installés dans le dossier Mods."""
from pathlib import Path

from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)

import i18n
import mod_scanner


class InstalledModsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(i18n.tr("installed.title"))
        self.resize(560, 360)
        self._folder = ""

        layout = QVBoxLayout(self)

        action_row = QHBoxLayout()
        self.scan_button = QPushButton(i18n.tr("send.scan"))
        self.scan_button.clicked.connect(lambda: self.refresh(self._folder))
        action_row.addWidget(self.scan_button)
        action_row.addStretch()
        layout.addLayout(action_row)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([i18n.tr("send.table_title"), i18n.tr("installed.col_version")])
        self.tree.setRootIsDecorated(False)
        self.tree.setSelectionMode(QAbstractItemView.NoSelection)
        layout.addWidget(self.tree)

    def refresh(self, folder_str: str) -> None:
        self._folder = folder_str
        folder = Path(folder_str) if folder_str else None
        self.tree.clear()
        if not folder or not folder.exists():
            return
        for mod in mod_scanner.scan_installed_mods(folder):
            self.tree.addTopLevelItem(QTreeWidgetItem([mod["title"], mod["version"]]))
