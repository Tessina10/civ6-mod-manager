"""Permet aux tests d'importer les modules locaux (mod_scanner, formatting, i18n...)
sans faire de app/ un package installé : on ajoute le dossier parent au sys.path,
comme le fait PyInstaller en exécutant main.py depuis ce même dossier."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
