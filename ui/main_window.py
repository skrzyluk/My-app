from datetime import datetime, timezone
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QScrollArea, QFrame, QApplication, QMessageBox, QMenu, QSystemTrayIcon,
)
from PyQt6.QtGui import QIcon, QCloseEvent
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from google.oauth2.credentials import Credentials

import i18n
from database.db import Database
from models.video import Video
from services.video_provider import VideoProvider
from utils.summary_builder import build_single_video_text, build_summary_text
from utils.logger import get_logger

logger = get_logger(__name__)

_PERIOD_KEYS = [
    ("today", "tab_today"),
    ("week",  "tab_week"),
    ("month", "tab_month"),
]

_SHORT_MONTHS = [
    "sty", "lut", "mar", "kwi", "maj", "cze",
    "lip", "sie", "wrz", "paź", "lis", "gru",
]

_ICON_PATH = Path(__file__).resolve().parent.parent / "resources" / "icon.ico"


def _fmt_date(dt: datetime) -> str:
    d = dt.astimezone(timezone.utc)
    return f"{d.day} {_SHORT_MONTHS[d.month - 1]} {d.year}"


def _app_icon() -> QIcon:
    if _ICON_PATH.exists():
        return QIcon(str(_ICON_PATH))
    return QIcon()


# ------------------------------------------------------------------ #
# Background fetch worker                                             #
# ------------------------------------------------------------------ #

class _FetchWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, provider: VideoProvider, period: str, force: bool = False):
        super().__init__()
        self._provider = provider
        self._period = period
        self._force = force

    def run(self):
        try:
            if self._force:
                videos = self._provider.force_refresh(self._period)
            else:
                videos = self._provider.get_videos(self._period)
            self.finished.emit(videos)
        except Exception as e:
            logger.exception("Error fetching videos")
            self.error.emit(str(e))


# ------------------------------------------------------------------ #
# Video card widget                                                   #
# ------------------------------------------------------------------ #

class _VideoCard(QFrame):
    def __init__(self, video: Video, parent=None):
        super().__init__(parent)
        self._video = video
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setLineWidth(1)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        title_label = QLabel(self._video.title)
        title_label.setWordWrap(True)
        f = title_label.font()
        f.setBold(True)
        title_label.setFont(f)
        layout.addWidget(title_label)

        meta_row = QHBoxLayout()
        meta_row.setContentsMargins(0, 0, 0, 0)
        meta = QLabel(f"⏱ {self._video.duration}  •  📅 {_fmt_date(self._video.published_at)}")
        meta.setStyleSheet("color: gray;")
        meta_row.addWidget(meta)
        meta_row.addStretch()
        self._copy_btn = QPushButton(i18n.tr("btn_copy"))
        self._copy_btn.setFixedWidth(70)
        self._copy_btn.clicked.connect(self._copy)
        meta_row.addWidget(self._copy_btn)
        layout.addLayout(meta_row)

        if self._video.description:
            desc_text = self._video.description[:150].rstrip()
            if len(self._video.description) > 150:
                desc_text += "…"
            desc = QLabel(desc_text)
            desc.setWordWrap(True)
            desc.setStyleSheet("color: #555;")
            layout.addWidget(desc)

        link = QLabel(f'<a href="{self._video.url}">{self._video.url}</a>')
        link.setOpenExternalLinks(True)
        link.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(link)

    def _copy(self):
        QApplication.clipboard().setText(build_single_video_text(self._video))


# ------------------------------------------------------------------ #
# Main window                                                         #
# ------------------------------------------------------------------ #

