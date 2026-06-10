from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QComboBox, QCheckBox, QFrame, QMessageBox, QLineEdit, QButtonGroup,
)
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt, QSize

import i18n
from config.settings import AppSettings
from database.db import Database
from resources.styles import THEMES, resolve_theme
from services.ai_service import get_api_key


# theme id → (i18n key, accent colour for the swatch dot)
_THEME_OPTIONS: list[tuple[str, str]] = [
    ("system", "theme_system_label"),
    ("dark-crimson", "theme_dark_crimson"),
    ("dark-ocean", "theme_dark_ocean"),
    ("dark-forest", "theme_dark_forest"),
    ("dark-violet", "theme_dark_violet"),
    ("dark-amber", "theme_dark_amber"),
    ("light-classic", "theme_light_classic"),
    ("high-contrast", "theme_high_contrast"),
]

_FONT_OPTIONS: list[tuple[str, str]] = [
    ("small", "font_small"),
    ("normal", "font_normal"),
    ("large", "font_large"),
    ("xlarge", "font_xlarge"),
]


_PREVIEW_W, _PREVIEW_H = 48, 32


def _theme_preview_icon(theme_id: str) -> QIcon:
    """A tiny live-ish preview of a theme: app bg + card + accent bar + text lines."""
    if theme_id == "system":
        bg, card, accent, line = "#2b2b2b", "#3d3d3d", "#8a8a8a", "#9e9e9e"
    else:
        t = THEMES[theme_id]
        bg, card, accent, line = t["bg_app"], t["bg_card"], t["accent"], t["text_secondary"]

    pm = QPixmap(_PREVIEW_W, _PREVIEW_H)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(Qt.PenStyle.NoPen)

    p.setBrush(QColor(bg))
    p.drawRoundedRect(0, 0, _PREVIEW_W, _PREVIEW_H, 5, 5)
    p.setBrush(QColor(card))
    p.drawRoundedRect(5, 6, _PREVIEW_W - 10, _PREVIEW_H - 12, 3, 3)
    p.setBrush(QColor(accent))
    p.drawRoundedRect(9, 10, 12, 4, 2, 2)
    p.setBrush(QColor(line))
    p.drawRect(9, 17, _PREVIEW_W - 20, 2)
    p.drawRect(9, 21, _PREVIEW_W - 26, 2)
    p.end()
    return QIcon(pm)


