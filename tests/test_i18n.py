from linkedin_cli import i18n
from linkedin_cli.i18n import get_language, t


def test_translate_english():
    assert t("en", "config_saved") == "Configuration saved."


def test_translate_portuguese():
    assert t("pt", "config_saved") == "Configuração salva."


def test_translate_with_formatting():
    assert t("en", "queue_added", id="abc", when="2026-08-10 09:00") == (
        "Queued post 'abc' for 2026-08-10 09:00."
    )
    assert t("pt", "queue_added", id="abc", when="2026-08-10 09:00") == (
        "Post 'abc' agendado para 2026-08-10 09:00."
    )


def test_translate_unknown_language_falls_back_to_english():
    assert t("fr", "config_saved") == "Configuration saved."


def test_translate_unknown_key_in_portuguese_falls_back_to_english(monkeypatch):
    monkeypatch.setitem(i18n._MESSAGES["en"], "en_only", "English only")
    assert t("pt", "en_only") == "English only"


def test_translate_unknown_key_returns_key():
    assert t("en", "does_not_exist") == "does_not_exist"


def test_get_language():
    assert get_language("en") == "en"
    assert get_language("pt") == "pt"
    assert get_language("fr") == "en"
    assert get_language(None) == "en"
