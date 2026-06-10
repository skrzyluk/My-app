from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QFrame, QApplication,
)
from PyQt6.QtCore import Qt

import i18n
from database.db import Database
from models.summary import Summary

_PERIOD_TR_KEYS = {
    "today": "tab_today",
    "week":  "tab_week",
    "month": "tab_month",
}

_POLISH_MONTHS = [
    "stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca",
    "lipca", "sierpnia", "września", "października", "listopada", "grudnia",
]


def _fmt_date(dt) -> str:
    d = dt.astimezone()
    return f"{d.day} {_POLISH_MONTHS[d.month - 1]} {d.year}"


class HistoryDialog(QDialog):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self._db = db
        self.setWindowTitle(i18n.tr("dlg_history_title"))
        self.setMinimumSize(560, 450)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header = QLabel(i18n.tr("dlg_history_title"))
        f = header.font()
        f.setPointSize(14)
        f.setBold(True)
        header.setFont(f)
        layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        container = QWidget()
        self._items_layout = QVBoxLayout(container)
        self._items_layout.setContentsMargins(0, 0, 0, 0)
        self._items_layout.setSpacing(8)
        self._items_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll, stretch=1)

        self._close_btn = QPushButton(i18n.tr("btn_close"))
        self._close_btn.setFixedWidth(100)
        self._close_btn.setFixedHeight(32)
        self._close_btn.clicked.connect(self.accept)
        layout.addWidget(self._close_btn, alignment=Qt.AlignmentFlag.AlignRight)

        self._populate()

    def _populate(self):
        summaries = self._db.get_summaries()
        if not summaries:
            placeholder = QLabel(i18n.tr("lbl_no_summaries"))
            placeholder.setObjectName("history_empty")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setContentsMargins(0, 40, 0, 40)
            self._items_layout.insertWidget(0, placeholder)
            return

        for idx, summary in enumerate(summaries):
            self._items_layout.insertWidget(idx, self._make_card(summary))

    def _make_card(self, summary: Summary) -> QFrame:
        card = QFrame()
        card.setObjectName("history_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(8)

        date_lbl = QLabel(_fmt_date(summary.created_at))
        date_lbl.setObjectName("history_date")
        top.addWidget(date_lbl)

        period_key = _PERIOD_TR_KEYS.get(summary.period, "tab_today")
        period_lbl = QLabel(i18n.tr(period_key))
        period_lbl.setObjectName("history_period")
        top.addWidget(period_lbl)

        count_lbl = QLabel(i18n.tr("lbl_videos_count_fmt").format(summary.videos_count))
        count_lbl.setObjectName("history_count")
        top.addWidget(count_lbl)

        top.addStretch()

        copy_btn = QPushButton(i18n.tr("btn_copy"))
        copy_btn.setFixedWidth(72)
        copy_btn.setFixedHeight(26)
        copy_btn.clicked.connect(
            lambda _checked=False, t=summary.summary_text: QApplication.clipboard().setText(t)
        )
        top.addWidget(copy_btn)

        layout.addLayout(top)

        preview = summary.summary_text[:200].rstrip()
        if len(summary.summary_text) > 200:
            preview += "…"
        preview_lbl = QLabel(preview)
        preview_lbl.setObjectName("history_preview")
        preview_lbl.setWordWrap(True)
        layout.addWidget(preview_lbl)

        return card
