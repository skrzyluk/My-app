import pytest
from PyQt6.QtWidgets import QApplication

from resources.styles import LIGHT_QSS, DARK_QSS
from config.theme import apply_theme


class TestQssStrings:
    def test_light_qss_non_empty(self):
        assert len(LIGHT_QSS.strip()) > 100

    def test_dark_qss_non_empty(self):
        assert len(DARK_QSS.strip()) > 100

    def test_light_qss_contains_video_card(self):
        assert "#video_card" in LIGHT_QSS

    def test_dark_qss_contains_video_card(self):
        assert "#video_card" in DARK_QSS

    def test_light_qss_contains_refresh_btn(self):
        assert "#refresh_btn" in LIGHT_QSS

    def test_dark_qss_contains_refresh_btn(self):
        assert "#refresh_btn" in DARK_QSS

    def test_light_qss_contains_tab_selector(self):
        assert 'QPushButton[tab="true"]' in LIGHT_QSS

    def test_dark_qss_contains_tab_selector(self):
        assert 'QPushButton[tab="true"]' in DARK_QSS

    def test_light_has_scrollbar_style(self):
        assert "QScrollBar" in LIGHT_QSS

    def test_dark_has_scrollbar_style(self):
        assert "QScrollBar" in DARK_QSS


class TestApplyThemeStylesheet:
    def test_dark_theme_sets_stylesheet(self, qapp):
        apply_theme(qapp, "dark")
        assert len(qapp.styleSheet()) > 0

    def test_light_theme_sets_stylesheet(self, qapp):
        apply_theme(qapp, "light")
        assert len(qapp.styleSheet()) > 0

    def test_system_theme_clears_stylesheet(self, qapp):
        apply_theme(qapp, "dark")
        apply_theme(qapp, "system")
        assert qapp.styleSheet() == ""

    def test_dark_stylesheet_matches_dark_qss(self, qapp):
        apply_theme(qapp, "dark")
        assert "#video_card" in qapp.styleSheet()

    def test_light_stylesheet_matches_light_qss(self, qapp):
        apply_theme(qapp, "light")
        assert "#video_card" in qapp.styleSheet()


class TestVideoCardObjectNames:
    def test_card_has_video_card_object_name(self, qtbot):
        from datetime import datetime, timezone, timedelta
        from models.video import Video
        from ui.main_window import _VideoCard

        v = Video(
            video_id="v1", channel_id="c1", title="Test",
            description="desc", url="https://yt.com/v?v=v1",
            duration="5:00",
            published_at=datetime.now(tz=timezone.utc) - timedelta(hours=1),
        )
        card = _VideoCard(v)
        qtbot.addWidget(card)
        assert card.objectName() == "video_card"

    def test_card_copy_btn_has_object_name(self, qtbot):
        from datetime import datetime, timezone, timedelta
        from models.video import Video
        from ui.main_window import _VideoCard
        from PyQt6.QtWidgets import QPushButton

        v = Video(
            video_id="v1", channel_id="c1", title="Test",
            description="", url="https://yt.com/v?v=v1",
            duration="5:00",
            published_at=datetime.now(tz=timezone.utc) - timedelta(hours=1),
        )
        card = _VideoCard(v)
        qtbot.addWidget(card)
        copy_btn = next(
            b for b in card.findChildren(QPushButton) if b.text() == "Kopiuj"
        )
        assert copy_btn.objectName() == "card_copy_btn"


class TestMainWindowObjectNames:
    @pytest.fixture
    def window(self, qtbot):
        from unittest.mock import MagicMock, patch
        mock_creds = MagicMock()
        mock_db = MagicMock()
        mock_prov = MagicMock()
        mock_prov.get_videos.return_value = []
        with patch("ui.main_window._FetchWorker") as MockW, \
             patch("ui.main_window.QSystemTrayIcon") as MockT:
            inst = MockW.return_value
            inst.isRunning.return_value = False
            MockT.isSystemTrayAvailable.return_value = False
            from ui.main_window import MainWindow
            w = MainWindow(mock_creds, db=mock_db, provider=mock_prov)
            qtbot.addWidget(w)
            yield w

    def test_refresh_btn_object_name(self, window):
        assert window._refresh_btn.objectName() == "refresh_btn"

    def test_copy_all_btn_object_name(self, window):
        assert window._copy_all_btn.objectName() == "copy_all_btn"

    def test_status_label_object_name(self, window):
        assert window._status_label.objectName() == "status_label"

    def test_tab_buttons_have_tab_property(self, window):
        for btn in window._tab_buttons.values():
            assert btn.property("tab") == "true"
