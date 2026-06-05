import pytest
from datetime import datetime, timezone

from PyQt6.QtWidgets import QLabel, QPushButton, QApplication

from database.db import Database
from ui.history_dialog import HistoryDialog, _fmt_date


@pytest.fixture
def db():
    instance = Database(db_path=":memory:")
    yield instance
    instance.close()


class TestHistoryDialogEmpty:
    def test_shows_empty_placeholder(self, qtbot, db):
        dlg = HistoryDialog(db)
        qtbot.addWidget(dlg)
        labels = dlg.findChildren(QLabel)
        texts = [lbl.text() for lbl in labels]
        assert any("Brak" in t for t in texts)

    def test_has_close_button(self, qtbot, db):
        dlg = HistoryDialog(db)
        qtbot.addWidget(dlg)
        buttons = [b.text() for b in dlg.findChildren(QPushButton)]
        assert "Zamknij" in buttons


class TestHistoryDialogWithSummaries:
    def test_renders_summary_cards(self, qtbot, db):
        db.save_summary("week", 3, "Summary A")
        db.save_summary("today", 1, "Summary B")
        dlg = HistoryDialog(db)
        qtbot.addWidget(dlg)
        labels = dlg.findChildren(QLabel)
        texts = " ".join(lbl.text() for lbl in labels)
        assert "Tydzień" in texts
        assert "Dzisiaj" in texts

    def test_shows_video_count(self, qtbot, db):
        db.save_summary("week", 7, "Some text")
        dlg = HistoryDialog(db)
        qtbot.addWidget(dlg)
        labels = dlg.findChildren(QLabel)
        texts = " ".join(lbl.text() for lbl in labels)
        assert "7" in texts

    def test_copy_button_per_summary(self, qtbot, db):
        db.save_summary("week", 3, "Week summary text")
        db.save_summary("today", 1, "Today summary text")
        dlg = HistoryDialog(db)
        qtbot.addWidget(dlg)
        copy_buttons = [b for b in dlg.findChildren(QPushButton) if b.text() == "Kopiuj"]
        assert len(copy_buttons) == 2

    def test_copy_button_sets_clipboard(self, qtbot, db, qapp):
        db.save_summary("week", 3, "Unique clipboard text 12345")
        dlg = HistoryDialog(db)
        qtbot.addWidget(dlg)
        copy_btn = next(b for b in dlg.findChildren(QPushButton) if b.text() == "Kopiuj")
        copy_btn.click()
        assert "Unique clipboard text 12345" in QApplication.clipboard().text()

    def test_shows_preview_text(self, qtbot, db):
        db.save_summary("month", 2, "Preview content here")
        dlg = HistoryDialog(db)
        qtbot.addWidget(dlg)
        labels = dlg.findChildren(QLabel)
        texts = " ".join(lbl.text() for lbl in labels)
        assert "Preview content here" in texts

    def test_long_preview_truncated(self, qtbot, db):
        long_text = "A" * 300
        db.save_summary("week", 1, long_text)
        dlg = HistoryDialog(db)
        qtbot.addWidget(dlg)
        labels = dlg.findChildren(QLabel)
        texts = " ".join(lbl.text() for lbl in labels)
        assert "A" * 300 not in texts
        assert "…" in texts


class TestFmtDate:
    def test_polish_months(self):
        dt = datetime(2026, 6, 5, tzinfo=timezone.utc)
        assert "czerwca" in _fmt_date(dt)

    def test_day_and_year(self):
        dt = datetime(2026, 3, 15, tzinfo=timezone.utc)
        result = _fmt_date(dt)
        assert "15" in result
        assert "2026" in result
