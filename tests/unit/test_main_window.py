import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

from PyQt6.QtWidgets import QApplication

from models.video import Video
from ui.main_window import MainWindow, _VideoCard, _fmt_date


def _make_video(video_id="v1", title="Test Title", hours_ago=1) -> Video:
    return Video(
        video_id=video_id,
        channel_id="UC1",
        title=title,
        description="Short desc",
        url=f"https://www.youtube.com/watch?v={video_id}",
        duration="10:30",
        published_at=datetime.now(tz=timezone.utc) - timedelta(hours=hours_ago),
    )


@pytest.fixture
def mock_provider():
    p = MagicMock()
    p.get_videos.return_value = []
    p.force_refresh.return_value = []
    return p


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def window(qtbot, mock_provider, mock_db):
    mock_creds = MagicMock()
    with patch("ui.main_window._FetchWorker") as MockWorker:
        instance = MockWorker.return_value
        instance.isRunning.return_value = False
        w = MainWindow(mock_creds, db=mock_db, provider=mock_provider)
        qtbot.addWidget(w)
        yield w, mock_provider


class TestMainWindowInit:
    def test_window_title(self, window):
        w, _ = window
        assert w.windowTitle() == "YouTube Notifier"

    def test_minimum_size(self, window):
        w, _ = window
        assert w.minimumWidth() == 700
        assert w.minimumHeight() == 550

    def test_default_tab_is_today(self, window):
        w, _ = window
        assert w._current_period == "today"

    def test_today_tab_checked(self, window):
        w, _ = window
        assert w._tab_buttons["today"].isChecked()
        assert not w._tab_buttons["week"].isChecked()
        assert not w._tab_buttons["month"].isChecked()


class TestTabSwitching:
    def test_switch_to_week(self, window, qtbot):
        w, _ = window
        qtbot.mouseClick(w._tab_buttons["week"], __import__("PyQt6.QtCore", fromlist=["Qt"]).Qt.MouseButton.LeftButton)
        assert w._current_period == "week"

    def test_active_tab_checked(self, window, qtbot):
        w, _ = window
        w._on_tab("month")
        assert w._tab_buttons["month"].isChecked()
        assert not w._tab_buttons["today"].isChecked()
        assert not w._tab_buttons["week"].isChecked()

    def test_switch_to_same_tab_is_noop(self, window):
        w, mock_prov = window
        initial_calls = mock_prov.get_videos.call_count
        w._on_tab("today")
        assert mock_prov.get_videos.call_count == initial_calls


class TestVideoRendering:
    def test_empty_list_shows_placeholder(self, window):
        w, _ = window
        w._on_videos_loaded([])
        labels = [
            w._videos_layout.itemAt(i).widget()
            for i in range(w._videos_layout.count())
            if w._videos_layout.itemAt(i).widget()
        ]
        texts = [lbl.text() for lbl in labels if hasattr(lbl, "text")]
        assert any("Brak" in t for t in texts)

    def test_videos_render_cards(self, window):
        w, _ = window
        videos = [_make_video(f"v{i}", f"Title {i}") for i in range(3)]
        w._on_videos_loaded(videos)
        cards = [
            w._videos_layout.itemAt(i).widget()
            for i in range(w._videos_layout.count())
            if isinstance(w._videos_layout.itemAt(i).widget(), _VideoCard)
        ]
        assert len(cards) == 3

    def test_status_label_shows_count(self, window):
        w, _ = window
        videos = [_make_video(f"v{i}") for i in range(5)]
        w._on_videos_loaded(videos)
        assert "5" in w._status_label.text()

    def test_status_label_no_videos(self, window):
        w, _ = window
        w._on_videos_loaded([])
        assert "Brak" in w._status_label.text()

    def test_single_video_noun(self, window):
        w, _ = window
        w._on_videos_loaded([_make_video()])
        assert "film" in w._status_label.text()

    def test_rerender_clears_previous(self, window):
        w, _ = window
        w._on_videos_loaded([_make_video("v1")])
        w._on_videos_loaded([_make_video("v2"), _make_video("v3")])
        cards = [
            w._videos_layout.itemAt(i).widget()
            for i in range(w._videos_layout.count())
            if isinstance(w._videos_layout.itemAt(i).widget(), _VideoCard)
        ]
        assert len(cards) == 2


class TestCopyAll:
    def test_copy_all_sets_clipboard(self, window, qapp):
        w, _ = window
        videos = [_make_video("v1", "My Video")]
        w._on_videos_loaded(videos)
        w._on_copy_all()
        text = QApplication.clipboard().text()
        assert "My Video" in text

    def test_copy_all_does_nothing_when_empty(self, window, qapp):
        w, _ = window
        QApplication.clipboard().setText("before")
        w._current_videos = []
        w._on_copy_all()
        assert QApplication.clipboard().text() == "before"


class TestButtons:
    def test_refresh_btn_enabled_after_load(self, window):
        w, _ = window
        w._on_videos_loaded([])
        assert w._refresh_btn.isEnabled()

    def test_copy_all_btn_disabled_when_no_videos(self, window):
        w, _ = window
        w._on_videos_loaded([])
        assert not w._copy_all_btn.isEnabled()

    def test_copy_all_btn_enabled_when_videos(self, window):
        w, _ = window
        w._on_videos_loaded([_make_video()])
        assert w._copy_all_btn.isEnabled()


class TestVideoCard:
    def test_card_shows_title(self, qtbot):
        v = _make_video("v1", "Hello World")
        card = _VideoCard(v)
        qtbot.addWidget(card)
        all_text = " ".join(
            w.text() for w in card.findChildren(__import__("PyQt6.QtWidgets", fromlist=["QLabel"]).QLabel)
        )
        assert "Hello World" in all_text

    def test_card_shows_duration(self, qtbot):
        v = _make_video()
        card = _VideoCard(v)
        qtbot.addWidget(card)
        from PyQt6.QtWidgets import QLabel
        texts = [w.text() for w in card.findChildren(QLabel)]
        assert any("10:30" in t for t in texts)

    def test_card_copy_button_sets_clipboard(self, qtbot, qapp):
        v = _make_video("v1", "CopyMe")
        card = _VideoCard(v)
        qtbot.addWidget(card)
        from PyQt6.QtWidgets import QPushButton
        copy_btn = next(b for b in card.findChildren(QPushButton) if b.text() == "Kopiuj")
        copy_btn.click()
        assert "CopyMe" in QApplication.clipboard().text()


class TestFmtDate:
    def test_formats_polish_month(self):
        dt = datetime(2026, 6, 4, 12, 0, 0, tzinfo=timezone.utc)
        result = _fmt_date(dt)
        assert "4 cze 2026" == result

    def test_january(self):
        dt = datetime(2026, 1, 1, tzinfo=timezone.utc)
        assert "sty" in _fmt_date(dt)
