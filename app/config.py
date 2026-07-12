"""Stockage local de la configuration de l'application (clé API Pixeldrain, langue)."""
import json
import os
import platform
from pathlib import Path
from typing import Optional

APP_DIR_NAME = "Civ6ModBridge"
CONFIG_FILE_NAME = "config.json"

# Ancien emplacement utilisé par steam_lister avant la fusion en une seule
# appli : si aucune config n'existe encore au nouvel emplacement, on
# rapatrie la clé API depuis là pour éviter à l'utilisateur de la ressaisir.
LEGACY_APP_DIR_NAME = "Civ6ModManager"
LEGACY_CONFIG_FILE_NAME = "steam_lister_config.json"


def _base_dir() -> Path:
    if platform.system() == "Windows":
        return Path(os.environ.get("APPDATA", Path.home()))
    return Path.home()


def _config_path() -> Path:
    return _base_dir() / APP_DIR_NAME / CONFIG_FILE_NAME


def _legacy_config_path() -> Path:
    return _base_dir() / LEGACY_APP_DIR_NAME / LEGACY_CONFIG_FILE_NAME


def _read_json(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _write_config(data: dict) -> None:
    config_dir = _config_path().parent
    config_dir.mkdir(parents=True, exist_ok=True)
    _config_path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_api_key() -> Optional[str]:
    data = _read_json(_config_path())
    if data is not None:
        return data.get("pixeldrain_api_key") or None

    legacy_data = _read_json(_legacy_config_path())
    if legacy_data:
        key = legacy_data.get("pixeldrain_api_key")
        if key:
            save_api_key(key)  # migre vers le nouvel emplacement pour la prochaine fois
            return key
    return None


def save_api_key(api_key: str) -> None:
    data = _read_json(_config_path()) or {}
    data["pixeldrain_api_key"] = api_key
    _write_config(data)


def load_language() -> Optional[str]:
    data = _read_json(_config_path())
    return data.get("language") if data else None


def save_language(language: str) -> None:
    data = _read_json(_config_path()) or {}
    data["language"] = language
    _write_config(data)