class MainWindow(QMainWindow):
    def __init__(
        self,
        credentials: Credentials,
        *,
        db: Database | None = None,
        provider: VideoProvider | None = None,
    ):
        super().__init__()
        self._credentials = credentials
        self._db = db or Database()
        self._provider = provider or VideoProvider(self._db, credentials)
        self._current_period = "today"
        self._worker: _FetchWorker | None = None
        self._current_videos: list[Video] = []
        self._tray: QSystemTrayIcon | None = None
        self._bg_worker = None
        self._quitting = False

        self.setWindowTitle(i18n.tr("window_title"))
        self.setMinimumSize(700, 550)
        self._build_ui()
        self._setup_tray()
        self._start_background_worker()
        self._load_videos()

    # ------------------------------------------------------------------ #
    # UI construction                                                     #
    # ------------------------------------------------------------------ #

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._make_tab_bar())

        self._status_label = QLabel("")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setFixedHeight(24)
        self._status_label.setStyleSheet("color: gray; font-size: 12px;")
        root.addWidget(self._status_label)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._videos_container = QWidget()
        self._videos_layout = QVBoxLayout(self._videos_container)
        self._videos_layout.setContentsMargins(8, 4, 8, 4)
        self._videos_layout.setSpacing(6)
        self._videos_layout.addStretch()
        self._scroll.setWidget(self._videos_container)
        root.addWidget(self._scroll, stretch=1)

        root.addWidget(self._make_action_bar())

        self._set_active_tab("today")

    def _make_tab_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(44)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)

        self._tab_buttons: dict[str, QPushButton] = {}
        for key, tr_key in _PERIOD_KEYS:
            btn = QPushButton(i18n.tr(tr_key))
            btn.setCheckable(True)
            btn.setFixedHeight(32)
            btn.clicked.connect(lambda _checked, p=key: self._on_tab(p))
            self._tab_buttons[key] = btn
            layout.addWidget(btn)
        layout.addStretch()
        return bar

    def _make_action_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(52)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self._refresh_btn = QPushButton(i18n.tr("btn_refresh"))
        self._refresh_btn.clicked.connect(self._on_refresh)
        layout.addWidget(self._refresh_btn)

        self._copy_all_btn = QPushButton(i18n.tr("btn_copy_all"))
        self._copy_all_btn.clicked.connect(self._on_copy_all)
        layout.addWidget(self._copy_all_btn)

        layout.addStretch()

        self._history_btn = QPushButton(i18n.tr("btn_history"))
        self._history_btn.clicked.connect(self._on_history)
        layout.addWidget(self._history_btn)

        self._settings_btn = QPushButton(i18n.tr("btn_settings"))
        self._settings_btn.clicked.connect(self._on_settings)
        layout.addWidget(self._settings_btn)

        return bar

    # ------------------------------------------------------------------ #
    # Translation                                                         #
    # ------------------------------------------------------------------ #

    def retranslateUi(self):
        """Re-apply all translatable strings after a language change."""
        self.setWindowTitle(i18n.tr("window_title"))
        for key, tr_key in _PERIOD_KEYS:
            self._tab_buttons[key].setText(i18n.tr(tr_key))
        self._refresh_btn.setText(i18n.tr("btn_refresh"))
        self._copy_all_btn.setText(i18n.tr("btn_copy_all"))
        self._history_btn.setText(i18n.tr("btn_history"))
        self._settings_btn.setText(i18n.tr("btn_settings"))
        if self._tray:
            self._rebuild_tray_menu()

    def _rebuild_tray_menu(self):
        if not self._tray:
            return
        menu = QMenu()
        menu.addAction(i18n.tr("tray_open"), self._show_window)
        menu.addAction(i18n.tr("tray_refresh"), self._on_refresh)
        menu.addSeparator()
        menu.addAction(i18n.tr("tray_quit"), self._quit_app)
        self._tray.setContextMenu(menu)

    # ------------------------------------------------------------------ #
    # System tray                                                         #
    # ------------------------------------------------------------------ #

    def _setup_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("System tray not available.")
            return

        self._tray = QSystemTrayIcon(_app_icon(), self)
        self._tray.setToolTip(i18n.tr("app_title"))
        self._rebuild_tray_menu()
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_window()

    def _show_window(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def _quit_app(self):
        self._quitting = True
        self._cleanup()
        QApplication.instance().quit()

    # ------------------------------------------------------------------ #
    # Background worker                                                   #
    # ------------------------------------------------------------------ #

    def _start_background_worker(self):
        if self._db.get_setting("notifications", "true") != "true":
            return
        from workers.background_worker import BackgroundWorker
        from services.notification_service import NotificationService
        self._notif_service = NotificationService()
        self._bg_worker = BackgroundWorker(self._provider)
        self._bg_worker.new_videos_found.connect(self._on_new_videos_found)
        self._bg_worker.start()
        logger.info("Background worker started.")

    def _on_new_videos_found(self, count: int):
        if hasattr(self, "_notif_service"):
            self._notif_service.show_new_videos(count)

    # ------------------------------------------------------------------ #
    # Tab switching                                                       #
    # ------------------------------------------------------------------ #

    def _on_tab(self, period: str):
        if period == self._current_period:
            return
        self._current_period = period
        self._set_active_tab(period)
        self._load_videos()

    def _set_active_tab(self, period: str):
        for key, btn in self._tab_buttons.items():
            btn.setChecked(key == period)

    # ------------------------------------------------------------------ #
    # Video loading                                                       #
    # ------------------------------------------------------------------ #

    def _load_videos(self, force: bool = False):
        if self._worker and self._worker.isRunning():
            return
        self._set_busy(i18n.tr("status_loading"))
        self._worker = _FetchWorker(self._provider, self._current_period, force=force)
        self._worker.finished.connect(self._on_videos_loaded)
        self._worker.error.connect(self._on_fetch_error)
        self._worker.start()

    def _on_videos_loaded(self, videos: list[Video]):
        self._current_videos = videos
        self._render_videos(videos)
        count = len(videos)
        if count == 0:
            self._status_label.setText(i18n.tr("status_no_videos"))
        else:
            noun_key = (
                "video_singular" if count == 1
                else ("video_2_4" if 2 <= count <= 4 else "video_many")
            )
            self._status_label.setText(f"{count} {i18n.tr(noun_key)}")
        self._set_idle()

    def _on_fetch_error(self, message: str):
        self._set_idle()
        self._status_label.setText(i18n.tr("status_error"))
        QMessageBox.critical(self, i18n.tr("dlg_error"), message)

    def _render_videos(self, videos: list[Video]):
        while self._videos_layout.count() > 1:
            item = self._videos_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not videos:
            placeholder = QLabel(i18n.tr("placeholder_no_videos"))
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("color: gray; padding: 40px;")
            self._videos_layout.insertWidget(0, placeholder)
            return

        for idx, video in enumerate(videos):
            self._videos_layout.insertWidget(idx, _VideoCard(video))

    def _set_busy(self, text: str):
        self._status_label.setText(text)
        self._refresh_btn.setEnabled(False)
        self._copy_all_btn.setEnabled(False)

    def _set_idle(self):
        self._refresh_btn.setEnabled(True)
        self._copy_all_btn.setEnabled(bool(self._current_videos))

    # ------------------------------------------------------------------ #
    # Button actions                                                      #
    # ------------------------------------------------------------------ #

    def _on_refresh(self):
        self._load_videos(force=True)

    def _on_copy_all(self):
        if not self._current_videos:
            return
        QApplication.clipboard().setText(
            build_summary_text(self._current_videos, self._current_period)
        )

    def _on_history(self):
        from ui.history_dialog import HistoryDialog
        HistoryDialog(self._db, self).exec()

    def _on_settings(self):
        from ui.settings_dialog import SettingsDialog
        from config.theme import apply_theme
        dlg = SettingsDialog(self._db, self)
        dlg.exec()

        # Apply any changed settings immediately
        lang = self._db.get_setting("language", "pl") or "pl"
        i18n.set_language(lang)
        self.retranslateUi()
        theme = self._db.get_setting("theme", "system") or "system"
        apply_theme(QApplication.instance(), theme)

        if dlg.logout_requested:
            self._handle_logout()

    def _handle_logout(self):
        from services.auth_service import AuthService
        from ui.login_window import LoginWindow
        AuthService().logout()
        if self._tray:
            self._tray.hide()
        self._quitting = True
        self._cleanup()
        self._login_window = LoginWindow()
        self._login_window.show()
        self.close()

    # ------------------------------------------------------------------ #
    # Lifecycle                                                           #
    # ------------------------------------------------------------------ #

    def _cleanup(self):
        if self._bg_worker:
            self._bg_worker.stop()
            self._bg_worker = None
        self._db.close()

    def closeEvent(self, event: QCloseEvent):
        if self._tray and self._tray.isVisible() and not self._quitting:
            event.ignore()
            self.hide()
        else:
            self._cleanup()
            event.accept()
