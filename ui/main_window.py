from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QScrollArea, QFrame, QApplication, QMessageBox, QMenu, QSystemTrayIcon,
    QSplitter, QLineEdit, QLayout, QSizePolicy,
)
from PyQt6.QtGui import QIcon, QCloseEvent, QPixmap, QPainter, QPainterPath, QColor
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl, QRect, QSize, QPoint
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt6 import sip
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

#: Avatar background colours, picked deterministically per channel.
_AVATAR_COLORS = [
    "#ff0000", "#1565c0", "#2e7d32", "#6a1b9a",
    "#c62828", "#0277bd", "#ef6c00", "#00838f",
]

_CARD_WIDTH = 300
_CARD_HEIGHT = 392           # fixed height so every collapsed tile is identical
_DESC_MAX_HEIGHT = 54        # ~3 lines while collapsed
_DESC_COLLAPSE_CHARS = 160   # show the "show more" toggle past this length


def _fmt_date(dt: datetime) -> str:
    d = dt.astimezone()
    return f"{d.day} {_SHORT_MONTHS[d.month - 1]} {d.year}"


def _video_noun(count: int) -> str:
    if count == 1:
        return i18n.tr("video_singular")
    if 2 <= count <= 4:
        return i18n.tr("video_2_4")
    return i18n.tr("video_many")


def _avatar_color(seed: str) -> str:
    if not seed:
        return _AVATAR_COLORS[0]
    return _AVATAR_COLORS[sum(map(ord, seed)) % len(_AVATAR_COLORS)]


def _app_icon() -> QIcon:
    if _ICON_PATH.exists():
        return QIcon(str(_ICON_PATH))
    return QIcon()


# ─────────────────────────────────────────────────────────────────────────── #
#  Background fetch worker                                                    #
# ─────────────────────────────────────────────────────────────────────────── #

class _FetchWorker(QThread):
    finished = pyqtSignal(list)
    error    = pyqtSignal(str)

    def __init__(self, provider: VideoProvider, period: str, force: bool = False):
        super().__init__()
        self._provider = provider
        self._period   = period
        self._force    = force

    def run(self):
        try:
            videos = (
                self._provider.force_refresh(self._period)
                if self._force
                else self._provider.get_videos(self._period)
            )
            self.finished.emit(videos)
        except Exception as e:
            logger.exception("Error fetching videos")
            self.error.emit(str(e))


# ─────────────────────────────────────────────────────────────────────────── #
#  Flow layout (responsive tile grid: reflows 3 → 2 → 1 columns)              #
# ─────────────────────────────────────────────────────────────────────────── #

class FlowLayout(QLayout):
    """A layout that arranges children left-to-right and wraps to new rows."""

    def __init__(self, parent=None, margin: int = 14, spacing: int = 12):
        super().__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self._items: list = []

    def addItem(self, item):
        self._items.append(item)

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect: QRect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.sizeHint())
        m = self.contentsMargins()
        size += QSize(m.left() + m.right(), m.top() + m.bottom())
        return size

    def _do_layout(self, rect: QRect, test_only: bool) -> int:
        m = self.contentsMargins()
        x = rect.x() + m.left()
        y = rect.y() + m.top()
        right = rect.right() - m.right()
        line_height = 0
        spacing = self.spacing()

        for item in self._items:
            hint = item.sizeHint()
            w, h = hint.width(), hint.height()
            # Respect the widget's own min/max height so fixed-size cards
            # (collapsed tiles) all lay out at an identical height.
            wgt = item.widget()
            if wgt is not None:
                h = max(h, wgt.minimumHeight())
                if wgt.maximumHeight() < (1 << 24):
                    h = min(h, wgt.maximumHeight())
            if x + w > right + 1 and line_height > 0:
                x = rect.x() + m.left()
                y += line_height + spacing
                line_height = 0
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), QSize(w, h)))
            x += w + spacing
            line_height = max(line_height, h)

        return y + line_height + m.bottom() - rect.y()


# ─────────────────────────────────────────────────────────────────────────── #
#  Thumbnail (top of the card)                                                #
# ─────────────────────────────────────────────────────────────────────────── #

_THUMB_W = _CARD_WIDTH - 2
_THUMB_H = round(_THUMB_W * 9 / 16)
_THUMB_RADIUS = 6

