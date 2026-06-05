import pytest
from unittest.mock import MagicMock, patch

from config.settings import AppSettings


@pytest.fixture
def mock_q():
    return MagicMock()


@pytest.fixture
def settings(mock_q):
    return AppSettings(_q=mock_q)


class TestGet:
    def test_returns_value_when_set(self, settings, mock_q):
        mock_q.value.return_value = "en"
        assert settings.get("language") == "en"

    def test_returns_default_when_none(self, settings, mock_q):
        mock_q.value.return_value = None
        assert settings.get("language", "pl") == "pl"

    def test_returns_none_when_no_default(self, settings, mock_q):
        mock_q.value.return_value = None
        assert settings.get("missing") is None

    def test_casts_to_str(self, settings, mock_q):
        mock_q.value.return_value = 42
        assert settings.get("key") == "42"


class TestSet:
    def test_calls_set_value(self, settings, mock_q):
        settings.set("language", "en")
        mock_q.setValue.assert_called_once_with("language", "en")


class TestTypedHelpers:
    def test_language_default_pl(self, settings, mock_q):
        mock_q.value.return_value = None
        assert settings.language() == "pl"

    def test_language_returns_saved(self, settings, mock_q):
        mock_q.value.return_value = "en"
        assert settings.language() == "en"

    def test_theme_default_system(self, settings, mock_q):
        mock_q.value.return_value = None
        assert settings.theme() == "system"

    def test_theme_returns_saved(self, settings, mock_q):
        mock_q.value.return_value = "dark"
        assert settings.theme() == "dark"

    def test_notifications_enabled_default_true(self, settings, mock_q):
        mock_q.value.return_value = None
        assert settings.notifications_enabled() is True

    def test_notifications_enabled_false(self, settings, mock_q):
        mock_q.value.return_value = "false"
        assert settings.notifications_enabled() is False

    def test_notifications_enabled_true(self, settings, mock_q):
        mock_q.value.return_value = "true"
        assert settings.notifications_enabled() is True


class TestSetHelpers:
    def test_set_language(self, settings, mock_q):
        settings.set_language("en")
        mock_q.setValue.assert_called_with("language", "en")

    def test_set_theme(self, settings, mock_q):
        settings.set_theme("dark")
        mock_q.setValue.assert_called_with("theme", "dark")

    def test_set_notifications_enabled_true(self, settings, mock_q):
        settings.set_notifications_enabled(True)
        mock_q.setValue.assert_called_with("notifications", "true")

    def test_set_notifications_enabled_false(self, settings, mock_q):
        settings.set_notifications_enabled(False)
        mock_q.setValue.assert_called_with("notifications", "false")
