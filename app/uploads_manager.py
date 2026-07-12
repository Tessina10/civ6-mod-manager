"""Fenêtre de gestion des envois Pixeldrain (liste, suppression individuelle/en masse)."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)

import formatting
import i18n
import workers
from progress_dialog import ProgressDialog


class UploadsManagerDialog(QDialog):
    def __init__(self, parent, api_key: str):
        super().__init__(parent)
        self.api_key = api_key
        self.setWindowTitle(i18n.tr("uploads.title"))
        self.resize(640, 400)

        self._refresh_worker: workers.RefreshUploadsWorker | None = None
        self._delete_worker: workers.DeleteUploadsWorker | None = None
        self._progress_dialog: ProgressDialog | None = None

        layout = QVBoxLayout(self)

        action_row = QHBoxLayout()
        self.refresh_button = QPushButton(i18n.tr("uploads.refresh"))
        self.refresh_button.clicked.connect(self.refresh)
        action_row.addWidget(self.refresh_button)
        self.delete_selection_button = QPushButton(i18n.tr("uploads.delete_selection"))
        self.delete_selection_button.clicked.connect(lambda: self._delete(selection_only=True))
        action_row.addWidget(self.delete_selection_button)
        self.delete_all_button = QPushButton(i18n.tr("uploads.delete_all"))
        self.delete_all_button.clicked.connect(lambda: self._delete(selection_only=False))
        action_row.addWidget(self.delete_all_button)
        action_row.addStretch()
        layout.addLayout(action_row)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(
            [i18n.tr("uploads.col_name"), i18n.tr("uploads.col_size"), i18n.tr("uploads.col_date")]
        )
        self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree.setRootIsDecorated(False)
        layout.addWidget(self.tree)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        self.refresh()

    def _set_controls_enabled(self, enabled: bool):
        self.refresh_button.setEnabled(enabled)
        self.delete_selection_button.setEnabled(enabled)
        self.delete_all_button.setEnabled(enabled)

    def refresh(self):
        self._set_controls_enabled(False)
        self.status_label.setText(i18n.tr("uploads.loading"))
        self._refresh_worker = workers.RefreshUploadsWorker(self.api_key)
        self._refresh_worker.succeeded.connect(self._on_refresh_succeeded)
        self._refresh_worker.failed.connect(self._on_refresh_failed)
        self._refresh_worker.start()

    def _on_refresh_succeeded(self, files: list[dict]):
        self._set_controls_enabled(True)
        self.tree.clear()
        for f in files:
            item = QTreeWidgetItem(
                [f["name"], formatting.format_size(f["size"]), formatting.format_upload_date(f.get("date_upload", ""))]
            )
            item.setData(0, Qt.UserRole, f["id"])
            self.tree.addTopLevelItem(item)
        self.status_label.setText(i18n.tr("uploads.count", count=len(files)))

    def _on_refresh_failed(self, message: str):
        self._set_controls_enabled(True)
        self.status_label.setText("")
        QMessageBox.critical(self, i18n.tr("common.error"), i18n.tr("uploads.list_error", error=message))

    def _selected_ids(self) -> list[str]:
        return [item.data(0, Qt.UserRole) for item in self.tree.selectedItems()]

    def _all_ids(self) -> list[str]:
        return [self.tree.topLevelItem(i).data(0, Qt.UserRole) for i in range(self.tree.topLevelItemCount())]

    def _delete(self, selection_only: bool):
        if selection_only:
            ids = self._selected_ids()
            if not ids:
                QMessageBox.information(self, i18n.tr("common.info"), i18n.tr("uploads.select_at_least_one"))
                return
            question = i18n.tr("uploads.confirm_delete_selection", count=len(ids))
        else:
            ids = self._all_ids()
            if not ids:
                QMessageBox.information(self, i18n.tr("common.info"), i18n.tr("uploads.nothing_to_delete"))
                return
            question = i18n.tr("uploads.confirm_delete_all", count=len(ids))

        reply = QMessageBox.question(
            self, i18n.tr("uploads.confirm_title"), question, QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        self._set_controls_enabled(False)
        self._progress_dialog = ProgressDialog(
            self, i18n.tr("uploads.deleting_title"), i18n.tr("uploads.deleting_message", count=len(ids))
        )
        self._delete_worker = workers.DeleteUploadsWorker(ids, self.api_key)
        self._delete_worker.progress.connect(self._progress_dialog.set_progress)
        self._delete_worker.succeeded.connect(self._on_delete_succeeded)
        self._progress_dialog.show()
        self._delete_worker.start()

    def _on_delete_succeeded(self, succeeded: int, failed_count: int):
        self._progress_dialog.close()
        self._set_controls_enabled(True)
        if failed_count:
            QMessageBox.warning(
                self,
                i18n.tr("uploads.delete_done_title"),
                i18n.tr("uploads.delete_done_partial", succeeded=succeeded, failed=failed_count),
            )
        else:
            QMessageBox.information(
                self, i18n.tr("uploads.delete_done_title"), i18n.tr("uploads.delete_done_all", succeeded=succeeded)
            )
        self.refresh()