_net_manager: QNetworkAccessManager | None = None


def _network_manager() -> QNetworkAccessManager:
    global _net_manager
    if _net_manager is None:
        _net_manager = QNetworkAccessManager()
    return _net_manager


def _thumb_url(video_id: str) -> str:
    """YouTube thumbnail URL – available without an API call."""
    return f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg"


def _rounded_pixmap(src: QPixmap, w: int, h: int, radius: int = _THUMB_RADIUS) -> QPixmap:
    """Scale *src* to cover w×h, centre-crop, and clip to rounded corners."""
    scaled = src.scaled(
        w, h,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation,
    )
    x = max(0, (scaled.width() - w) // 2)
    y = max(0, (scaled.height() - h) // 2)
    cropped = scaled.copy(x, y, w, h)

    out = QPixmap(w, h)
    out.fill(Qt.GlobalColor.transparent)
    painter = QPainter(out)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    path.addRoundedRect(0.0, 0.0, float(w), float(h), float(radius), float(radius))
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, cropped)
    painter.end()
    return out


def _placeholder_pixmap(accent: str = "#ff0000", bg: str = "#1c1c1c") -> QPixmap:
    pm = QPixmap(_THUMB_W, _THUMB_H)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    path.addRoundedRect(0.0, 0.0, float(_THUMB_W), float(_THUMB_H),
                        float(_THUMB_RADIUS), float(_THUMB_RADIUS))
    painter.fillPath(path, QColor(bg))
    painter.setPen(QColor(accent))
    font = painter.font()
    font.setPointSize(28)
    painter.setFont(font)
    painter.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, "▶")
    painter.end()
    return pm


class _Thumbnail(QLabel):
    """16:9 thumbnail with a duration badge and optional NEW badge."""

    def __init__(self, video: Video, parent=None):
        super().__init__(parent)
        self.setObjectName("card_thumb")
        self.setFixedSize(_THUMB_W, _THUMB_H)
        self.setPixmap(_placeholder_pixmap())

        self._badge = QLabel(video.duration, self)
        self._badge.setObjectName("card_dur")
        self._badge.adjustSize()

        self._position_badge()
        self._load(video.video_id)

    def _position_badge(self):
        self._badge.move(
            _THUMB_W - self._badge.width() - 7,
            _THUMB_H - self._badge.height() - 7,
        )

    def _load(self, video_id: str):
        try:
            reply = _network_manager().get(QNetworkRequest(QUrl(_thumb_url(video_id))))
            reply.finished.connect(lambda r=reply: self._on_loaded(r))
        except Exception:
            logger.debug("Thumbnail request failed to start", exc_info=True)

    def _on_loaded(self, reply: QNetworkReply):
        try:
            if sip.isdeleted(self):
                return
            if reply.error() == QNetworkReply.NetworkError.NoError:
                pm = QPixmap()
                if pm.loadFromData(bytes(reply.readAll())) and not pm.isNull():
                    self.setPixmap(_rounded_pixmap(pm, _THUMB_W, _THUMB_H))
                    self._badge.raise_()
                    self._position_badge()
        except Exception:
            logger.debug("Thumbnail load failed", exc_info=True)
        finally:
            reply.deleteLater()


# ─────────────────────────────────────────────────────────────────────────── #
#  Video card widget                                                          #
# ─────────────────────────────────────────────────────────────────────────── #

