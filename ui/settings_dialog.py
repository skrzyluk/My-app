from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QCheckBox, QFrame, QMessageBox,
)
from PyQt6.QtCore import Qt

from database.db import Database


class SettingsDialog(QDialog):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self._db = db
        self.logout_requested = False
        self.setWindowTitle("Ustawienia")
        self.setFixedSize(380, 300)
        self._build_ui()
        self._load_settings()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        header = QLabel("Ustawienia")
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
        lang_row.addWidget(QLabel("Język:"))
        lang_row.addStretch()
        self._lang_combo = QComboBox()
        self._lang_combo.addItems(["Polski", "English"])
        self._lang_combo.setFixedWidth(130)
        lang_row.addWidget(self._lang_combo)
        layout.addLayout(lang_row)

        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("Motyw:"))
        theme_row.addStretch()
        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["Systemowy", "Jasny", "Ciemny"])
        self._theme_combo.setFixedWidth(130)
        theme_row.addWidget(self._theme_combo)
        layout.addLayout(theme_row)

        notif_row = QHBoxLayout()
        notif_row.addWidget(QLabel("Powiadomienia w tle:"))
        notif_row.addStretch()
        self._notif_check = QCheckBox()
        notif_row.addWidget(self._notif_check)
        layout.addLayout(notif_row)

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)

        logout_btn = QPushButton("Wyloguj się")
        logout_btn.clicked.connect(self._on_logout)
        btn_row.addWidget(logout_btn)

        btn_row.addStretch()

        cancel_btn = QPushButton("Anuluj")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("Zapisz")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)

    def _load_settings(self):
        lang = self._db.get_setting("language", "pl")
        self._lang_combo.setCurrentIndex(0 if lang == "pl" else 1)

        theme = self._db.get_setting("theme", "system")
        self._theme_combo.setCurrentIndex({"system": 0, "light": 1, "dark": 2}.get(theme, 0))

        notif = self._db.get_setting("notifications", "true")
        self._notif_check.setChecked(notif == "true")

    def _on_save(self):
        self._db.set_setting("language", "pl" if self._lang_combo.currentIndex() == 0 else "en")
        self._db.set_setting(
            "theme", {0: "system", 1: "light", 2: "dark"}[self._theme_combo.currentIndex()]
        )
        self._db.set_setting(
            "notifications", "true" if self._notif_check.isChecked() else "false"
        )
        self.accept()

    def _on_logout(self):
        reply = QMessageBox.question(
            self,
            "Wylogowanie",
            "Czy na pewno chcesz się wylogować?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.logout_requested = True
            self.accept()
