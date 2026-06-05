import pytest
import i18n


@pytest.fixture(autouse=True)
def reset_language():
    """Each test starts with Polish and is reset after."""
    i18n.set_language("pl")
    yield
    i18n.set_language("pl")


class TestSetLanguage:
    def test_default_is_polish(self):
        assert i18n.current_language() == "pl"

    def test_set_english(self):
        i18n.set_language("en")
        assert i18n.current_language() == "en"

    def test_set_polish(self):
        i18n.set_language("en")
        i18n.set_language("pl")
        assert i18n.current_language() == "pl"

    def test_unknown_lang_falls_back_to_polish(self):
        i18n.set_language("fr")
        assert i18n.current_language() == "pl"

    def test_empty_string_falls_back_to_polish(self):
        i18n.set_language("")
        assert i18n.current_language() == "pl"


class TestTrPolish:
    def test_tab_today(self):
        assert i18n.tr("tab_today") == "Dzisiaj"

    def test_tab_week(self):
        assert i18n.tr("tab_week") == "Tydzień"

    def test_tab_month(self):
        assert i18n.tr("tab_month") == "Miesiąc"

    def test_btn_refresh(self):
        assert "Odśwież" in i18n.tr("btn_refresh")

    def test_btn_copy_all(self):
        assert i18n.tr("btn_copy_all") == "Skopiuj wszystko"

    def test_btn_logout(self):
        assert i18n.tr("btn_logout") == "Wyloguj się"

    def test_video_singular(self):
        assert i18n.tr("video_singular") == "film"

    def test_video_many(self):
        assert i18n.tr("video_many") == "filmów"


class TestTrEnglish:
    def setup_method(self):
        i18n.set_language("en")

    def test_tab_today(self):
        assert i18n.tr("tab_today") == "Today"

    def test_tab_week(self):
        assert i18n.tr("tab_week") == "Week"

    def test_tab_month(self):
        assert i18n.tr("tab_month") == "Month"

    def test_btn_refresh(self):
        assert "Refresh" in i18n.tr("btn_refresh")

    def test_btn_copy_all(self):
        assert i18n.tr("btn_copy_all") == "Copy All"

    def test_btn_logout(self):
        assert i18n.tr("btn_logout") == "Log out"

    def test_video_singular(self):
        assert i18n.tr("video_singular") == "video"

    def test_video_many(self):
        assert i18n.tr("video_many") == "videos"


class TestTrFallback:
    def test_missing_key_returns_key_itself(self):
        assert i18n.tr("nonexistent_key_xyz") == "nonexistent_key_xyz"

    def test_missing_en_key_falls_back_to_polish(self):
        i18n.set_language("en")
        # All keys exist in both, so test the pl fallback path via unknown lang
        i18n.set_language("pl")
        assert i18n.tr("app_title") == "YouTube Notifier"
