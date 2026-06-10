from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from google.oauth2.credentials import Credentials

import i18n
from services.auth_service import AuthService, AuthError, ClientSecretsNotFoundError
from utils.logger import get_logger

logger = get_logger(__name__)


class _AuthWorker(QThread):
    """Runs OAuth flow in a background thread to avoid blocking the UI."""

    success = pyqtSignal(object)   # emits Credentials
    error = pyqtSignal(str)        # emits error message

    def __init__(self, auth_service: AuthService, auto_login: bool = False):
        super().__init__()
        self._auth = auth_service
        self._auto_login = auto_login

    def run(self):
        try:
            if self._auto_login:
                creds = self._auth.get_credentials()
            else:
                creds = self._auth.authenticate()
            self.success.emit(creds)
        except ClientSecretsNotFoundError as e:
            self.error.emit(str(e))
        except AuthError as e:
            self.error.emit(str(e))
        except Exception as e:
            logger.exception("Unexpected auth error")
            self.error.emit(f"Nieoczekiwany błąd: {e}")


class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._auth = AuthService()
        self._worker: _AuthWorker | None = None
        self.setWindowTitle(i18n.tr("window_title"))
        self.setFixedSize(380, 260)
        self._build_ui()
        self._try_auto_login()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)
        layout.setContentsMargins(40, 40, 40, 40)

        logo_lbl = QLabel("▶")
        logo_lbl.setObjectName("login_logo")
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        f = logo_lbl.font()
        f.setPointSize(28)
        logo_lbl.setFont(f)
        layout.addWidget(logo_lbl)

        self._title_lbl = QLabel(i18n.tr("app_title"))
        self._title_lbl.setObjectName("login_title")
        self._title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._title_lbl)

        self.status_label = QLabel("")
        self.status_label.setObjectName("login_status")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        self.login_btn = QPushButton(i18n.tr("btn_login"))
        self.login_btn.setObjectName("login_btn")
        self.login_btn.setFixedHeight(42)
        self.login_btn.setFixedWidth(240)
        self.login_btn.clicked.connect(self._on_login)
        layout.addWidget(self.login_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def _try_auto_login(self):
        if not self._auth.is_logged_in():
            return
        self._set_busy(i18n.tr("status_logging_in"))
        self._run_worker(auto_login=True)

    def _on_login(self):
        self._set_busy(i18n.tr("status_opening_browser"))
        self._run_worker(auto_login=False)

    def _run_worker(self, auto_login: bool):
        self._worker = _AuthWorker(self._auth, auto_login=auto_login)
        self._worker.success.connect(self._on_auth_success)
        self._worker.error.connect(self._on_auth_error)
        self._worker.start()

    def _on_auth_success(self, credentials: Credentials):
        from ui.main_window import MainWindow
        self._main_window = MainWindow(credentials)
        self._main_window.show()
        self.close()

    def _on_auth_error(self, message: str):
        self._set_idle()
        QMessageBox.critical(self, i18n.tr("dlg_auth_error"), message)

    def _set_busy(self, text: str):
        self.status_label.setText(text)
        self.login_btn.setEnabled(False)

    def _set_idle(self):
        self.status_label.setText("")
        self.login_btn.setEnabled(True)
