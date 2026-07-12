"""Pop-up de progression réutilisable pour les opérations longues (compression,
envoi, téléchargement, extraction, suppression en masse)."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QLabel, QProgressBar, QVBoxLayout


class ProgressDialog(QDialog):
    def __init__(self, parent, title: str, message: str):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setFixedWidth(380)

        layout = QVBoxLayout(self)
        self.message_label = QLabel(message)
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

    def set_message(self, message: str) -> None:
        self.message_label.setText(message)

    def set_progress(self, done: int, total: int) -> None:
        if total:
            if self.progress_bar.maximum() == 0:
                self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(int(done / total * 100))

    def set_indeterminate(self) -> None:
        self.progress_bar.setRange(0, 0)  # idiome Qt pour une barre "occupée" animée

    # Volontairement pas de blocage de fermeture manuelle (bouton X, Échap) : une
    # première version bloquait tout, ce qui a bloqué l'appli entière si la pop-up
    # ne se fermait pas automatiquement comme prévu (aucune échappatoire possible).
    # Fermer cette pop-up n'interrompt pas l'opération en cours (elle continue en
    # fond) ; le résultat (succès ou erreur) s'affichera quand même à la fin via
    # une boîte de dialogue séparée.