class SettingsDialog(QDialog):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self._db = db
        self._app_settings = AppSettings()
        self.logout_requested = False
        self._selected_theme = "system"
        self._selected_font = "normal"
        self.setWindowTitle(i18n.tr("dlg_settings_title"))
        self.setMinimumWidth(430)
        self._build_ui()
        self._load_settings()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        header = QLabel(f"⚙  {i18n.tr('dlg_settings_title')}")
        f = header.font()
        f.setPointSize(13)
        f.setBold(True)
        header.setFont(f)
        layout.addWidget(header)

        # ── Theme palette ───────────────────────────────────────────── #
        layout.addWidget(self._section_label(i18n.tr("lbl_appearance")))
        theme_grid = QGridLayout()
        theme_grid.setSpacing(6)
        self._theme_group = QButtonGroup(self)
        self._theme_group.setExclusive(True)
        self._theme_buttons: dict[str, QPushButton] = {}
        for idx, (theme_id, tr_key) in enumerate(_THEME_OPTIONS):
            btn = QPushButton(i18n.tr(tr_key))
            btn.setProperty("swatch", "true")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setIcon(_theme_preview_icon(theme_id))
            btn.setIconSize(QSize(_PREVIEW_W, _PREVIEW_H))
            btn.setMinimumHeight(44)
            btn.clicked.connect(lambda _c, t=theme_id: self._select_theme(t))
            self._theme_group.addButton(btn)
            self._theme_buttons[theme_id] = btn
            theme_grid.addWidget(btn, idx // 2, idx % 2)
        layout.addLayout(theme_grid)

        # ── Font size ───────────────────────────────────────────────── #
        layout.addWidget(self._section_label(i18n.tr("lbl_font_size")))
        font_row = QHBoxLayout()
        font_row.setSpacing(5)
        self._font_group = QButtonGroup(self)
        self._font_group.setExclusive(True)
        self._font_buttons: dict[str, QPushButton] = {}
        for size_id, tr_key in _FONT_OPTIONS:
            btn = QPushButton(f"Aa\n{i18n.tr(tr_key)}")
            btn.setProperty("fontbtn", "true")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _c, s=size_id: self._select_font(s))
            self._font_group.addButton(btn)
            self._font_buttons[size_id] = btn
            font_row.addWidget(btn)
        layout.addLayout(font_row)

        # ── Text accessibility (white text) ─────────────────────────── #
        layout.addWidget(self._section_label(i18n.tr("lbl_text_accessibility")))
        self._white_text_check = QCheckBox(i18n.tr("lbl_white_text"))
        layout.addWidget(self._white_text_check)
        wt_desc = QLabel(i18n.tr("desc_white_text"))
        wt_desc.setObjectName("settings_hint")
        wt_desc.setWordWrap(True)
        layout.addWidget(wt_desc)

        # ── Language ────────────────────────────────────────────────── #
        lang_row = QHBoxLayout()
        lang_row.addWidget(QLabel(i18n.tr("lbl_language")))
        lang_row.addStretch()
        self._lang_combo = QComboBox()
        self._lang_combo.addItems([i18n.tr("lang_polish"), i18n.tr("lang_english")])
        self._lang_combo.setFixedWidth(150)
        lang_row.addWidget(self._lang_combo)
        layout.addLayout(lang_row)

        # ── Background notifications ─────────────────────────────────── #
        notif_row = QHBoxLayout()
        notif_row.addWidget(QLabel(i18n.tr("lbl_notif_title")))
        notif_row.addStretch()
        self._notif_check = QCheckBox()
        notif_row.addWidget(self._notif_check)
        layout.addLayout(notif_row)

        # ── AI Assistant ─────────────────────────────────────────────── #
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep)

        layout.addWidget(self._section_label(i18n.tr("lbl_ai_section")))

        url_row = QHBoxLayout()
        url_row.addWidget(QLabel(i18n.tr("lbl_ollama_url")))
        self._ollama_url_input = QLineEdit()
        self._ollama_url_input.setPlaceholderText("http://localhost:11434")
        url_row.addWidget(self._ollama_url_input, stretch=1)
        layout.addLayout(url_row)

        model_row = QHBoxLayout()
        model_row.addWidget(QLabel(i18n.tr("lbl_ollama_model")))
        self._ollama_model_input = QLineEdit()
        self._ollama_model_input.setPlaceholderText("llama3.2")
        model_row.addWidget(self._ollama_model_input, stretch=1)
        layout.addLayout(model_row)

        ollama_hint = QLabel(i18n.tr("hint_ollama"))
        ollama_hint.setObjectName("settings_hint")
        ollama_hint.setWordWrap(True)
        layout.addWidget(ollama_hint)

        test_btn = QPushButton(i18n.tr("btn_test_ollama"))
        test_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        test_btn.clicked.connect(self._test_ollama)
        layout.addWidget(test_btn)

        layout.addStretch()

        # ── Footer ──────────────────────────────────────────────────── #
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)

        logout_btn = QPushButton(i18n.tr("btn_logout"))
        logout_btn.setObjectName("btn_logout")
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.clicked.connect(self._on_logout)
        btn_row.addWidget(logout_btn)

        btn_row.addStretch()

        cancel_btn = QPushButton(i18n.tr("btn_cancel"))
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton(i18n.tr("btn_save_close"))
        save_btn.setObjectName("btn_save")
        save_btn.setDefault(True)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)

    def _section_label(self, text: str) -> QLabel:
        lbl = QLabel(text.upper())
        lbl.setObjectName("settings_section_label")
        return lbl

    # ─────────────────────────────────────────────────────────────────── #

    def _select_theme(self, theme_id: str):
        self._selected_theme = theme_id
        btn = self._theme_buttons.get(theme_id)
        if btn:
            btn.setChecked(True)

    def _select_font(self, size_id: str):
        self._selected_font = size_id
        btn = self._font_buttons.get(size_id)
        if btn:
            btn.setChecked(True)

    def _load_settings(self):
        lang = self._db.get_setting("language", "pl") or "pl"
        self._lang_combo.setCurrentIndex(0 if lang == "pl" else 1)

        stored_theme = self._db.get_setting("theme", "system") or "system"
        theme_id = "system" if stored_theme == "system" else resolve_theme(stored_theme)
        if theme_id not in self._theme_buttons:
            theme_id = "system"
        self._select_theme(theme_id)

        font_size = self._db.get_setting("font_size", "normal") or "normal"
        if font_size not in self._font_buttons:
            font_size = "normal"
        self._select_font(font_size)

        white = self._db.get_setting("white_text", "false")
        self._white_text_check.setChecked(white == "true")

        notif = self._db.get_setting("notifications", "true")
        self._notif_check.setChecked(notif == "true")

        self._ollama_url_input.setText(self._app_settings.ollama_url())
        self._ollama_model_input.setText(self._app_settings.ollama_model())

    def _test_ollama(self):
        """Sprawdź połączenie z Ollama i dostępność modelu."""
        url   = self._ollama_url_input.text().strip() or "http://localhost:11434"
        model = self._ollama_model_input.text().strip() or "llama3.2"
        try:
            import requests
            r = requests.get(f"{url.rstrip('/')}/api/tags", timeout=5)
            r.raise_for_status()
            data = r.json()
            available = [m["name"] for m in data.get("models", [])]
            base = model.split(":")[0]
            found = any(m.split(":")[0] == base for m in available)
            if found:
                QMessageBox.information(
                    self,
                    "Ollama – połączono ✅",
                    f"Model „{model}" jest dostępny i gotowy do użycia.",
                )
            else:
                models_str = "\n".join(f"  • {m}" for m in available) if available else "  (brak pobranych modeli)"
                QMessageBox.warning(
                    self,
                    "Ollama – model niedostępny",
                    f"Połączono z Ollama, ale model „{model}" nie jest pobrany.\n\n"
                    f"Dostępne modele:\n{models_str}\n\n"
                    f"Pobierz model poleceniem:\n  ollama pull {model}",
                )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Ollama – błąd połączenia ❌",
                f"Nie można połączyć się z Ollama pod adresem:\n{url}\n\n"
                f"Błąd: {exc}\n\n"
                "Upewnij się, że Ollama jest zainstalowane i uruchomione.",
            )

    def _on_save(self):
        lang = "pl" if self._lang_combo.currentIndex() == 0 else "en"
        theme = self._selected_theme
        font_size = self._selected_font
        white = "true" if self._white_text_check.isChecked() else "false"
        notif = "true" if self._notif_check.isChecked() else "false"

        self._db.set_setting("language", lang)
        self._db.set_setting("theme", theme)
        self._db.set_setting("font_size", font_size)
        self._db.set_setting("white_text", white)
        self._db.set_setting("notifications", notif)

        self._app_settings.set_language(lang)
        self._app_settings.set_theme(theme)
        self._app_settings.set_font_size(font_size)
        self._app_settings.set_white_text(white == "true")
        self._app_settings.set_notifications_enabled(notif == "true")

        self._app_settings.set_ollama_url(
            self._ollama_url_input.text().strip() or "http://localhost:11434"
        )
        self._app_settings.set_ollama_model(
            self._ollama_model_input.text().strip() or "llama3.2"
        )

        self.accept()

    def _on_logout(self):
        reply = QMessageBox.question(
            self,
            i18n.tr("dlg_logout_title"),
            i18n.tr("dlg_logout_msg"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.logout_requested = True
            self.accept()