class _VideoCard(QFrame):
    # Emitted (with self) when this card expands its description.
    expanded = pyqtSignal(object)

    def __init__(self, video: Video, parent=None):
        super().__init__(parent)
        self._video = video
        self.setObjectName("video_card")
        self.setFixedWidth(_CARD_WIDTH)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        self._desc_expanded = False
        self._desc: QLabel | None = None
        self._toggle_btn: QPushButton | None = None
        self._build()
        self._set_collapsed_geometry()

    # Text used for searching/filtering.
    def search_text(self) -> str:
        return " ".join([
            self._video.title or "",
            self._video.channel_title or "",
            self._video.description or "",
        ]).lower()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(_Thumbnail(self._video))

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(11, 11, 11, 11)
        body_layout.setSpacing(8)

        # Channel row: avatar · name · date
        chan_row = QHBoxLayout()
        chan_row.setSpacing(7)
        channel = self._video.channel_title or i18n.tr("card_no_channel")

        avatar = QLabel(channel[:1].upper())
        avatar.setObjectName("card_avatar")
        avatar.setFixedSize(22, 22)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(f"background-color: {_avatar_color(channel)};")
        chan_row.addWidget(avatar)

        name_lbl = QLabel(channel)
        name_lbl.setObjectName("card_channel_name")
        chan_row.addWidget(name_lbl, 1)

        date_lbl = QLabel(_fmt_date(self._video.published_at))
        date_lbl.setObjectName("card_date")
        chan_row.addWidget(date_lbl, 0, Qt.AlignmentFlag.AlignRight)
        body_layout.addLayout(chan_row)

        # Title (clamped to 2 lines so every card starts the same height)
        title_lbl = QLabel(self._video.title)
        title_lbl.setObjectName("card_title")
        title_lbl.setWordWrap(True)
        title_lbl.setMaximumHeight(40)
        body_layout.addWidget(title_lbl)

        # Separator
        sep = QFrame()
        sep.setObjectName("card_sep")
        sep.setFixedHeight(1)
        body_layout.addWidget(sep)

        # Description
        if self._video.description:
            desc_label = QLabel(i18n.tr("card_label_desc"))
            desc_label.setObjectName("card_desc_label")
            body_layout.addWidget(desc_label)

            self._desc = QLabel(self._video.description)
            self._desc.setObjectName("card_desc")
            self._desc.setWordWrap(True)
            body_layout.addWidget(self._desc)

            if len(self._video.description) > _DESC_COLLAPSE_CHARS:
                self._toggle_btn = QPushButton(i18n.tr("btn_show_more"))
                self._toggle_btn.setObjectName("toggle_desc_btn")
                self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                self._toggle_btn.clicked.connect(self._toggle_desc)
                body_layout.addWidget(self._toggle_btn, 0, Qt.AlignmentFlag.AlignLeft)

        body_layout.addStretch()

        # Action buttons – identical 2-column grid on every card
        actions = QHBoxLayout()
        actions.setSpacing(6)

        copy_btn = QPushButton(i18n.tr("btn_card_copy"))
        copy_btn.setObjectName("card_copy_btn")
        copy_btn.setProperty("card_btn", "true")
        copy_btn.setFixedHeight(30)
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self._copy)
        actions.addWidget(copy_btn, 1)

        yt_btn = QPushButton(i18n.tr("btn_card_youtube"))
        yt_btn.setObjectName("card_yt_btn")
        yt_btn.setProperty("card_btn", "yt")
        yt_btn.setFixedHeight(30)
        yt_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        yt_btn.clicked.connect(self._open_youtube)
        actions.addWidget(yt_btn, 1)

        body_layout.addLayout(actions)
        root.addWidget(body)

    # ── Collapse / expand (accordion: only one card expanded at a time) ── #

    def _set_collapsed_geometry(self):
        self.setMinimumHeight(_CARD_HEIGHT)
        self.setMaximumHeight(_CARD_HEIGHT)
        if self._desc is not None:
            self._desc.setMaximumHeight(_DESC_MAX_HEIGHT)

    def collapse(self):
        if not self._desc_expanded:
            return
        self._desc_expanded = False
        self._set_collapsed_geometry()
        if self._toggle_btn:
            self._toggle_btn.setText(i18n.tr("btn_show_more"))
        self._request_reflow()

    def expand(self):
        if self._desc_expanded:
            return
        self._desc_expanded = True
        self.setMaximumHeight(16_777_215)
        if self._desc is not None:
            self._desc.setMaximumHeight(16_777_215)
        if self._toggle_btn:
            self._toggle_btn.setText(i18n.tr("btn_show_less"))
        self.expanded.emit(self)
        self._request_reflow()

    def _toggle_desc(self):
        self.collapse() if self._desc_expanded else self.expand()

    def _request_reflow(self):
        self.updateGeometry()
        parent = self.parentWidget()
        if parent and parent.layout():
            parent.layout().invalidate()

    def _copy(self):
        QApplication.clipboard().setText(build_single_video_text(self._video))

    def _open_youtube(self):
        from PyQt6.QtGui import QDesktopServices
        QDesktopServices.openUrl(QUrl(self._video.url))


