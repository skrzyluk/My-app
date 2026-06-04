from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt


class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Notifier")
        self.setFixedSize(360, 240)
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        title = QLabel("YouTube Notifier")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.login_btn = QPushButton("Zaloguj się przez Google")
        self.login_btn.setFixedWidth(220)
        self.login_btn.clicked.connect(self._on_login)
        layout.addWidget(self.login_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def _on_login(self):
        # Phase 2: OAuth flow
        pass
