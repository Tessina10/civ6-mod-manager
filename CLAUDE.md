# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**Civ6 Mod Bridge** (anciennement "Civ 6 Mod Manager", à l'origine deux
outils Tkinter séparés) — une application PySide6 unique, bilingue FR/EN,
pour partager des mods Civilization VI entre un ami en version **Steam** et
un ami en version **Epic Games** (ou toute autre). Flux principal : upload
automatique vers [Pixeldrain](https://pixeldrain.com) et transmission d'un
simple lien ; en secours, transfert manuel via fichier JSON / presse-papiers
/ archive `.zip` que les utilisateurs s'échangent eux-mêmes.

Historique : le projet visait initialement deux utilisateurs précis
(l'auteur et un ami). Il a été renommé et fusionné en une seule application
pour être facilement partageable à n'importe qui rencontrant le même
problème Steam/Epic (fusion des deux anciens outils, réécriture Tkinter →
PySide6, bilingue). Licence MIT (voir `LICENSE`).

## Commandes

Tout le code vit dans `app/` (pas un package installable — voir Architecture) :

```
pip install -r requirements.txt -r requirements-dev.txt   # PySide6 + outils de dev
cd app && python main.py                                  # lancer l'application
```

Build de l'exécutable Windows (PyInstaller) :

```
cd app && pyinstaller Civ6ModBridge.spec
```

Le binaire est produit dans `app/dist/`. PySide6 est bien supporté
nativement par PyInstaller (hooks fournis par PySide6 lui-même) — pas de
`hiddenimports` nécessaires. L'exécutable est nettement plus volumineux
qu'avec Tkinter (~48 Mo, bibliothèque Qt complète embarquée) : normal, pas
une régression. Au lancement, un build PyInstaller onefile démarre
généralement **deux process** `Civ6ModBridge.exe` (le bootloader qui
extrait, puis le vrai process applicatif) — comportement normal de
PyInstaller onefile, pas un bug ni un double-lancement.

### Dev : dépendances, lint, tests

`requirements.txt` (racine) : dépendance runtime unique, PySide6.
`requirements-dev.txt` (racine) : ruff, pytest, pre-commit, pyinstaller.

Lint (config dans le `pyproject.toml` racine, règles par défaut ruff, pas de
`ruff format` pour ne pas reformater tout le style existant) :

```
ruff check .
```

Un hook pre-commit (`.pre-commit-config.yaml`, installé via `pre-commit
install`) bloque un commit si `ruff check` échoue.

Tests (pytest), dans `app/tests/`, à lancer **depuis `app/`** :

```
cd app && pytest
```

Les tests couvrent uniquement la logique pure, sans Qt ni réseau réel :
`mod_scanner.py` (parsing `.modinfo`, scan Workshop/Mods), `formatting.py`
(zip/dézip, formatage taille/date, parsing lien Pixeldrain), `i18n.py`
(traductions, repli sur clé manquante). Pas de mock du réseau Pixeldrain
(pas de clé API en CI) : le flux d'upload/téléchargement/suppression n'est
validé qu'à la main, avec un vrai compte.

## Architecture

```
app/
├── main.py                 point d'entrée (QApplication + MainWindow)
├── main_window.py           QMainWindow : onglets Envoyer/Recevoir + bouton "Options avancées"
├── send_tab.py               onglet Envoyer (scan Workshop, envoi par lien, partage manuel)
├── receive_tab.py            onglet Recevoir (installation par lien, import zip local)
├── installed_mods_dialog.py  fenêtre secondaire "Mods installés"
├── uploads_manager.py        fenêtre "Gérer mes envois Pixeldrain" (liste/suppression)
├── settings_dialog.py        boîte de dialogue clé API Pixeldrain
├── link_dialog.py             boîte de dialogue affichant le lien créé
├── progress_dialog.py         pop-up de progression réutilisable
├── workers.py                 QThread par opération longue (voir plus bas)
├── mod_scanner.py             scan_workshop_mods() + scan_installed_mods()
├── steam_locator.py           détection du dossier Workshop Steam
├── pixeldrain_client.py       upload_file() / list_files() / delete_file()
├── config.py                  clé API + langue, stockage local
├── formatting.py              fonctions pures : zip/dézip, formatage, parsing lien
├── i18n.py                    dictionnaire de traductions FR/EN + détection langue
├── tests/                     tests de logique pure uniquement
└── Civ6ModBridge.spec         spec PyInstaller
```

### UI : onglets + menu contextuel, pas d'écran de démarrage

`main_window.py` utilise un `QTabWidget` (onglets "Envoyer"/"Recevoir")
plutôt qu'un écran de choix de rôle au démarrage — plus flexible, l'un ou
l'autre onglet reste accessible à tout moment.

Deux éléments de navigation vivent volontairement à deux endroits
différents, suite à des retours utilisateur successifs :
- **Sélecteur de langue** (`QComboBox`) : dans le **coin de la barre
  d'onglets** (`QTabWidget.setCornerWidget()`), car général et indépendant
  de l'onglet actif.
- **Bouton "Options avancées"** (`QPushButton` + `QMenu`, PAS dans la
  barre de menu Qt classique) : positionné **sous les onglets**, car son
  contenu est contextuel et change selon l'onglet actif
  (`MainWindow._update_advanced_menu()`, appelée sur
  `QTabWidget.currentChanged`). La barre de menu Qt (`self.menuBar()`) est
  volontairement inutilisée : elle est toujours au-dessus de tout dans une
  `QMainWindow`, ce qui ne permettait pas de la positionner sous les
  onglets comme demandé.

⚠️ Piège rencontré : dans `MainWindow.__init__`, `self.advanced_menu` doit
être créé (`_update_advanced_menu` appelé une première fois) **avant** de
connecter `tabs.currentChanged` puis d'appeler `tabs.setCurrentIndex(...)`
avec un index non nul — sinon `setCurrentIndex` déclenche
`_update_advanced_menu` avant que `self.advanced_menu` existe
(`AttributeError`). C'est arrivé lors de l'implémentation du changement de
langue à chaud en partant de l'onglet "Recevoir".

### Changement de langue à chaud (sans redémarrer l'app)

`i18n.py` est un dictionnaire de traductions maison (pas de toolchain Qt
Linguist, volontairement simple pour 2 langues). Changer de langue
**reconstruit `MainWindow`** (`MainWindow._change_language()`) plutôt que de
retraduire dynamiquement chaque widget existant : plus simple et sans
risque d'oublier un widget, au prix de perdre l'état de saisie en cours
(mods scannés, lien collé) — l'onglet actif et les dossiers sélectionnés
sont explicitement reportés sur la nouvelle fenêtre. La nouvelle fenêtre est
affichée **avant** de fermer l'ancienne (`quitOnLastWindowClosed` sinon
l'appli se fermerait au moment où il n'y a temporairement plus aucune
fenêtre visible) ; une référence module-level (`main_window._current_window`)
évite que Python ne libère la nouvelle fenêtre par manque de référence.

### `workers.py` : QThread + signaux, pas de `threading.Thread` + polling

Une sous-classe `QThread` par opération longue (`CreateArchiveWorker`,
`SendLinkWorker`, `ImportZipWorker`, `DownloadInstallWorker`,
`RefreshUploadsWorker`, `DeleteUploadsWorker`), avec des signaux
`progress(int, int)` / `succeeded(...)` / `failed(str)` émis depuis `run()`.
Les signaux Qt traversent déjà le thread en toute sécurité vers le thread UI
(pattern plus simple que le `threading.Thread` + `self.after(0, ...)` de
l'ancienne version Tkinter). Les workers doivent être gardés en référence
sur `self` (ex. `self._send_worker = ...`) tant qu'ils tournent, sinon
risque de libération prématurée par Python.

`SendLinkWorker` a deux phases : compression (barre déterminée, `progress`)
puis upload (`phase_changed.emit("uploading")`, bascule en barre indéterminée
— l'API Pixeldrain ne permet pas de mesurer la progression réelle d'un
upload sans réécrire toute la couche réseau déjà testée avec un vrai
compte). `DownloadInstallWorker` a le même principe : téléchargement (barre
déterminée si `Content-Length` connu, sinon indéterminée) puis extraction.

`ProgressDialog` (`progress_dialog.py`) : volontairement **pas** de blocage
de la fermeture manuelle (bouton X, Échap). Une première version bloquait
tout pour empêcher d'interrompre une opération en cours ; en pratique, deux
instances de l'exe lancées en même temps (comportement normal de
PyInstaller onefile, voir plus haut) ont fait qu'une pop-up ne recevait
jamais son signal de fermeture, bloquant toute l'application sans
échappatoire. Fermer la pop-up n'interrompt pas l'opération en fond ; le
résultat s'affiche quand même via une boîte de dialogue séparée à la fin.

### Modules de logique pure, réutilisés depuis l'ancienne version Tkinter

- `pixeldrain_client.py` — repris à l'identique de l'ancien
  `steam_lister/pixeldrain_client.py`, déjà testé avec un vrai compte. Deux
  bugs déjà corrigés à ne pas réintroduire : (1) `urllib` ne suit pas les
  redirections 307/308 sur `PUT` (seulement GET/HEAD) alors que Pixeldrain
  redirige l'upload vers un autre serveur — suivi manuel dans
  `upload_file()` ; (2) l'endpoint de listing est `/api/user/files` (avec le
  préfixe `/api/`), pas `/user/files` qui renvoie la page HTML de login.
