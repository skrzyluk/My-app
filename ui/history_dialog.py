from datetime import timezone

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QFrame, QApplication,
)
from PyQt6.QtCore import Qt

from database.db import Database
from models.summary import Summary

_PERIOD_LABELS = {
    "today": "Dzisiaj",
    "week":  "Tydzień",
    "month": "Miesiąc",
}

_POLISH_MONTHS = [
    "stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca",
    "lipca", "sierpnia", "września", "października", "listopada", "grudnia",
]


def _fmt_date(dt) -> str:
    d = dt.astimezone(timezone.utc)
    return f"{d.day} {_POLISH_MONTHS[d.month - 1]} {d.year}"


class HistoryDialog(QDialog):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self._db = db
        self.setWindowTitle("Historia podsumowań")
        self.setMinimumSize(560, 450)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        header = QLabel("Historia podsumowań")
        f = header.font()
        f.setPointSize(13)
        f.setBold(True)
        header.setFont(f)
        layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        container = QWidget()
        self._items_layout = QVBoxLayout(container)
        self._items_layout.setContentsMargins(0, 0, 0, 0)
        self._items_layout.setSpacing(6)
        self._items_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll, stretch=1)

        close_btn = QPushButton("Zamknij")
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

        self._populate()

    def _populate(self):
        summaries = self._db.get_summaries()
        if not summaries:
            placeholder = QLabel("Brak zapisanych podsumowań.")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("color: gray; padding: 40px;")
            self._items_layout.insertWidget(0, placeholder)
            return

        for i, summary in enumerate(summaries):
            self._items_layout.insertWidget(i, self._make_card(summary))

    def _make_card(self, summary: Summary) -> QFrame:
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)

        date_lbl = QLabel(_fmt_date(summary.created_at))
        f = date_lbl.font()
        f.setBold(True)
        date_lbl.setFont(f)
        top.addWidget(date_lbl)

        period_lbl = QLabel(_PERIOD_LABELS.get(summary.period, summary.period))
        period_lbl.setStyleSheet("color: gray;")
        top.addWidget(period_lbl)

        count_lbl = QLabel(f"({summary.videos_count} filmów)")
        count_lbl.setStyleSheet("color: gray;")
        top.addWidget(count_lbl)

        top.addStretch()

        copy_btn = QPushButton("Kopiuj")
        copy_btn.setFixedWidth(70)
        copy_btn.clicked.connect(
            lambda _checked=False, t=summary.summary_text: QApplication.clipboard().setText(t)
        )
        top.addWidget(copy_btn)

        layout.addLayout(top)

        preview = summary.summary_text[:200].rstrip()
        if len(summary.summary_text) > 200:
            preview += "…"
        preview_lbl = QLabel(preview)
        preview_lbl.setWordWrap(True)
        preview_lbl.setStyleSheet("color: #555; font-size: 12px;")
        layout.addWidget(preview_lbl)

        return card
