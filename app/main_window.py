"""Fenêtre principale : onglets Envoyer/Recevoir (avec le sélecteur de langue
dans leur coin, car général et indépendant de l'onglet actif), et juste en
dessous un bouton "Options avancées" (menu contextuel qui change selon
l'onglet actif) — volontairement pas dans la barre de menu Qt tout en haut,
qui reste au-dessus de tout et ne peut pas être repositionnée sous les onglets."""
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QMainWindow, QMenu, QPushButton, QTabWidget, QVBoxLayout, QWidget

import i18n
from receive_tab import ReceiveTab
from send_tab import SendTab
from uploads_manager import UploadsManagerDialog

SEND_TAB_INDEX = 0
RECEIVE_TAB_INDEX = 1

_LANGUAGE_LABELS = {"fr": "Français", "en": "English"}

# Garde une référence vers la fenêtre courante pour que Python ne la libère pas
# pendant un changement de langue à chaud (voir _change_language).
_current_window = None


class MainWindow(QMainWindow):
    def __init__(
        self,
        initial_tab: int = SEND_TAB_INDEX,
        initial_send_folder: str = "",
        initial_receive_folder: str = "",
    ):
        super().__init__()
        self.setWindowTitle(i18n.tr("app.title"))
        self.resize(760, 520)

        self.send_tab = SendTab()
        self.receive_tab = ReceiveTab()
        if initial_send_folder:
            self.send_tab.folder_edit.setText(initial_send_folder)
        if initial_receive_folder:
            self.receive_tab.folder_edit.setText(initial_receive_folder)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.send_tab, i18n.tr("tab.send"))
        self.tabs.addTab(self.receive_tab, i18n.tr("tab.receive"))
        self._build_language_selector()

        self.advanced_button = QPushButton(i18n.tr("menu.advanced"))
        self.advanced_menu = QMenu(self)
        self.advanced_button.setMenu(self.advanced_menu)
        self._update_advanced_menu(self.tabs.currentIndex())  # peuple le menu pour l'onglet courant (0)

        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.addWidget(self.tabs)
        button_row = QHBoxLayout()
        button_row.addWidget(self.advanced_button)
        button_row.addStretch()
        central_layout.addLayout(button_row)
        self.setCentralWidget(central)

        # Connecté puis appliqué seulement une fois self.advanced_menu prêt : sinon,
        # passer initial_tab=1 déclencherait _update_advanced_menu avant que le menu
        # n'existe (AttributeError), ce qui plantait le changement de langue à chaud
        # quand on se trouvait sur l'onglet Recevoir.
        self.tabs.currentChanged.connect(self._update_advanced_menu)
        self.tabs.setCurrentIndex(initial_tab)

    def _build_language_selector(self):
        self.language_combo = QComboBox()
        for code, label in _LANGUAGE_LABELS.items():
            self.language_combo.addItem(label, userData=code)
        current_index = list(_LANGUAGE_LABELS.keys()).index(i18n.current_language())
        self.language_combo.setCurrentIndex(current_index)
        # Connecté après avoir positionné l'index initial, pour ne pas déclencher
        # un changement de langue "fantôme" pendant la construction de la fenêtre.
        self.language_combo.currentIndexChanged.connect(
            lambda index: self._change_language(self.language_combo.itemData(index))
        )
        self.tabs.setCornerWidget(self.language_combo)

    def _update_advanced_menu(self, index: int):
        self.advanced_menu.clear()
        if index == SEND_TAB_INDEX:
            pixeldrain_menu = self.advanced_menu.addMenu(i18n.tr("menu.pixeldrain"))
            pixeldrain_menu.addAction(i18n.tr("menu.pixeldrain.api_key"), self.send_tab.open_settings_dialog)
            pixeldrain_menu.addAction(i18n.tr("menu.pixeldrain.manage_uploads"), self._open_uploads_manager)

            self.advanced_menu.addSeparator()
            manual_menu = self.advanced_menu.addMenu(i18n.tr("menu.manual_sharing"))
            manual_menu.addAction(i18n.tr("menu.manual_sharing.export_json"), self.send_tab.export_json)
            manual_menu.addAction(i18n.tr("menu.manual_sharing.copy_links"), self.send_tab.copy_workshop_links)
            manual_menu.addAction(i18n.tr("menu.manual_sharing.create_archive"), self.send_tab.create_archive)
        else:
            self.advanced_menu.addAction(i18n.tr("installed.menu_item"), self.receive_tab.show_installed_mods)
            self.advanced_menu.addAction(i18n.tr("receive.import_menu_item"), self.receive_tab.import_zip)

    def _open_uploads_manager(self):
        api_key = self.send_tab.ensure_api_key()
        if not api_key:
            return
        dialog = UploadsManagerDialog(self, api_key)
        dialog.exec()

    def _change_language(self, language: str):
        if language == i18n.current_language():
            return
        i18n.set_language(language)

        global _current_window
        new_window = MainWindow(
            initial_tab=self.tabs.currentIndex(),
            initial_send_folder=self.send_tab.folder_edit.text(),
            initial_receive_folder=self.receive_tab.folder_edit.text(),
        )
        # Affiche la nouvelle fenêtre AVANT de fermer l'ancienne : il ne doit
        # jamais y avoir zéro fenêtre visible, sinon Qt quitte l'application
        # (quitOnLastWindowClosed).
        new_window.show()
        _current_window = new_window
        self.close()