- `mod_scanner.py` — fusionne les deux anciens `mod_scanner.py` distincts
  (un pour le Workshop, un pour le dossier Mods) en un seul fichier avec un
  `_parse_modinfo()` partagé (dupliqué à l'identique auparavant) :
  - `scan_workshop_mods()` : chaque sous-dossier **numérique** du dossier
    Workshop = un ID Workshop (nom du dossier fait foi).
  - `scan_installed_mods()` : le `.modinfo` peut être à la racine du
    sous-dossier du mod **ou dans un sous-sous-dossier**.
- `formatting.py` — regroupe les fonctions pures qui vivaient mélangées
  dans les anciens `gui.py` Tkinter (`sanitize_folder_name`,
  `write_mods_zip`, `extract_zip_to_folder`, `extract_pixeldrain_id`,
  `format_size`, `format_upload_date`) : logique inchangée, juste séparée
  de la couche UI pour rester testable sans Qt.
- `config.py` — stocke la clé API et la langue dans
  `%APPDATA%/Civ6ModBridge/config.json` (fallback `Path.home()` hors
  Windows). Migre automatiquement une clé API trouvée à l'ancien
  emplacement (`%APPDATA%/Civ6ModManager/steam_lister_config.json`, utilisé
  par l'ancienne version Tkinter) si le nouveau fichier n'existe pas encore.
- `steam_locator.py` — inchangé depuis l'ancienne version.

### Flux de partage

1. **Lien Pixeldrain** *(flux recommandé, complet et automatique)* :
   `SendLinkWorker` zippe les mods scannés (`formatting.write_mods_zip`),
   upload (`pixeldrain_client.upload_file`), affiche le lien ;
   `DownloadInstallWorker` télécharge ce lien et extrait
   (`formatting.extract_zip_to_folder`) directement dans le dossier Mods.
2. **Archive .zip locale** (fonctionnel dans les deux sens, sans réseau) :
   `SendTab.create_archive()` zippe chaque mod scanné sous
   `<id>_<titre_nettoyé>/...` vers un fichier choisi ;
   `ReceiveTab.import_zip()` extrait une archive choisie sur le disque.
3. **Liste JSON** : `SendTab.export_json()` exporte `{id, title}` de chaque
   mod scanné, à titre d'inventaire/usage manuel — pas d'import automatique
   correspondant côté Recevoir (le message d'export ne le prétend pas).
4. **Liens presse-papiers** : `SendTab.copy_workshop_links()` copie des URLs
   `steamcommunity.com/sharedfiles/filedetails/?id=<id>` — usage manuel.
