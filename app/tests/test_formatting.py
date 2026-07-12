"""Tests des fonctions pures de formatting.py (aucune dépendance Qt)."""
import zipfile

import formatting


def test_sanitize_folder_name_replaces_invalid_characters():
    # ':' '/' '*' '!' sont hors de [\w\-. ] -> remplacés par '_', puis les '_'
    # finaux sont retirés par rstrip("_") dans l'implémentation.
    assert formatting.sanitize_folder_name("Mod: Special/Édition*!") == "Mod_ Special_Édition"


def test_sanitize_folder_name_empty_result_falls_back_to_mod():
    assert formatting.sanitize_folder_name("///") == "mod"


def test_write_mods_zip_creates_expected_archive_layout(tmp_path):
    mod_folder = tmp_path / "source" / "111"
    mod_folder.mkdir(parents=True)
    (mod_folder / "Mod.modinfo").write_text("<Mod/>", encoding="utf-8")
    (mod_folder / "Text").mkdir()
    (mod_folder / "Text" / "fr_FR.xml").write_text("<Text/>", encoding="utf-8")

    mods_data = [{"id": "111", "title": "Mon Mod", "path": str(mod_folder)}]
    zip_path = tmp_path / "out.zip"

    formatting.write_mods_zip(zip_path, mods_data)

    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())

    assert "111_Mon Mod/Mod.modinfo" in names
    assert "111_Mon Mod/Text/fr_FR.xml" in names


def test_write_mods_zip_reports_progress(tmp_path):
    mod_folder = tmp_path / "source" / "111"
    mod_folder.mkdir(parents=True)
    (mod_folder / "a.modinfo").write_text("<Mod/>", encoding="utf-8")
    (mod_folder / "b.txt").write_text("data", encoding="utf-8")

    calls = []
    formatting.write_mods_zip(
        tmp_path / "out.zip",
        [{"id": "111", "title": "Mon Mod", "path": str(mod_folder)}],
        on_progress=lambda done, total: calls.append((done, total)),
    )

    assert calls == [(1, 2), (2, 2)]


def test_extract_zip_to_folder_round_trip(tmp_path):
    # Simule l'archive que produit write_mods_zip() : un dossier par mod au
    # premier niveau (<id>_<titre>/...).
    zip_path = tmp_path / "mods_recus.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("111_Mon Mod/Mod.modinfo", "<Mod/>")
        zf.writestr("111_Mon Mod/Text/fr_FR.xml", "<Text/>")
        zf.writestr("222_Autre Mod/Autre.modinfo", "<Mod/>")

    dest = tmp_path / "Mods"
    count = formatting.extract_zip_to_folder(zip_path, dest)

    assert count == 2
    assert (dest / "111_Mon Mod" / "Mod.modinfo").exists()
    assert (dest / "111_Mon Mod" / "Text" / "fr_FR.xml").exists()
    assert (dest / "222_Autre Mod" / "Autre.modinfo").exists()


def test_extract_pixeldrain_id_from_full_link():
    assert formatting.extract_pixeldrain_id("https://pixeldrain.com/u/abc123XY") == "abc123XY"


def test_extract_pixeldrain_id_from_api_link():
    assert formatting.extract_pixeldrain_id("https://pixeldrain.com/api/file/abc123XY") == "abc123XY"


def test_extract_pixeldrain_id_from_raw_id():
    assert formatting.extract_pixeldrain_id("abc123XY") == "abc123XY"


def test_extract_pixeldrain_id_strips_whitespace():
    assert formatting.extract_pixeldrain_id("  abc123XY  ") == "abc123XY"


def test_extract_pixeldrain_id_rejects_invalid_input():
    assert formatting.extract_pixeldrain_id("") is None
    assert formatting.extract_pixeldrain_id("not a valid link !!") is None


def test_format_size_bytes():
    assert formatting.format_size(0) == "0 o"
    assert formatting.format_size(512) == "512 o"


def test_format_size_kilo_mega_giga():
    assert formatting.format_size(1536) == "1.5 Ko"
    assert formatting.format_size(5 * 1024 * 1024) == "5.0 Mo"
    assert formatting.format_size(2 * 1024 * 1024 * 1024) == "2.0 Go"


def test_format_upload_date_parses_iso_with_z_suffix():
    assert formatting.format_upload_date("2026-07-12T00:54:44.095Z") == "2026-07-12 00:54"


def test_format_upload_date_falls_back_to_raw_on_bad_input():
    assert formatting.format_upload_date("not-a-date") == "not-a-date"
    assert formatting.format_upload_date("") == "?"
