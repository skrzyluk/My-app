import pytest
from unittest.mock import patch, MagicMock

from PyQt6.QtWidgets import QDialogButtonBox, QMessageBox

from database.db import Database
from ui.settings_dialog import SettingsDialog


@pytest.fixture
def db():
    instance = Database(db_path=":memory:")
    yield instance
    instance.close()


@pytest.fixture
def dialog(qtbot, db):
    with patch("ui.settings_dialog.AppSettings"):
        dlg = SettingsDialog(db)
        qtbot.addWidget(dlg)
        yield dlg, db


class TestSettingsLoad:
    def test_default_language_polish(self, dialog):
        dlg, _ = dialog
        assert dlg._lang_combo.currentIndex() == 0

    def test_default_theme_system(self, dialog):
        dlg, _ = dialog
        assert dlg._theme_combo.currentIndex() == 0

    def test_default_notifications_enabled(self, dialog):
        dlg, _ = dialog
        assert dlg._notif_check.isChecked()

    def test_loads_saved_language_english(self, qtbot, db):
        db.set_setting("language", "en")
        dlg = SettingsDialog(db)
        qtbot.addWidget(dlg)
        assert dlg._lang_combo.currentIndex() == 1

    def test_loads_saved_theme_dark(self, qtbot, db):
        db.set_setting("theme", "dark")
        dlg = SettingsDialog(db)
        qtbot.addWidget(dlg)
        assert dlg._theme_combo.currentIndex() == 2

    def test_loads_notifications_off(self, qtbot, db):
        db.set_setting("notifications", "false")
        dlg = SettingsDialog(db)
        qtbot.addWidget(dlg)
        assert not dlg._notif_check.isChecked()


class TestSettingsSave:
    def test_save_language_english(self, dialog):
        dlg, db = dialog
        dlg._lang_combo.setCurrentIndex(1)
        dlg._on_save()
        assert db.get_setting("language") == "en"

    def test_save_language_polish(self, dialog):
        dlg, db = dialog
        dlg._lang_combo.setCurrentIndex(0)
        dlg._on_save()
        assert db.get_setting("language") == "pl"

    def test_save_theme_light(self, dialog):
        dlg, db = dialog
        dlg._theme_combo.setCurrentIndex(1)
        dlg._on_save()
        assert db.get_setting("theme") == "light"

    def test_save_theme_dark(self, dialog):
        dlg, db = dialog
        dlg._theme_combo.setCurrentIndex(2)
        dlg._on_save()
        assert db.get_setting("theme") == "dark"

    def test_save_notifications_off(self, dialog):
        dlg, db = dialog
        dlg._notif_check.setChecked(False)
        dlg._on_save()
        assert db.get_setting("notifications") == "false"

    def test_save_accepts_dialog(self, dialog):
        dlg, _ = dialog
        dlg._on_save()
        assert dlg.result() == SettingsDialog.DialogCode.Accepted


class TestLogout:
    def test_logout_flag_false_initially(self, dialog):
        dlg, _ = dialog
        assert dlg.logout_requested is False

    def test_logout_sets_flag_on_yes(self, dialog):
        dlg, _ = dialog
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
            dlg._on_logout()
        assert dlg.logout_requested is True

    def test_logout_no_flag_on_cancel(self, dialog):
        dlg, _ = dialog
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.No):
            dlg._on_logout()
        assert dlg.logout_requested is False

    def test_cancel_button_rejects_dialog(self, dialog):
        dlg, _ = dialog
        dlg._lang_combo.setCurrentIndex(1)
        dlg.reject()
        assert dlg.result() == SettingsDialog.DialogCode.Rejected