# ─────────────────────────────────────────────────────────────────────────── #
#  Main window                                                                #
# ─────────────────────────────────────────────────────────────────────────── #

class MainWindow(QMainWindow):
    def __init__(
        self,
        credentials: Credentials,
        *,
        db: Database | None = None,
        provider: VideoProvider | None = None,
    ):
        super().__init__()
        self._credentials     = credentials
        self._db              = db or Database()
        self._provider        = provider or VideoProvider(self._db, credentials)
        self._current_period  = "today"
        self._worker: _FetchWorker | None = None
        self._current_videos: list[Video] = []
        self._cards: list[_VideoCard] = []
        self._expanded_card: _VideoCard | None = None
        self._tray: QSystemTrayIcon | None = None
        self._bg_worker       = None
        self._quitting        = False

        self.setWindowTitle(i18n.tr("window_title"))
        self.setMinimumSize(720, 580)
        self._build_ui()
        self._setup_tray()
        self._start_background_worker()
        self._load_videos()

    # ─────────────────────────────────────────────────────────────────── #
    #  UI construction                                                    #
    # ─────────────────────────────────────────────────────────────────── #

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("central_widget")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._make_toolbar())
        root.addWidget(self._make_search_bar())

        # Body: tiles (left) + AI panel (right)
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setHandleWidth(1)
        self._splitter.setChildrenCollapsible(True)

        self._scroll = QScrollArea()
        self._scroll.setObjectName("tiles_scroll")
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._videos_container = QWidget()
        self._videos_container.setObjectName("tiles_container")
        self._videos_layout = FlowLayout(self._videos_container, margin=14, spacing=12)
        self._scroll.setWidget(self._videos_container)
        self._splitter.addWidget(self._scroll)

        from ui.ai_chat_widget import AiChatWidget
        self._chat_widget = AiChatWidget()
        self._chat_widget.closed.connect(self._on_chat_closed)
        self._chat_widget.setVisible(False)
        self._splitter.addWidget(self._chat_widget)
        self._splitter.setStretchFactor(0, 3)
        self._splitter.setStretchFactor(1, 2)

        root.addWidget(self._splitter, stretch=1)
        root.addWidget(self._make_status_bar())

        self._set_active_tab("today")

    def _make_toolbar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("toolbar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(8)

        # Period tabs grouped in a pill container
        tab_group = QFrame()
        tab_group.setObjectName("tab_group")
        tg_layout = QHBoxLayout(tab_group)
        tg_layout.setContentsMargins(3, 3, 3, 3)
        tg_layout.setSpacing(3)

        self._tab_buttons: dict[str, QPushButton] = {}
        for key, tr_key in _PERIOD_KEYS:
            btn = QPushButton(i18n.tr(tr_key))
            btn.setProperty("tab", "true")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _c, p=key: self._on_tab(p))
            self._tab_buttons[key] = btn
            tg_layout.addWidget(btn)
        layout.addWidget(tab_group)

        self._count_label = QLabel("")
        self._count_label.setObjectName("video_count")
        layout.addWidget(self._count_label)

        layout.addStretch()

        self._refresh_btn = QPushButton(i18n.tr("btn_refresh"))
        self._refresh_btn.setObjectName("refresh_btn")
        self._refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._refresh_btn.clicked.connect(self._on_refresh)
        layout.addWidget(self._refresh_btn)

        self._copy_all_btn = QPushButton(i18n.tr("btn_copy_all"))
        self._copy_all_btn.setObjectName("copy_all_btn")
        self._copy_all_btn.setProperty("tbtn", "true")
        self._copy_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._copy_all_btn.clicked.connect(self._on_copy_all)
        layout.addWidget(self._copy_all_btn)

        self._chat_btn = QPushButton(i18n.tr("btn_chat_ai"))
        self._chat_btn.setObjectName("ai_toggle_btn")
        self._chat_btn.setCheckable(True)
        self._chat_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._chat_btn.clicked.connect(self._on_toggle_chat)
        layout.addWidget(self._chat_btn)

        self._history_btn = QPushButton(i18n.tr("btn_history"))
        self._history_btn.setProperty("tbtn", "true")
        self._history_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._history_btn.clicked.connect(self._on_history)
        layout.addWidget(self._history_btn)

        self._settings_btn = QPushButton(i18n.tr("btn_settings"))
        self._settings_btn.setProperty("tbtn", "true")
        self._settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._settings_btn.clicked.connect(self._on_settings)
        layout.addWidget(self._settings_btn)

        return bar

    def _make_search_bar(self) -> QWidget:
        wrap = QWidget()
        wrap.setObjectName("search_wrap")
        layout = QHBoxLayout(wrap)
        layout.setContentsMargins(16, 7, 16, 7)
        layout.setSpacing(8)

        self._search_input = QLineEdit()
        self._search_input.setObjectName("search_input")
        self._search_input.setClearButtonEnabled(True)
        self._search_input.setPlaceholderText(i18n.tr("search_placeholder"))
        self._search_input.textChanged.connect(self._apply_search)
        layout.addWidget(self._search_input)
        return wrap

    def _make_status_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("statusbar")
        bar.setFixedHeight(34)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 6, 16, 6)
        layout.setSpacing(6)

        # _status_label doubles as the connection/status message.
        self._status_label = QLabel(i18n.tr("status_ready"))
        self._status_label.setObjectName("status_label")
        layout.addWidget(self._status_label)

        layout.addStretch()

        self._status_hint = QLabel(i18n.tr("statusbar_hint"))
        self._status_hint.setObjectName("status_hint")
        layout.addWidget(self._status_hint)
        return bar

    # ─────────────────────────────────────────────────────────────────── #
    #  Translation                                                        #
    # ─────────────────────────────────────────────────────────────────── #

    def retranslateUi(self):
        self.setWindowTitle(i18n.tr("window_title"))
        for key, tr_key in _PERIOD_KEYS:
            self._tab_buttons[key].setText(i18n.tr(tr_key))
        self._refresh_btn.setText(i18n.tr("btn_refresh"))
        self._copy_all_btn.setText(i18n.tr("btn_copy_all"))
        self._history_btn.setText(i18n.tr("btn_history"))
        self._settings_btn.setText(i18n.tr("btn_settings"))
        self._chat_btn.setText(i18n.tr("btn_chat_ai"))
        self._search_input.setPlaceholderText(i18n.tr("search_placeholder"))
        self._status_hint.setText(i18n.tr("statusbar_hint"))
        self._update_count_label()
        if self._tray:
            self._rebuild_tray_menu()

    # ─────────────────────────────────────────────────────────────────── #
    #  Search                                                             #
    # ─────────────────────────────────────────────────────────────────── #

    def _apply_search(self, text: str):
        needle = text.strip().lower()
        for card in self._cards:
            card.setVisible(not needle or needle in card.search_text())
        self._videos_layout.invalidate()
        self._videos_container.adjustSize()

    # ─────────────────────────────────────────────────────────────────── #
    #  AI Chat                                                            #
    # ─────────────────────────────────────────────────────────────────── #

    def _on_toggle_chat(self, checked: bool):
        self._chat_widget.setVisible(checked)
        if checked:
            self._chat_widget.set_videos(self._current_videos, self._current_period)

    def _on_chat_closed(self):
        self._chat_widget.setVisible(False)
        self._chat_btn.setChecked(False)

    # ─────────────────────────────────────────────────────────────────── #
    #  System tray                                                        #
    # ─────────────────────────────────────────────────────────────────── #

    def _setup_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("System tray not available.")
            return
        self._tray = QSystemTrayIcon(_app_icon(), self)
        self._tray.setToolTip(i18n.tr("app_title"))
        self._rebuild_tray_menu()
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    def _rebuild_tray_menu(self):
        if not self._tray:
            return
        menu = QMenu()
        menu.addAction(i18n.tr("tray_open"),    self._show_window)
        menu.addAction(i18n.tr("tray_refresh"), self._on_refresh)
        menu.addSeparator()
        menu.addAction(i18n.tr("tray_quit"),    self._quit_app)
        self._tray.setContextMenu(menu)

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

    # ─────────────────────────────────────────────────────────────────── #
    #  Background worker                                                  #
    # ─────────────────────────────────────────────────────────────────── #

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

    def _apply_notification_setting(self):
        enabled = self._db.get_setting("notifications", "true") == "true"
        if enabled and self._bg_worker is None:
            self._start_background_worker()
        elif not enabled and self._bg_worker is not None:
            self._bg_worker.stop()
            self._bg_worker = None
            logger.info("Background worker stopped (notifications disabled).")

    # ─────────────────────────────────────────────────────────────────── #
    #  Tab switching                                                      #
    # ─────────────────────────────────────────────────────────────────── #

    def _on_tab(self, period: str):
        if period == self._current_period:
            return
        self._current_period = period
        self._set_active_tab(period)
        self._load_videos()

    def _set_active_tab(self, period: str):
        for key, btn in self._tab_buttons.items():
            btn.setChecked(key == period)

    # ─────────────────────────────────────────────────────────────────── #
    #  Video loading                                                      #
    # ─────────────────────────────────────────────────────────────────── #

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
        if self._chat_widget.isVisible():
            self._chat_widget.set_videos(videos, self._current_period)

        count = len(videos)
        if count == 0:
            self._status_label.setText(i18n.tr("status_no_videos"))
        else:
            self._status_label.setText(f"{count} {_video_noun(count)}")
        self._update_count_label()
        self._set_idle()

    def _update_count_label(self):
        count = len(self._current_videos)
        self._count_label.setText(
            i18n.tr("video_count_fmt").format(count=count, noun=_video_noun(count))
        )

    def _on_fetch_error(self, message: str):
        self._set_idle()
        self._status_label.setText(i18n.tr("status_error"))
        QMessageBox.critical(self, i18n.tr("dlg_error"), message)

    def _render_videos(self, videos: list[Video]):
        # Clear existing items
        while self._videos_layout.count():
            item = self._videos_layout.takeAt(0)
            if item is not None and item.widget():
                item.widget().deleteLater()
        self._cards = []
        self._expanded_card = None

        if not videos:
            self._videos_layout.addWidget(self._make_empty_state())
            return

        for video in videos:
            card = _VideoCard(video)
            card.expanded.connect(self._on_card_expanded)
            self._cards.append(card)
            self._videos_layout.addWidget(card)

        # Re-apply any active search filter to the fresh cards.
        if self._search_input.text().strip():
            self._apply_search(self._search_input.text())

    def _on_card_expanded(self, card: _VideoCard):
        """Accordion: collapse the previously expanded card."""
        if self._expanded_card is not None and self._expanded_card is not card:
            self._expanded_card.collapse()
        self._expanded_card = card

    def _make_empty_state(self) -> QWidget:
        w = QWidget()
        w.setFixedWidth(self._scroll.viewport().width() - 28 if self._scroll.viewport().width() else 600)
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 60, 0, 60)

        icon_lbl = QLabel("▶")
        icon_lbl.setObjectName("empty_icon")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        f = icon_lbl.font()
        f.setPointSize(32)
        icon_lbl.setFont(f)
        layout.addWidget(icon_lbl)

        text_lbl = QLabel(i18n.tr("placeholder_no_videos"))
        text_lbl.setObjectName("empty_text")
        text_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(text_lbl)

        hint_lbl = QLabel(i18n.tr("status_no_videos"))
        hint_lbl.setObjectName("empty_hint")
        hint_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint_lbl)
        return w

    def _set_busy(self, text: str):
        self._status_label.setText(text)
        self._refresh_btn.setEnabled(False)
        self._copy_all_btn.setEnabled(False)

    def _set_idle(self):
        self._refresh_btn.setEnabled(True)
        self._copy_all_btn.setEnabled(bool(self._current_videos))

    # ─────────────────────────────────────────────────────────────────── #
    #  Button actions                                                     #
    # ─────────────────────────────────────────────────────────────────── #

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
        from config.settings import AppSettings
        dlg = SettingsDialog(self._db, self)
        dlg.exec()

        s = AppSettings()
        lang = self._db.get_setting("language", "pl") or "pl"
        i18n.set_language(lang)
        self.retranslateUi()
        theme = self._db.get_setting("theme", "system") or "system"
        apply_theme(
            QApplication.instance(), theme,
            white_text=s.white_text(), font_scale=s.font_size(),
        )
        self._apply_notification_setting()

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

    # ─────────────────────────────────────────────────────────────────── #
    #  Lifecycle                                                          #
    # ─────────────────────────────────────────────────────────────────── #

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
