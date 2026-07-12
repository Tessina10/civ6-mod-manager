"""Fonctions pures utilisées par l'UI : compression/extraction de mods, formatage
de tailles/dates, parsing de lien Pixeldrain. Aucune dépendance à Qt ni à Tkinter."""
import re
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

ProgressCallback = Optional[Callable[[int, int], None]]


def sanitize_folder_name(name: str) -> str:
    """Nettoie un titre de mod pour en faire un nom de dossier valide dans l'archive."""
    name = re.sub(r"[^\w\-. ]", "_", name).strip()
    name = name.rstrip("_").strip()
    return name or "mod"


def collect_mod_files(mods_data: list[dict]) -> list[tuple[Path, Path]]:
    """Liste (chemin réel, chemin dans l'archive) de tous les fichiers des mods donnés."""
    entries = []
    for mod in mods_data:
        mod_folder = Path(mod["path"])
        top_name = f"{mod['id']}_{sanitize_folder_name(mod['title'])}"
        for file_path in mod_folder.rglob("*"):
            if file_path.is_file():
                arcname = Path(top_name) / file_path.relative_to(mod_folder)
                entries.append((file_path, arcname))
    return entries


def write_mods_zip(path: Path, mods_data: list[dict], on_progress: ProgressCallback = None) -> None:
    """Zippe les dossiers des mods donnés dans l'archive `path`.
    `on_progress(fait, total)` est appelé après chaque fichier écrit, si fourni."""
    entries = collect_mod_files(mods_data)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, (file_path, arcname) in enumerate(entries, start=1):
            zf.write(file_path, arcname)
            if on_progress:
                on_progress(i, len(entries))


def extract_zip_to_folder(zip_path: Path, folder: Path, on_progress: ProgressCallback = None) -> int:
    """Extrait l'archive `zip_path` dans `folder` et retourne le nombre de mods extraits.
    `on_progress(fait, total)` est appelé après chaque fichier extrait, si fourni."""
    folder.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        infos = zf.infolist()
        total = len(infos)
        for i, info in enumerate(infos, start=1):
            zf.extract(info, folder)
            if on_progress:
                on_progress(i, total)
        names = [info.filename for info in infos]
    top_level = {name.split("/")[0] for name in names if name.strip()}
    return len(top_level)


def extract_pixeldrain_id(link: str) -> Optional[str]:
    """Accepte un lien Pixeldrain complet ou un ID brut, retourne l'ID ou None."""
    link = link.strip()
    if not link:
        return None
    match = re.search(r"pixeldrain\.com/(?:api/file|u)/([A-Za-z0-9]+)", link)
    if match:
        return match.group(1)
    if re.fullmatch(r"[A-Za-z0-9]+", link):
        return link
    return None


def format_size(num_bytes: int) -> str:
    """Formate une taille en octets en chaîne lisible (Ko/Mo/Go)."""
    size = float(num_bytes)
    for unit in ("o", "Ko", "Mo", "Go"):
        if size < 1024 or unit == "Go":
            return f"{size:.0f} {unit}" if unit == "o" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} Go"


def format_upload_date(date_upload: str) -> str:
    """Formate une date ISO 8601 renvoyée par l'API Pixeldrain en chaîne lisible."""
    try:
        return datetime.fromisoformat(date_upload).strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return date_upload or "?"
