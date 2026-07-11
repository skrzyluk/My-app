"""AI Chat side-panel widget for YouTube Notifier.

Layout (right-side panel, toggled by the main window):

  ┌──────────────────────────────┐
  │ 🤖 Asystent AI         [✕]  │  ← header
  ├──────────────────────────────┤
  │  [Podsumuj filmy]            │  ← quick-prompt chips (hidden after 1st msg)
  │  [Co polecasz?]              │
  │  [Który najdłuższy?]         │
  ├──────────────────────────────┤
  │  ╭──────────────────────╮   │
  │  │ AI: Cześć! Mam …     │   │  ← scroll area with message bubbles
  │  ╰──────────────────────╯   │
  │       ╭────────────────╮    │
  │       │ Ty: Podsumuj   │    │
  │       ╰────────────────╯    │
  ├──────────────────────────────┤
  │  [________________] [Wyślij] │  ← input row
  └──────────────────────────────┘
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QLineEdit, QSizePolicy, QApplication,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QKeyEvent, QColor, QPalette

import i18n
from utils.chat_render import to_html
from utils.logger import get_logger

logger = get_logger(__name__)

_QUICK_PROMPTS_PL = [
    "Podsumuj wszystkie filmy",
    "Co polecasz obejrzeć?",
    "Który film jest najdłuższy?",
    "Z jakich kanałów są filmy?",
]
_QUICK_PROMPTS_EN = [
    "Summarize all videos",
    "What do you recommend watching?",
    "Which video is the longest?",
    "What channels are the videos from?",
]


# ─────────────────────────────────────────────────────────────────────────── #
#  Background worker – calls Gemini in a separate thread                      #
# ─────────────────────────────────────────────────────────────────────────── #

class _AskWorker(QThread):
    reply_ready = pyqtSignal(str)
    error       = pyqtSignal(str)

    def __init__(self, session, message: str):
        super().__init__()
        self._session = session
        self._message = message

    def run(self):
        try:
            reply = self._session.send(self._message)
            self.reply_ready.emit(reply)
        except Exception as exc:
            logger.exception("AskWorker error")
            self.error.emit(str(exc))


# ─────────────────────────────────────────────────────────────────────────── #
#  Individual message bubble                                                  #
# ─────────────────────────────────────────────────────────────────────────── #

class _MessageBubble(QFrame):
    def __init__(self, text: str, role: str, parent=None,
                 title_urls: dict | None = None, show_copy: bool = False,
                 rich: bool = True):
        super().__init__(parent)
        # role: "user" | "assistant" | "system"
        self.setObjectName(f"bubble_{role}")
        self._raw_text   = text
        self._title_urls = title_urls or {}
        self._rich       = rich

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 7, 10, 7)
        layout.setSpacing(4)

        lbl = QLabel()
        lbl.setWordWrap(True)
        lbl.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
            | Qt.TextInteractionFlag.LinksAccessibleByMouse
            | Qt.TextInteractionFlag.LinksAccessibleByKeyboard
        )
        lbl.setOpenExternalLinks(True)
        lbl.setTextFormat(
            Qt.TextFormat.RichText if rich else Qt.TextFormat.PlainText
        )
        # Kolor linkow zalezny od tla babelka (bialy na akcencie, indygo na karcie)
        pal = lbl.palette()
        link_color = QColor("#ffffff") if role == "user" else QColor("#8b93ff")
        pal.setColor(QPalette.ColorRole.Link, link_color)
        lbl.setPalette(pal)
        layout.addWidget(lbl)
        self._lbl = lbl
        self._render(text)

        if show_copy:
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.addStretch()
            self._copy_btn = QPushButton("⧉")
            self._copy_btn.setObjectName("chat_copy_btn")
            self._copy_btn.setFixedSize(24, 20)
            self._copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._copy_btn.setToolTip(i18n.tr("chat_copy"))
            self._copy_btn.clicked.connect(self._copy)
            row.addWidget(self._copy_btn)
            layout.addLayout(row)

    def _render(self, text: str):
        if self._rich:
            self._lbl.setText(to_html(text, self._title_urls))
        else:
            self._lbl.setText(text)

    def _copy(self):
        QApplication.clipboard().setText(self._raw_text)
        self._copy_btn.setText("✓")
        self._copy_btn.setToolTip(i18n.tr("chat_copied"))
        QTimer.singleShot(1200, self._reset_copy_icon)

    def _reset_copy_icon(self):
        self._copy_btn.setText("⧉")
        self._copy_btn.setToolTip(i18n.tr("chat_copy"))

    def set_text(self, text: str):
        self._raw_text = text
        self._render(text)


# ─────────────────────────────────────────────────────────────────────────── #
#  Main chat widget                                                           #
# ─────────────────────────────────────────────────────────────────────────── #

class AiChatWidget(QWidget):
    """Collapsible side-panel with an AI chat interface."""

    # Emitted when the user closes the panel
    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ai_chat_panel")
        self.setMinimumWidth(280)
        self.setMaximumWidth(440)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        self._session = None          # ChatSession (created lazily)
        self._videos  = []
        self._period  = "week"
        self._worker: _AskWorker | None = None
        self._typing_bubble: _MessageBubble | None = None
        self._dots_timer = QTimer(self)
        self._dots_timer.setInterval(500)
        self._dots_timer.timeout.connect(self._animate_dots)
        self._dots_count = 0

        self._build_ui()

    # ─────────────────────────────────────────────────────────────────── #
    #  Public API                                                         #
    # ─────────────────────────────────────────────────────────────────── #

    def set_videos(self, videos: list, period: str = "week"):
        """Update the video context and reset the chat session."""
        self._videos = videos
        self._period = period
        self._session = None          # will be (re-)created on first send
        self._reset_conversation(videos, period)

    # ─────────────────────────────────────────────────────────────────── #
    #  UI construction                                                    #
    # ─────────────────────────────────────────────────────────────────── #

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._make_header())

        # Quick-prompt chips
        self._quick_bar = self._make_quick_bar()
        root.addWidget(self._quick_bar)

        # Scroll area – messages
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._msg_container = QWidget()
        self._msg_container.setObjectName("msg_container")
        self._msg_layout = QVBoxLayout(self._msg_container)
        self._msg_layout.setContentsMargins(10, 8, 10, 8)
        self._msg_layout.setSpacing(8)
        self._msg_layout.addStretch()
        self._scroll.setWidget(self._msg_container)
        root.addWidget(self._scroll, stretch=1)

        root.addWidget(self._make_input_bar())

        self._note = QLabel(i18n.tr("chat_note"))
        self._note.setObjectName("chat_note")
        self._note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self._note)

    def _make_header(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("chat_header")
        bar.setFixedHeight(52)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(8)

        icon = QLabel("🤖")
        f = icon.font()
        f.setPointSize(16)
        icon.setFont(f)
        layout.addWidget(icon)

        text_col = QVBoxLayout()
        text_col.setSpacing(0)
        title = QLabel(i18n.tr("chat_title"))
        title.setObjectName("chat_header_title")
        f2 = title.font()
        f2.setBold(True)
        f2.setPointSize(10)
        title.setFont(f2)
        text_col.addWidget(title)

        self._subtitle = QLabel(i18n.tr("chat_subtitle_ollama"))
        self._subtitle.setObjectName("chat_subtitle")
        text_col.addWidget(self._subtitle)
        layout.addLayout(text_col, 1)

        self._live = QLabel(f"● {i18n.tr('chat_ready')}")
        self._live.setObjectName("chat_live")
        layout.addWidget(self._live)

        new_btn = QPushButton("🗑")
        new_btn.setObjectName("chat_new_btn")
        new_btn.setFixedSize(28, 28)
        new_btn.setToolTip(i18n.tr("chat_new"))
        new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_btn.clicked.connect(self._new_chat)
        layout.addWidget(new_btn)

        close_btn = QPushButton("✕")
        close_btn.setObjectName("chat_close_btn")
        close_btn.setFixedSize(28, 28)
        close_btn.setToolTip(i18n.tr("chat_close"))
        close_btn.clicked.connect(self.closed.emit)
        layout.addWidget(close_btn)
        return bar

    def _make_quick_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("quick_bar")
        layout = QVBoxLayout(bar)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(5)

        lang = i18n.current_language() if hasattr(i18n, "current_language") else "pl"
        prompts = _QUICK_PROMPTS_EN if lang == "en" else _QUICK_PROMPTS_PL
        self._quick_btns = []
        for prompt in prompts:
            btn = QPushButton(prompt)
            btn.setObjectName("quick_prompt_btn")
            btn.clicked.connect(lambda _c, p=prompt: self._send(p))
            layout.addWidget(btn)
            self._quick_btns.append(btn)
        return bar

    def _make_input_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("chat_input_bar")
        bar.setFixedHeight(52)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        self._input = _EnterLineEdit()
        self._input.setObjectName("chat_input")
        self._input.setPlaceholderText(i18n.tr("chat_placeholder"))
        self._input.enter_pressed.connect(self._on_send)
        layout.addWidget(self._input, stretch=1)

        self._send_btn = QPushButton(i18n.tr("chat_send"))
        self._send_btn.setObjectName("chat_send_btn")
        self._send_btn.setFixedHeight(34)
        self._send_btn.clicked.connect(self._on_send)
        layout.addWidget(self._send_btn)
        return bar

    # ─────────────────────────────────────────────────────────────────── #
    #  Message helpers                                                    #
    # ─────────────────────────────────────────────────────────────────── #

    def _reset_conversation(self, videos: list, period: str):
        """Clear the message list and show a new welcome message."""
        # Remove all bubbles
        while self._msg_layout.count() > 1:
            item = self._msg_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Show quick prompts again
        self._quick_bar.setVisible(True)

        period_labels = {"today": "dzisiaj", "week": "ostatniego tygodnia", "month": "ostatniego miesiąca"}
        label = period_labels.get(period, period)
        welcome = i18n.tr("chat_welcome").format(count=len(videos), period=label)
        self._add_bubble(welcome, "assistant")

    def _add_bubble(self, text: str, role: str, *, show_copy: bool = False,
                    link_titles: bool = False, rich: bool = True) -> _MessageBubble:
        bubble = _MessageBubble(
            text, role,
            title_urls=self._title_urls() if link_titles else None,
            show_copy=show_copy,
            rich=rich,
        )
        # Insert before the trailing stretch
        idx = max(self._msg_layout.count() - 1, 0)
        self._msg_layout.insertWidget(idx, bubble)
        QTimer.singleShot(30, self._scroll_to_bottom)
        return bubble

    def _title_urls(self) -> dict:
        """Mapowanie tytul filmu -> URL, do klikalnych tytulow w odpowiedziach."""
        result = {}
        for v in self._videos:
            if hasattr(v, "title"):
                title, url = v.title, getattr(v, "url", "")
            else:
                title, url = v.get("title", ""), v.get("url", "")
            if title and url:
                result[title] = url
        return result

    def _scroll_to_bottom(self):
        sb = self._scroll.verticalScrollBar()
        sb.setValue(sb.maximum())

    # ─────────────────────────────────────────────────────────────────── #
    #  Typing indicator                                                   #
    # ─────────────────────────────────────────────────────────────────── #

    def _start_typing(self):
        self._typing_bubble = self._add_bubble("●", "assistant", rich=False)
        self._dots_count = 0
        self._dots_timer.start()

    def _stop_typing(self):
        self._dots_timer.stop()
        if self._typing_bubble:
            self._typing_bubble.deleteLater()
            self._typing_bubble = None

    def _animate_dots(self):
        self._dots_count = (self._dots_count + 1) % 4
        dots = "●" * (self._dots_count + 1) + "○" * (3 - self._dots_count)
        if self._typing_bubble:
            self._typing_bubble.set_text(dots)

    # ─────────────────────────────────────────────────────────────────── #
    #  Send logic                                                         #
    # ─────────────────────────────────────────────────────────────────── #

    def _new_chat(self):
        """Wyczysc rozmowe i zresetuj sesje (bez przeladowania listy filmow)."""
        if self._worker and self._worker.isRunning():
            return
        self._stop_typing()
        self._session = None
        self._reset_conversation(self._videos, self._period)

    def _on_send(self):
        text = self._input.text().strip()
        if text:
            self._send(text)
            self._input.clear()

    def _send(self, message: str):
        if self._worker and self._worker.isRunning():
            return

        # Hide quick prompts after first message
        self._quick_bar.setVisible(False)

        # Ensure session exists
        if self._session is None:
            from services.ai_service import create_chat_session
            try:
                self._session = create_chat_session(self._videos)
            except RuntimeError as exc:
                self._add_bubble(str(exc), "system")
                return

        self._add_bubble(message, "user")
        self._set_busy(True)
        self._start_typing()

        self._worker = _AskWorker(self._session, message)
        self._worker.reply_ready.connect(self._on_reply)
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(lambda: self._set_busy(False))
        self._worker.start()

    def _on_reply(self, text: str):
        self._stop_typing()
        self._add_bubble(text, "assistant", show_copy=True, link_titles=True)

    def _on_error(self, msg: str):
        self._stop_typing()
        self._add_bubble(f"❌ {msg}", "system")

    def _set_busy(self, busy: bool):
        self._input.setEnabled(not busy)
        self._send_btn.setEnabled(not busy)


# ─────────────────────────────────────────────────────────────────── #
#  Line edit with Enter key support                                   #
# ─────────────────────────────────────────────────────────────────── #

class _EnterLineEdit(QLineEdit):
    enter_pressed = pyqtSignal()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.enter_pressed.emit()
        else:
            super().keyPressEvent(event)
