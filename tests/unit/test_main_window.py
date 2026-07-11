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
    with patch("ui.main_window._FetchWorker") as MockWorker, \
         patch("ui.main_window.QSystemTrayIcon") as MockTray:
        instance = MockWorker.return_value
        instance.isRunning.return_value = False
        MockTray.isSystemTrayAvailable.return_value = False
        w = MainWindow(mock_creds, db=mock_db, provider=mock_provider)
        qtbot.addWidget(w)
        yield w, mock_provider


class TestMainWindowInit:
    def test_window_title(self, window):
        w, _ = window
        assert w.windowTitle() == "YouTube Notifier"

    def test_minimum_size(self, window):
        w, _ = window
        assert w.minimumWidth() == 720
        assert w.minimumHeight() == 580

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
        from PyQt6.QtWidgets import QLabel
        all_labels = w._videos_container.findChildren(QLabel)
        texts = [lbl.text() for lbl in all_labels]
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


def _vid(vid, ch="UC1", cht="Alpha", dur="10:00", days=1):
    return Video(
        video_id=vid, channel_id=ch, title=f"Film {vid}", description="opis",
        url=f"https://youtu.be/{vid}", duration=dur,
        published_at=datetime.now(tz=timezone.utc) - timedelta(days=days),
        channel_title=cht,
    )


def _layout_order(w):
    return [
        wd.video.video_id
        for i in range(w._videos_layout.count())
        if isinstance((wd := w._videos_layout.itemAt(i).widget()), _VideoCard)
    ]


def _shown(w):
    return sorted(
        wd.video.video_id
        for i in range(w._videos_layout.count())
        if isinstance((wd := w._videos_layout.itemAt(i).widget()), _VideoCard)
        and not wd.isHidden()
    )


class TestFiltersAndSort:
    _VIDS = [
        ("a", "UC1", "Alpha", "5:00", 1),
        ("b", "UC2", "Beta", "40:00", 3),
        ("c", "UC1", "Alpha", "1:00:00", 2),
    ]

    def _load(self, w):
        w._on_videos_loaded([_vid(*args) for args in self._VIDS])

    def test_channel_filter_populated(self, window):
        w, _ = window
        self._load(w)
        labels = [w._channel_filter.itemText(i) for i in range(w._channel_filter.count())]
        assert "Alpha" in labels and "Beta" in labels

    def test_sort_longest(self, window):
        w, _ = window
        self._load(w)
        w._sort_combo.setCurrentIndex(w._sort_modes.index("longest"))
        assert _layout_order(w) == ["c", "b", "a"]

    def test_sort_shortest(self, window):
        w, _ = window
        self._load(w)
        w._sort_combo.setCurrentIndex(w._sort_modes.index("shortest"))
        assert _layout_order(w) == ["a", "b", "c"]

    def test_channel_filter_hides_others(self, window):
        w, _ = window
        self._load(w)
        idx = next(i for i in range(w._channel_filter.count())
                   if w._channel_filter.itemData(i) == "UC1")
        w._channel_filter.setCurrentIndex(idx)
        assert _shown(w) == ["a", "c"]

    def test_search_filter(self, window):
        w, _ = window
        self._load(w)
        w._search_input.setText("Film b")
        assert _shown(w) == ["b"]


class TestWatched:
    def test_toggle_persists_and_counts(self, window):
        w, mock = window
        w._on_videos_loaded([_vid("a"), _vid("b")])
        card_a = next(c for c in w._cards if c.video.video_id == "a")
        card_a._toggle_watched()
        # persisted to DB
        w._db.set_watched.assert_called_with("a", True)
        # counter shows unwatched
        assert "1" in w._count_label.text()
        assert card_a.is_watched()

    def test_unwatched_only_hides_watched(self, window):
        w, _ = window
        w._on_videos_loaded([_vid("a"), _vid("b")])
        next(c for c in w._cards if c.video.video_id == "a")._toggle_watched()
        w._unwatched_check.setChecked(True)
        assert _shown(w) == ["b"]

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
        copy_btn = next(
            b for b in card.findChildren(QPushButton)
            if b.objectName() == "card_copy_btn"
        )
        copy_btn.click()
        assert "CopyMe" in QApplication.clipboard().text()


class TestFmtDate:
    def test_formats_polish_month(self):
        dt = datetime(2026, 6, 4, 12, 0, 0, tzinfo=timezone.utc)
        result = _fmt_date(dt)
        assert "4 cze 2026" == result

    def test_january(self):
        dt = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        assert "sty" in _fmt_date(dt)
