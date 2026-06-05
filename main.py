import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from ui.login_window import LoginWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("YouTube Notifier")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("skrzyluk")
    app.setQuitOnLastWindowClosed(False)

    window = LoginWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
