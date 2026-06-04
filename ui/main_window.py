from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from google.oauth2.credentials import Credentials


class MainWindow(QMainWindow):
    """Main application window – fully implemented in Phase 6."""

    def __init__(self, credentials: Credentials):
        super().__init__()
        self.credentials = credentials
        self.setWindowTitle("YouTube Notifier")
        self.setMinimumSize(700, 500)
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel("Zalogowano pomyślnie!\n\nGłówny ekran – Phase 6")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
