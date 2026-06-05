from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QCheckBox, QFrame, QMessageBox,
)
import i18n
from config.settings import AppSettings
from database.db import Database


class SettingsDialog(QDialog):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self._db = db
        self._app_settings = AppSettings()
        self.logout_requested = False
        self.setWindowTitle(i18n.tr("dlg_settings_title"))
        self.setFixedSize(380, 300)
        self._build_ui()
        self._load_settings()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        header = QLabel(i18n.tr("dlg_settings_title"))
        f = header.font()
        f.setPointSize(13)
        f.setBold(True)
        header.setFont(f)
        layout.addWidget(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep)

        lang_row = QHBoxLayout()
        lang_row.addWidget(QLabel(i18n.tr("lbl_language")))
        lang_row.addStretch()
        self._lang_combo = QComboBox()
        self._lang_combo.addItems([i18n.tr("lang_polish"), i18n.tr("lang_english")])
        self._lang_combo.setFixedWidth(130)
        lang_row.addWidget(self._lang_combo)
        layout.addLayout(lang_row)

        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel(i18n.tr("lbl_theme")))
        theme_row.addStretch()
        self._theme_combo = QComboBox()
        self._theme_combo.addItems([
            i18n.tr("theme_system"),
            i18n.tr("theme_light"),
            i18n.tr("theme_dark"),
        ])
        self._theme_combo.setFixedWidth(130)
        theme_row.addWidget(self._theme_combo)
        layout.addLayout(theme_row)

        notif_row = QHBoxLayout()
        notif_row.addWidget(QLabel(i18n.tr("lbl_notifications")))
        notif_row.addStretch()
        self._notif_check = QCheckBox()
        notif_row.addWidget(self._notif_check)
        layout.addLayout(notif_row)

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)

        logout_btn = QPushButton(i18n.tr("btn_logout"))
        logout_btn.clicked.connect(self._on_logout)
        btn_row.addWidget(logout_btn)

        btn_row.addStretch()

        cancel_btn = QPushButton(i18n.tr("btn_cancel"))
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton(i18n.tr("btn_save"))
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)

    def _load_settings(self):
        lang = self._db.get_setting("language", "pl") or "pl"
        self._lang_combo.setCurrentIndex(0 if lang == "pl" else 1)

        theme = self._db.get_setting("theme", "system") or "system"
        self._theme_combo.setCurrentIndex({"system": 0, "light": 1, "dark": 2}.get(theme, 0))

        notif = self._db.get_setting("notifications", "true")
        self._notif_check.setChecked(notif == "true")

    def _on_save(self):
        lang = "pl" if self._lang_combo.currentIndex() == 0 else "en"
        theme = {0: "system", 1: "light", 2: "dark"}[self._theme_combo.currentIndex()]
        notif = "true" if self._notif_check.isChecked() else "false"

        # Persist to DB
        self._db.set_setting("language", lang)
        self._db.set_setting("theme", theme)
        self._db.set_setting("notifications", notif)

        # Persist to QSettings (survives DB resets / app restarts)
        self._app_settings.set_language(lang)
        self._app_settings.set_theme(theme)
        self._app_settings.set_notifications_enabled(notif == "true")

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
