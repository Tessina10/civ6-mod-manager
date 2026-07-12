"""Tests de i18n.py : traduction, repli sur clé manquante, changement de langue."""
import pytest

import i18n


def test_tr_returns_correct_string_per_language():
    i18n.set_language("fr")
    assert i18n.tr("tab.send") == "Envoyer"
    i18n.set_language("en")
    assert i18n.tr("tab.send") == "Send"


def test_tr_formats_placeholders():
    i18n.set_language("fr")
    assert i18n.tr("send.status_scan_result", count=3) == "3 mod(s) trouvé(s)."


def test_tr_falls_back_to_key_when_missing_everywhere():
    i18n.set_language("fr")
    assert i18n.tr("this.key.does.not.exist") == "this.key.does.not.exist"


def test_tr_ignores_unknown_placeholder_gracefully():
    i18n.set_language("fr")
    # "tab.send" n'a pas de placeholder : passer un kwarg superflu ne doit pas planter.
    assert i18n.tr("tab.send", unused="x") == "Envoyer"


def test_set_language_rejects_unsupported_language():
    with pytest.raises(ValueError):
        i18n.set_language("de")


def test_all_keys_present_in_both_languages():
    fr_keys = set(i18n.TRANSLATIONS["fr"].keys())
    en_keys = set(i18n.TRANSLATIONS["en"].keys())
    assert fr_keys == en_keys
