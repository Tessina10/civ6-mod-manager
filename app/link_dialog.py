"""Boîte de dialogue affichant le lien Pixeldrain créé, prêt à copier."""
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

import i18n


class LinkDialog(QDialog):
    def __init__(self, parent, link: str):
        super().__init__(parent)
        self.link = link
        self.setWindowTitle(i18n.tr("link_dialog.title"))
        self.setModal(True)

        layout = QVBoxLayout(self)

        message = QLabel(i18n.tr("link_dialog.message"))
        message.setWordWrap(True)
        layout.addWidget(message)

        self.link_edit = QLineEdit(link)
        self.link_edit.setReadOnly(True)
        self.link_edit.setMinimumWidth(420)
        layout.addWidget(self.link_edit)

        button_row = QHBoxLayout()
        button_row.addStretch()
        copy_button = QPushButton(i18n.tr("link_dialog.copy"))
        copy_button.clicked.connect(self._copy)
        button_row.addWidget(copy_button)
        close_button = QPushButton(i18n.tr("common.close"))
        close_button.clicked.connect(self.accept)
        button_row.addWidget(close_button)
        layout.addLayout(button_row)

    def _copy(self):
        QApplication.clipboard().setText(self.link)
